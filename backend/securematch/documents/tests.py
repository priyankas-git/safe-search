from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from documents.models import Auditor
from accounts.constants import Roles

User = get_user_model()

class RBACTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Resolve or create default groups (created by signals automatically, but get_or_create to be safe)
        self.super_admin_group, _ = Group.objects.get_or_create(name=Roles.ADMINISTRATOR)
        self.internal_analyst_group, _ = Group.objects.get_or_create(name=Roles.INTERNAL_ANALYST)
        self.compliance_officer_group, _ = Group.objects.get_or_create(name=Roles.COMPLIANCE_OFFICER)
        self.external_auditor_group, _ = Group.objects.get_or_create(name=Roles.EXTERNAL_AUDITOR)
        self.read_only_analyst_group, _ = Group.objects.get_or_create(name=Roles.READ_ONLY_ANALYST)

        # Create users for each role
        self.super_admin = User.objects.create_user(username="super_admin", password="password123")
        self.super_admin.groups.add(self.super_admin_group)

        self.internal_analyst = User.objects.create_user(username="internal_analyst", password="password123")
        self.internal_analyst.groups.add(self.internal_analyst_group)

        self.compliance_officer = User.objects.create_user(username="compliance_officer", password="password123")
        self.compliance_officer.groups.add(self.compliance_officer_group)

        self.external_auditor = User.objects.create_user(username="external_auditor", password="password123")
        self.external_auditor.groups.add(self.external_auditor_group)

        self.read_only_analyst = User.objects.create_user(username="read_only_analyst", password="password123")
        self.read_only_analyst.groups.add(self.read_only_analyst_group)

        # Create a test auditor for auditor-specific endpoints
        self.test_auditor = Auditor.objects.create(
            name="HDFC",
            public_key="test-public-key",
            key_version=1
        )

    def assert_allowed(self, user, method, url, data=None):
        self.client.force_authenticate(user=user)
        func = getattr(self.client, method)
        response = func(url, data=data)
        # If authorized, it should not return 403 Forbidden with PERMISSION_DENIED.
        # It could return 400 Bad Request or 404 Not Found (due to empty inputs or missing details),
        # but not a role permission restriction (403 with PERMISSION_DENIED).
        is_permission_denied = (
            response.status_code == status.HTTP_403_FORBIDDEN and 
            isinstance(response.data, dict) and 
            response.data.get("error", {}).get("code") == "PERMISSION_DENIED"
        )
        self.assertFalse(
            is_permission_denied,
            f"User {user.username} with role {user.groups.first().name} was forbidden on {method.upper()} {url} (expected allowed)"
        )

    def assert_forbidden(self, user, method, url, data=None):
        self.client.force_authenticate(user=user)
        func = getattr(self.client, method)
        response = func(url, data=data)
        self.assertEqual(
            response.status_code, 
            status.HTTP_403_FORBIDDEN, 
            f"User {user.username} with role {user.groups.first().name} was allowed on {method.upper()} {url} (expected forbidden)"
        )
        self.assertEqual(response.data["status"], "error")
        self.assertEqual(response.data["error"]["code"], "PERMISSION_DENIED")

    # 1. Upload Documents
    def test_upload_documents_permissions(self):
        url = "/api/upload/"
        self.assert_allowed(self.super_admin, "post", url)
        self.assert_allowed(self.internal_analyst, "post", url)
        
        self.assert_forbidden(self.compliance_officer, "post", url)
        self.assert_forbidden(self.external_auditor, "post", url)
        self.assert_forbidden(self.read_only_analyst, "post", url)

    # 2. Internal Search
    def test_internal_search_permissions(self):
        url = "/api/search/internal/"
        self.assert_allowed(self.super_admin, "post", url)
        self.assert_allowed(self.internal_analyst, "post", url)
        self.assert_allowed(self.compliance_officer, "post", url)
        self.assert_allowed(self.read_only_analyst, "post", url)
        
        self.assert_forbidden(self.external_auditor, "post", url)

    # 3. External Search
    def test_external_search_permissions(self):
        url = "/api/search/external/"
        self.assert_allowed(self.super_admin, "post", url)
        self.assert_allowed(self.external_auditor, "post", url)
        
        self.assert_forbidden(self.internal_analyst, "post", url)
        self.assert_forbidden(self.compliance_officer, "post", url)
        self.assert_forbidden(self.read_only_analyst, "post", url)

    # 4. Verify Auditor Credentials
    def test_verify_auditor_credentials_permissions(self):
        url = "/api/auditor/verify/"
        self.assert_allowed(self.super_admin, "post", url)
        self.assert_allowed(self.external_auditor, "post", url)
        
        self.assert_forbidden(self.internal_analyst, "post", url)
        self.assert_forbidden(self.compliance_officer, "post", url)
        self.assert_forbidden(self.read_only_analyst, "post", url)

    # 5. Rotate Auditor Keys
    def test_rotate_auditor_keys_permissions(self):
        url = "/api/auditor/rotate-key/"
        self.assert_allowed(self.super_admin, "post", url)
        
        self.assert_forbidden(self.internal_analyst, "post", url)
        self.assert_forbidden(self.compliance_officer, "post", url)
        self.assert_forbidden(self.external_auditor, "post", url)
        self.assert_forbidden(self.read_only_analyst, "post", url)

    # 6. Create Auditor
    def test_create_auditor_permissions(self):
        url = "/api/auditor/create/"
        self.assert_allowed(self.super_admin, "post", url)
        
        self.assert_forbidden(self.internal_analyst, "post", url)
        self.assert_forbidden(self.compliance_officer, "post", url)
        self.assert_forbidden(self.external_auditor, "post", url)
        self.assert_forbidden(self.read_only_analyst, "post", url)

    # 7. Delete Auditor
    def test_delete_auditor_permissions(self):
        url = f"/api/auditor/{self.test_auditor.id}/delete/"
        self.assert_allowed(self.super_admin, "delete", url)
        
        # Re-create auditor for subsequent tests
        self.test_auditor = Auditor.objects.create(
            name="HDFC",
            public_key="test-public-key",
            key_version=1
        )
        url = f"/api/auditor/{self.test_auditor.id}/delete/"
        self.assert_forbidden(self.internal_analyst, "delete", url)
        self.assert_forbidden(self.compliance_officer, "delete", url)
        self.assert_forbidden(self.external_auditor, "delete", url)
        self.assert_forbidden(self.read_only_analyst, "delete", url)

    # 8. View Auditor Logs
    def test_view_auditor_logs_permissions(self):
        url = f"/api/auditor/{self.test_auditor.id}/logs/"
        self.assert_allowed(self.super_admin, "get", url)
        self.assert_allowed(self.compliance_officer, "get", url)
        
        self.assert_forbidden(self.internal_analyst, "get", url)
        self.assert_forbidden(self.external_auditor, "get", url)
        self.assert_forbidden(self.read_only_analyst, "get", url)

    # 9. Internal Metrics
    def test_internal_metrics_permissions(self):
        url = "/api/metrics/internal/"
        self.assert_allowed(self.super_admin, "get", url)
        self.assert_allowed(self.compliance_officer, "get", url)
        
        self.assert_forbidden(self.internal_analyst, "get", url)
        self.assert_forbidden(self.external_auditor, "get", url)
        self.assert_forbidden(self.read_only_analyst, "get", url)

    # 10. External Metrics
    def test_external_metrics_permissions(self):
        url = "/api/metrics/external/"
        self.assert_allowed(self.super_admin, "get", url)
        self.assert_allowed(self.internal_analyst, "get", url)
        self.assert_allowed(self.compliance_officer, "get", url)
        self.assert_allowed(self.external_auditor, "get", url)
        self.assert_allowed(self.read_only_analyst, "get", url)

    # 11. Health Check
    def test_health_check(self):
        url = "/api/health/"
        self.client.force_authenticate(user=None)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["status"], "healthy")
        self.assertEqual(response.data["data"]["database"], "up")

    # 12. Download Auditor Credentials
    def test_download_auditor_credentials_permissions(self):
        url = f"/api/auditor/{self.test_auditor.id}/download/"
        self.assert_allowed(self.super_admin, "get", url)
        self.assert_allowed(self.super_admin, "post", url, data={"private_key": "test-priv"})
        self.assert_allowed(self.external_auditor, "get", url)
        self.assert_allowed(self.external_auditor, "post", url, data={"private_key": "test-priv"})
        
        self.assert_forbidden(self.internal_analyst, "get", url)
        self.assert_forbidden(self.compliance_officer, "get", url)
        self.assert_forbidden(self.read_only_analyst, "get", url)
        
        self.assert_forbidden(self.internal_analyst, "post", url, data={"private_key": "test-priv"})
        self.assert_forbidden(self.compliance_officer, "post", url, data={"private_key": "test-priv"})
        self.assert_forbidden(self.read_only_analyst, "post", url, data={"private_key": "test-priv"})


