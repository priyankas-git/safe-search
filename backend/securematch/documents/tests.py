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


class AuditorProfileManagementTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Resolve or create default groups
        self.super_admin_group, _ = Group.objects.get_or_create(name=Roles.ADMINISTRATOR)
        self.compliance_officer_group, _ = Group.objects.get_or_create(name=Roles.COMPLIANCE_OFFICER)
        self.external_auditor_group, _ = Group.objects.get_or_create(name=Roles.EXTERNAL_AUDITOR)

        # Create users
        self.super_admin = User.objects.create_user(username="super_admin_prof", password="password123")
        self.super_admin.groups.add(self.super_admin_group)

        self.compliance_officer = User.objects.create_user(username="compliance_officer_prof", password="password123")
        self.compliance_officer.groups.add(self.compliance_officer_group)

        self.external_auditor = User.objects.create_user(username="external_auditor_prof", password="password123")
        self.external_auditor.groups.add(self.external_auditor_group)

        # Create initial test auditors
        self.auditor = Auditor.objects.create(
            name="SBI Auditor",
            public_key="sbi-public-key-data",
            email="sbi@auditor.com",
            phone="+919876543210",
            designation="Senior Auditor",
            status="ACTIVE"
        )
        self.other_auditor = Auditor.objects.create(
            name="ICICI Auditor",
            public_key="icici-public-key-data",
            email="icici@auditor.com",
            phone="+919876543211",
            designation="Junior Auditor",
            status="ACTIVE"
        )

    # --------------------------------------------------
    # Retrieve Profile Tests
    # --------------------------------------------------
    def test_retrieve_profile_success_admin(self):
        url = f"/api/auditor/{self.auditor.id}/"
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        data = response.data["data"]
        self.assertEqual(data["id"], self.auditor.id)
        self.assertEqual(data["name"], "SBI Auditor")
        self.assertEqual(data["email"], "sbi@auditor.com")
        self.assertEqual(data["status"], "ACTIVE")
        self.assertEqual(data["public_key"], "sbi-public-key-data")
        self.assertEqual(data["key_version"], 1)

    def test_retrieve_profile_success_compliance_officer(self):
        url = f"/api/auditor/{self.auditor.id}/"
        self.client.force_authenticate(user=self.compliance_officer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

    def test_retrieve_profile_forbidden_external_auditor(self):
        url = f"/api/auditor/{self.auditor.id}/"
        self.client.force_authenticate(user=self.external_auditor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_profile_not_found(self):
        url = "/api/auditor/99999/"
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["status"], "error")
        self.assertEqual(response.data["error"]["code"], "AUDITOR_NOT_FOUND")

    # --------------------------------------------------
    # Update Profile Tests
    # --------------------------------------------------
    def test_update_profile_success_patch(self):
        url = f"/api/auditor/{self.auditor.id}/update/"
        self.client.force_authenticate(user=self.super_admin)
        payload = {
            "name": "SBI Updated Auditor",
            "email": "sbi.new@auditor.com",
            "phone": "+918888888888",
            "designation": "Executive Auditor"
        }
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        data = response.data["data"]
        self.assertEqual(data["name"], "SBI Updated Auditor")
        self.assertEqual(data["email"], "sbi.new@auditor.com")
        self.assertEqual(data["status"], "ACTIVE")  # Unaffected

    def test_update_profile_success_put(self):
        url = f"/api/auditor/{self.auditor.id}/update/"
        self.client.force_authenticate(user=self.super_admin)
        payload = {
            "name": "SBI Put Auditor",
            "email": "sbi.put@auditor.com",
            "phone": "+917777777777",
            "designation": "Lead Auditor"
        }
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(data["name"], "SBI Put Auditor")

    def test_update_profile_ignores_read_only_fields(self):
        url = f"/api/auditor/{self.auditor.id}/update/"
        self.client.force_authenticate(user=self.super_admin)
        payload = {
            "name": "SBI Field Auditor",
            "public_key": "hacked-public-key",
            "key_version": 99,
            "id": 9999
        }
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.auditor.refresh_from_db()
        self.assertEqual(self.auditor.name, "SBI Field Auditor")
        self.assertEqual(self.auditor.public_key, "sbi-public-key-data")
        self.assertEqual(self.auditor.key_version, 1)
        self.assertNotEqual(self.auditor.id, 9999)

    def test_update_profile_validation_errors(self):
        url = f"/api/auditor/{self.auditor.id}/update/"
        self.client.force_authenticate(user=self.super_admin)

        # 1. Empty name
        response = self.client.patch(url, {"name": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("name", response.data["error"]["details"])

        # 2. Min length name
        response = self.client.patch(url, {"name": "ab"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data["error"]["details"])

        # 3. Invalid email format
        response = self.client.patch(url, {"email": "invalid-email"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data["error"]["details"])

        # 4. Duplicate email
        response = self.client.patch(url, {"email": "icici@auditor.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data["error"]["details"])

        # 5. Duplicate name
        response = self.client.patch(url, {"name": "ICICI Auditor"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data["error"]["details"])

        # 6. Invalid phone format
        response = self.client.patch(url, {"phone": "12345"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", response.data["error"]["details"])

    # --------------------------------------------------
    # Status Management Tests
    # --------------------------------------------------
    def test_update_status_success(self):
        url = f"/api/auditor/{self.auditor.id}/status/"
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.patch(url, {"status": "DISABLED"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["status"], "DISABLED")
        self.auditor.refresh_from_db()
        self.assertEqual(self.auditor.status, "DISABLED")

        # Set back to ACTIVE
        response = self.client.patch(url, {"status": "ACTIVE"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], "ACTIVE")

    def test_update_status_invalid_value(self):
        url = f"/api/auditor/{self.auditor.id}/status/"
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.patch(url, {"status": "PENDING"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("status", response.data["error"]["details"])

    def test_update_status_forbidden_compliance_officer(self):
        url = f"/api/auditor/{self.auditor.id}/status/"
        self.client.force_authenticate(user=self.compliance_officer)
        response = self.client.patch(url, {"status": "DISABLED"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


