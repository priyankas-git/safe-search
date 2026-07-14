import time
import hashlib
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle
from crypto_engine.peks import generate_rsa_keypair
from rest_framework.permissions import IsAuthenticated, AllowAny
from accounts.permissions import (
    IsSuperAdministrator,
    IsInternalAnalyst,
    IsComplianceOfficer,
    IsExternalAuditor,
    IsReadOnlyAnalyst,
    IsInternalUser,
    IsAdministrator
)


from crypto_engine.peks import hash_keyword, verify_signature
from crypto_engine.sse import (
    encrypt_document,
    generate_token,
    generate_trapdoor,
    decrypt_document
)

from documents.models import (
    Auditor,
    EncryptedDocument,
    SearchTokenIndex,
    ExternalSearchAudit
)

from .constants import SEARCHABLE_FIELDS
from .utils import success_response, error_response
from .serializers import (
    AuditorRetrieveSerializer,
    AuditorUpdateSerializer,
    AuditorStatusSerializer
)


MAX_EXTERNAL_RESULTS = 50
MAX_INTERNAL_RESULTS = 50


# ---------------------------------------------------
#  Upload & Index
# ---------------------------------------------------

class UploadDocumentView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdministrator | IsInternalAnalyst]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "upload"

    def post(self, request):
        try:
            data = request.data

            if not isinstance(data, dict):
                return Response(
                    error_response("INVALID_JSON", "Invalid JSON object"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            encrypted_blob = encrypt_document(data)

            doc = EncryptedDocument.objects.create(
                encrypted_blob=encrypted_blob
            )

            for field in SEARCHABLE_FIELDS:
                if field in data and data[field] is not None:

                    value = str(data[field]).strip()
                    if not value:
                        continue

                    token = generate_token(field, value)
                    external_token = hash_keyword(value)

                    SearchTokenIndex.objects.create(
                        token=token,
                        external_token=external_token,
                        document=doc
                    )

            return Response(
                success_response(
                    data={"message": "Document encrypted and indexed"}
                ),
                status=status.HTTP_201_CREATED
            )

        except Exception:
            return Response(
                error_response("UPLOAD_FAILED", "Upload failed"),
                status=status.HTTP_400_BAD_REQUEST
            )


# ---------------------------------------------------
#  Internal Secure Search (SSE)
# ---------------------------------------------------

class InternalSearchView(APIView):
    permission_classes = [IsAuthenticated, IsInternalUser | IsReadOnlyAnalyst]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "search"

    def post(self, request):
        try:
            query_data = request.data

            if not isinstance(query_data, dict) or not query_data:
                return Response(
                    error_response("INVALID_QUERY", "Invalid search query"),
                    status=status.HTTP_400_BAD_REQUEST
                )

            start_time = time.perf_counter()
            matching_doc_ids = None

            for field, value in query_data.items():
                trapdoor = generate_trapdoor(field, str(value))

                token_matches = SearchTokenIndex.objects.filter(
                    token=trapdoor
                ).values_list("document_id", flat=True)

                token_doc_ids = set(token_matches)

                if matching_doc_ids is None:
                    matching_doc_ids = token_doc_ids
                else:
                    matching_doc_ids = matching_doc_ids.intersection(token_doc_ids)

            if not matching_doc_ids:
                execution_time = round((time.perf_counter() - start_time) * 1000, 2)

                return Response(
                    success_response(
                        data={"results": []},
                        meta={
                            "total_matches": 0,
                            "returned_count": 0,
                            "truncated": False,
                            "execution_time_ms": execution_time
                        }
                    ),
                    status=status.HTTP_200_OK
                )

            total_matches = len(matching_doc_ids)
            truncated = total_matches > MAX_INTERNAL_RESULTS

            limited_ids = list(matching_doc_ids)[:MAX_INTERNAL_RESULTS]

            encrypted_docs = EncryptedDocument.objects.filter(
                id__in=limited_ids
            )

            results = [
                decrypt_document(doc.encrypted_blob)
                for doc in encrypted_docs
            ]

            execution_time = round((time.perf_counter() - start_time) * 1000, 2)

            return Response(
                success_response(
                    data={"results": results},
                    meta={
                        "total_matches": total_matches,
                        "returned_count": len(results),
                        "truncated": truncated,
                        "execution_time_ms": execution_time
                    }
                ),
                status=status.HTTP_200_OK
            )

        except Exception:
            return Response(
                error_response("INTERNAL_SEARCH_FAILED", "Search failed"),
                status=status.HTTP_400_BAD_REQUEST
            )


# ---------------------------------------------------
#  External Public-Key Search (Hardened)
# ---------------------------------------------------

class ExternalSearchView(APIView):
    permission_classes = [IsAuthenticated, IsExternalAuditor | IsSuperAdministrator]

    def post(self, request):
        total_start = time.perf_counter()

        auditor_id = request.data.get("auditor_id")
        request_key_version = request.data.get("key_version")
        keyword_hash = request.data.get("keyword_hash")
        signature = request.data.get("signature")

        if not auditor_id or not keyword_hash or not signature:
            return Response(
                error_response("MISSING_FIELDS", "Required fields missing"),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            auditor = Auditor.objects.get(id=auditor_id)
        except Auditor.DoesNotExist:
            return Response(
                error_response("AUDITOR_NOT_FOUND", "Auditor not found"),
                status=status.HTTP_404_NOT_FOUND
            )

        current_key_version = getattr(auditor, "key_version", 1)
        if request_key_version is not None and str(request_key_version) != str(current_key_version):
            ExternalSearchAudit.objects.create(
                auditor=auditor,
                keyword_hash=keyword_hash,
                total_matches=0,
                returned_count=0,
                truncated=False,
                execution_time_ms=round(
                    (time.perf_counter() - total_start) * 1000, 2
                ),
                success=False,
                failure_reason="KEY_VERSION_MISMATCH",
                key_version=current_key_version
            )

            return Response(
                error_response("KEY_VERSION_MISMATCH", "Auditor key version mismatch"),
                status=status.HTTP_403_FORBIDDEN
            )

        # Signature Verification
        verify_start = time.perf_counter()
        is_valid = verify_signature(
            keyword_hash,
            signature,
            auditor.public_key
        )
        verify_time = (time.perf_counter() - verify_start) * 1000

        if not is_valid:
            ExternalSearchAudit.objects.create(
                auditor=auditor,
                keyword_hash=keyword_hash,
                total_matches=0,
                returned_count=0,
                truncated=False,
                execution_time_ms=round(
                    (time.perf_counter() - total_start) * 1000, 2
                ),
                success=False,
                failure_reason="INVALID_SIGNATURE",
                key_version=getattr(auditor, "key_version", 1)
            )

            return Response(
                error_response("INVALID_SIGNATURE", "Signature verification failed"),
                status=status.HTTP_403_FORBIDDEN
            )

        # Fetch Matches
        matches = SearchTokenIndex.objects.filter(
            external_token=keyword_hash
        ).select_related("document")

        total_matches = matches.count()
        limited_matches = matches[:MAX_EXTERNAL_RESULTS]

        encrypted_results = [
            {
                "nonce": m.document.encrypted_blob["nonce"],
                "ciphertext": m.document.encrypted_blob["ciphertext"]
            }
            for m in limited_matches
        ]

        # RESULT PADDING (Fixed Size)
        if len(encrypted_results) < MAX_EXTERNAL_RESULTS:
            padding_needed = MAX_EXTERNAL_RESULTS - len(encrypted_results)

            for _ in range(padding_needed):
                encrypted_results.append({
                    "nonce": "0" * 24,
                    "ciphertext": "0" * 64,
                    "padded": True
                })

        total_time = (time.perf_counter() - total_start) * 1000

        # Frequency Monitoring
        one_hour_ago = timezone.now() - timedelta(hours=1)

        recent_search_count = ExternalSearchAudit.objects.filter(
            auditor=auditor,
            created_at__gte=one_hour_ago
        ).count()

        # Audit Log
        audit_entry = ExternalSearchAudit.objects.create(
            auditor=auditor,
            keyword_hash=keyword_hash,
            total_matches=total_matches,
            returned_count=min(total_matches, MAX_EXTERNAL_RESULTS),
            truncated=total_matches > MAX_EXTERNAL_RESULTS,
            execution_time_ms=round(total_time, 2),
            success=True,
            key_version=getattr(auditor, "key_version", 1)
        )

        return Response(
            success_response(
                data={
                    "results": encrypted_results
                },
                meta={
                    "total_matches": total_matches,
                    "returned_count": min(total_matches, MAX_EXTERNAL_RESULTS),
                    "truncated": total_matches > MAX_EXTERNAL_RESULTS,
                    "execution_time_ms": round(total_time, 2),
                    "signature_verification_ms": round(verify_time, 2),
                    "audit_log_id": audit_entry.id,
                    "searches_last_hour": recent_search_count,
                    "key_version_used": getattr(auditor, "key_version", 1),
                    "response_padded": total_matches < MAX_EXTERNAL_RESULTS
                }
            ),
            status=status.HTTP_200_OK
        )

class RotateAuditorKeyView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdministrator]

    def post(self, request):
        auditor_id = request.data.get("auditor_id")
        new_public_key = request.data.get("new_public_key")

        if not auditor_id or not new_public_key:
            return Response(
                error_response("MISSING_FIELDS", "auditor_id and new_public_key required"),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            auditor = Auditor.objects.get(id=auditor_id)
        except Auditor.DoesNotExist:
            return Response(
                error_response("AUDITOR_NOT_FOUND", "Auditor not found"),
                status=status.HTTP_404_NOT_FOUND
            )

        # Simulated key version increment
        current_version = getattr(auditor, "key_version", 1)
        auditor.public_key = new_public_key
        auditor.key_version = current_version + 1
        auditor.save()

        return Response(
            success_response(
                data={
                    "auditor_id": auditor.id,
                    "new_key_version": auditor.key_version
                }
            ),
            status=status.HTTP_200_OK
        )


class VerifyAuditorCredentialsView(APIView):
    permission_classes = [IsAuthenticated, IsExternalAuditor | IsSuperAdministrator]

    def post(self, request):
        auditor_id = request.data.get("auditor_id")
        signature = request.data.get("signature")

        if not auditor_id or not signature:
            return Response(
                error_response("MISSING_FIELDS", "auditor_id and signature required"),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            auditor = Auditor.objects.get(id=auditor_id)
        except Auditor.DoesNotExist:
            return Response(
                error_response("AUDITOR_NOT_FOUND", "Auditor not found"),
                status=status.HTTP_404_NOT_FOUND
            )

        probe = f"auditor-probe:{auditor.id}"
        probe_hash = hashlib.sha256(probe.encode()).hexdigest()
        is_valid = verify_signature(probe_hash, signature, auditor.public_key)

        if not is_valid:
            return Response(
                error_response("INVALID_SIGNATURE", "Private key does not match selected auditor"),
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            success_response(
                data={
                    "auditor_id": auditor.id,
                    "name": auditor.name,
                    "active_key_version": auditor.key_version,
                    "created_at": auditor.created_at.isoformat()
                }
            ),
            status=status.HTTP_200_OK
        )

class AuditorLogsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdministrator | IsComplianceOfficer]

    def get(self, request, auditor_id):

        try:
            auditor = Auditor.objects.get(id=auditor_id)
        except Auditor.DoesNotExist:
            return Response(
                error_response("AUDITOR_NOT_FOUND", "Auditor not found"),
                status=status.HTTP_404_NOT_FOUND
            )

        logs = ExternalSearchAudit.objects.filter(
            auditor=auditor
        )[:100]

        data = [
            {
                "id": log.id,
                "keyword_hash": log.keyword_hash,
                "success": log.success,
                "total_matches": log.total_matches,
                "returned_count": log.returned_count,
                "execution_time_ms": log.execution_time_ms,
                "created_at": log.created_at,
                "key_version": getattr(log, "key_version", 1)
            }
            for log in logs
        ]

        return Response(
            success_response(
                data={"logs": data}
            ),
            status=status.HTTP_200_OK
        )
    
class InternalMetricsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdministrator | IsComplianceOfficer]

    def get(self, request):
        try:
            now = timezone.now()
            last_24h = now - timedelta(hours=24)

            total_documents = EncryptedDocument.objects.count()
            total_tokens = SearchTokenIndex.objects.count()

            external_tokens = SearchTokenIndex.objects.exclude(
                external_token__isnull=True
            ).count()

            avg_external = ExternalSearchAudit.objects.filter(
                success=True
            ).aggregate(avg=Avg("execution_time_ms"))["avg"] or 0

            external_24h = ExternalSearchAudit.objects.filter(
                created_at__gte=last_24h
            ).count()

            failed_24h = ExternalSearchAudit.objects.filter(
                created_at__gte=last_24h,
                success=False
            ).count()

            last_doc = EncryptedDocument.objects.order_by("-created_at").first()
            last_index_update = (
                last_doc.created_at.isoformat()
                if last_doc else None
            )

            # 🔑 Multi-Auditor Key Info
            auditors = Auditor.objects.all().order_by("id")

            auditor_data = [
                {
                    "auditor_id": a.id,
                    "name": a.name,
                    "public_key": a.public_key,
                    "active_key_version": a.key_version,
                    "created_at": a.created_at.isoformat()
                }
                for a in auditors
            ]

            return Response({
                "data": {
                    "system_metrics": {
                        "total_documents": total_documents,
                        "total_tokens": total_tokens,
                        "external_tokens": external_tokens,
                        "avg_external_search_ms": round(avg_external, 2),
                        "external_searches_last_24h": external_24h,
                        "failed_external_searches_last_24h": failed_24h,
                        "last_index_update": last_index_update
                    },
                    "auditors": auditor_data
                }
            })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )      

    def head(self, request):
        """Respond to HEAD checks (UptimeRobot friendly).

        Returns 200 with no body so external uptime monitors can verify service availability.
        """
        return Response(status=status.HTTP_200_OK)

class ExternalMetricsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            total_documents = EncryptedDocument.objects.count()

            return Response({
                "data": {
                    "total_documents": total_documents
                }
            })

        except Exception:
            return Response(
                {"error": "Failed to fetch metrics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RotateAuditorKeyView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdministrator]

    def post(self, request):
        auditor_id = request.data.get("auditor_id")

        if not auditor_id:
            return Response(
                error_response("MISSING_AUDITOR_ID", "Auditor ID required"),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            auditor = Auditor.objects.get(id=auditor_id)
        except Auditor.DoesNotExist:
            return Response(
                error_response("AUDITOR_NOT_FOUND", "Auditor not found"),
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate new keypair
        private_key, public_key = generate_rsa_keypair()

        # Rotate
        auditor.public_key = public_key
        auditor.key_version += 1
        auditor.save()

        return Response(
            success_response(
                data={
                    "new_private_key": private_key,
                    "new_public_key": public_key,
                    "new_key_version": auditor.key_version
                }
            ),
            status=status.HTTP_200_OK
        )
    
class CreateAuditorView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdministrator]

    def post(self, request):
        name = request.data.get("name")

        if not name:
            return Response(
                error_response("MISSING_NAME", "Auditor name required"),
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate keypair
        private_key, public_key = generate_rsa_keypair()

        auditor = Auditor.objects.create(
            name=name,
            public_key=public_key,
            key_version=1
        )

        return Response(
            success_response(
                data={
                    "auditor_id": auditor.id,
                    "name": auditor.name,
                    "public_key": public_key,
                    "private_key": private_key,  # Return only once
                    "key_version": auditor.key_version
                }
            ),
            status=status.HTTP_201_CREATED
        )

class DeleteAuditorView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdministrator]

    def delete(self, request, auditor_id):
        try:
            auditor = Auditor.objects.get(id=auditor_id)
        except Auditor.DoesNotExist:
            return Response(
                error_response("AUDITOR_NOT_FOUND", "Auditor not found"),
                status=status.HTTP_404_NOT_FOUND
            )

        auditor.delete()

        return Response(
            success_response(
                data={"message": "Auditor deleted successfully"}
            ),
            status=status.HTTP_200_OK
        )


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_status = "up"
            db_healthy = True
        except Exception as e:
            db_status = "down"
            db_healthy = False
            error_details = str(e)

        if db_healthy:
            return Response(
                success_response(
                    data={
                        "status": "healthy",
                        "database": db_status
                    }
                ),
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                error_response(
                    code="DATABASE_UNAVAILABLE",
                    message="Database connection failed",
                    details={"error": error_details}
                ),
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class AuditorProfileRetrieveView(APIView):
    """
    GET /api/auditor/<id>/

    Success: 200
    {
        "status": "success",
        "data": {
            "id": 1,
            "name": "SBI Auditor",
            "email": "sbi@auditor.com",
            "phone": "+919876543210",
            "designation": "Senior Auditor",
            "public_key": "...",
            "key_version": 1,
            "status": "ACTIVE",
            "created_at": "2026-07-14T08:00:00Z",
            "updated_at": "2026-07-14T08:00:00Z"
        },
        "meta": {}
    }

    Errors: 404 AUDITOR_NOT_FOUND, 500 AUDITOR_PROFILE_RETRIEVE_FAILED
    """
    permission_classes = [IsAuthenticated, IsSuperAdministrator | IsComplianceOfficer]

    def get(self, request, id):
        try:
            auditor = Auditor.objects.get(id=id)
        except Auditor.DoesNotExist:
            return Response(
                error_response(
                    code="AUDITOR_NOT_FOUND",
                    message="Auditor not found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception:
            return Response(
                error_response(
                    code="AUDITOR_PROFILE_RETRIEVE_FAILED",
                    message="Failed to retrieve auditor profile"
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        serializer = AuditorRetrieveSerializer(auditor)
        return Response(
            success_response(data=serializer.data),
            status=status.HTTP_200_OK
        )


class AuditorProfileUpdateView(APIView):
    """
    PUT/PATCH /api/auditor/<id>/update/

    Request body:
    {
        "name": "SBI Auditor",
        "email": "sbi@auditor.com",
        "phone": "+919876543210",
        "designation": "Senior Auditor"
    }

    Editable fields: name, email, phone, designation.
    Ignored read-only fields: id, public_key, key_version, created_at, updated_at, status.

    Success: 200 with AuditorRetrieveSerializer response.
    Errors: 400 VALIDATION_ERROR, 404 AUDITOR_NOT_FOUND, 500 AUDITOR_PROFILE_UPDATE_FAILED
    """
    permission_classes = [IsAuthenticated, IsSuperAdministrator]

    def patch(self, request, id):
        return self._update(request, id, partial=True)

    def put(self, request, id):
        return self._update(request, id, partial=False)

    def _update(self, request, id, partial):
        try:
            auditor = Auditor.objects.get(id=id)
        except Auditor.DoesNotExist:
            return Response(
                error_response(
                    code="AUDITOR_NOT_FOUND",
                    message="Auditor not found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AuditorUpdateSerializer(
            auditor,
            data=request.data,
            partial=partial
        )
        if not serializer.is_valid():
            return Response(
                error_response(
                    code="VALIDATION_ERROR",
                    message="Invalid request data.",
                    details=serializer.errors
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            auditor = serializer.save()
        except Exception:
            return Response(
                error_response(
                    code="AUDITOR_PROFILE_UPDATE_FAILED",
                    message="Failed to update auditor profile"
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        profile_serializer = AuditorRetrieveSerializer(auditor)
        return Response(
            success_response(data=profile_serializer.data),
            status=status.HTTP_200_OK
        )


class AuditorStatusUpdateView(APIView):
    """
    PATCH /api/auditor/<id>/status/

    Request body:
    {
        "status": "DISABLED"
    }

    Supported status values: ACTIVE, DISABLED.

    Success: 200
    {
        "status": "success",
        "data": {
            "auditor_id": 1,
            "status": "DISABLED"
        },
        "meta": {}
    }

    Errors: 400 VALIDATION_ERROR, 404 AUDITOR_NOT_FOUND, 500 AUDITOR_STATUS_UPDATE_FAILED
    """
    permission_classes = [IsAuthenticated, IsSuperAdministrator]

    def patch(self, request, id):
        try:
            auditor = Auditor.objects.get(id=id)
        except Auditor.DoesNotExist:
            return Response(
                error_response(
                    code="AUDITOR_NOT_FOUND",
                    message="Auditor not found"
                ),
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AuditorStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                error_response(
                    code="VALIDATION_ERROR",
                    message="Invalid request data.",
                    details=serializer.errors
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            auditor.status = serializer.validated_data["status"]
            auditor.save(update_fields=["status", "updated_at"])
        except Exception:
            return Response(
                error_response(
                    code="AUDITOR_STATUS_UPDATE_FAILED",
                    message="Failed to update auditor status"
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            success_response(
                data={
                    "auditor_id": auditor.id,
                    "status": auditor.status
                }
            ),
            status=status.HTTP_200_OK
        )