class CredentialTests(TestCase):
    def test_fingerprint_generation(self):
        from crypto_engine.peks import generate_rsa_keypair, get_public_key_fingerprint
        _, public_key = generate_rsa_keypair()
        fingerprint = get_public_key_fingerprint(public_key)
        self.assertEqual(len(fingerprint), 64)  # SHA-256 is 64 hex characters
        
        # Verify fallback works for invalid key format
        invalid_key = "invalid-public-key"
        fp_fallback = get_public_key_fingerprint(invalid_key)
        import hashlib
        self.assertEqual(fp_fallback, hashlib.sha256(invalid_key.encode()).hexdigest())

    def test_pdf_generation_and_download_flow(self):
        from documents.models import Auditor
        from documents.pdf_generator import generate_credential_pdf
        from rest_framework.test import APIClient
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        
        # Setup auditor
        auditor = Auditor.objects.create(
            name="Test Auditor PDF",
            public_key="test-public-key",
            key_version=2
        )
        
        # Test PDF generator function directly
        pdf_no_priv = generate_credential_pdf(auditor)
        self.assertIsInstance(pdf_no_priv, bytes)
        self.assertTrue(len(pdf_no_priv) > 100)
        
        pdf_with_priv = generate_credential_pdf(auditor, private_key="test-private-key")
        self.assertIsInstance(pdf_with_priv, bytes)
        self.assertTrue(len(pdf_with_priv) > 100)
        
        # Test download endpoint responses
        client = APIClient()
        super_admin_group, _ = Group.objects.get_or_create(name=Roles.ADMINISTRATOR)
        super_admin = get_user_model().objects.create_user(username="test_admin_dl", password="password123")
        super_admin.groups.add(super_admin_group)
        client.force_authenticate(user=super_admin)
        
        # GET request
        url = f"/api/auditor/{auditor.id}/download/"
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.has_header('Content-Disposition'))
        
        # POST request
        response_post = client.post(url, {"private_key": "my-private-key-test"})
        self.assertEqual(response_post.status_code, status.HTTP_200_OK)
        self.assertEqual(response_post['Content-Type'], 'application/pdf')
        
        # Test 404 for non-existent auditor
        response_404 = client.get("/api/auditor/99999/download/")
        self.assertEqual(response_404.status_code, status.HTTP_404_NOT_FOUND)


