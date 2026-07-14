import string
import random
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

from accounts.constants import Roles
from documents.models import Auditor
from documents.services.key_service import generate_keys

User = get_user_model()
logger = logging.getLogger(__name__)

def generate_random_password(length=14):
    """
    Generates a secure random temporary password.
    """
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choices(chars, k=length))

def generate_username(name):
    """
    Generates a clean username from the auditor name.
    """
    clean = "".join(c for c in name.lower() if c.isalnum() or c in "_-")
    base = f"auditor_{clean}"
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}_{counter}"
        counter += 1
    return username

def assign_external_auditor_role(user):
    """
    Assigns the 'External Auditor' role to a Django User.
    """
    group, _ = Group.objects.get_or_create(name=Roles.EXTERNAL_AUDITOR)
    user.groups.add(group)
    logger.info(f"Assigned 'External Auditor' group to user {user.username}")

def provision_auditor_profile(name, public_key, email=None, phone=None, designation=None, status="ACTIVE"):
    """
    Provisions a new Auditor profile.
    """
    auditor = Auditor.objects.create(
        name=name,
        email=email,
        phone=phone,
        designation=designation,
        status=status,
        public_key=public_key,
        key_version=1
    )
    logger.info(f"Provisioned Auditor profile for {name} (ID: {auditor.id})")
    return auditor

def create_auditor_with_identity(name, email=None, phone=None, designation=None, status="ACTIVE"):
    """
    Creates an Auditor, generates their key pair, provisions their profile,
    creates their Django User account, and assigns the External Auditor role.
    Runs inside a transaction.
    """
    with transaction.atomic():
        # Generate temporary credentials
        temp_pass = generate_random_password()
        username = generate_username(name)

        # Create Django User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=temp_pass,
            is_active=(status == "ACTIVE")
        )

        # Assign role
        assign_external_auditor_role(user)

        # Generate RSA keys
        private_key, public_key = generate_keys()

        # Provision profile
        auditor = provision_auditor_profile(
            name=name,
            public_key=public_key,
            email=email,
            phone=phone,
            designation=designation,
            status=status
        )

        return {
            "auditor": auditor,
            "user": user,
            "private_key": private_key,
            "temporary_password": temp_pass,
            "username": username
        }

def update_auditor_status(auditor, new_status):
    """
    Updates the auditor's status and deactivates/reactivates the corresponding user.
    """
    if new_status not in [choice[0] for choice in Auditor.STATUS_CHOICES]:
        raise ValueError(f"Invalid status choice: {new_status}")

    with transaction.atomic():
        auditor.status = new_status
        auditor.save(update_fields=["status", "updated_at"])

        is_active = (new_status == "ACTIVE")

        # Find and update corresponding Django User
        updated_count = 0
        if auditor.email:
            updated_count = User.objects.filter(email=auditor.email).update(is_active=is_active)
        
        if updated_count == 0:
            # Fallback to username search if email didn't match or was empty
            clean_name = "".join(c for c in auditor.name.lower() if c.isalnum() or c in "_-")
            User.objects.filter(username__startswith=f"auditor_{clean_name}").update(is_active=is_active)

        logger.info(f"Updated auditor {auditor.id} status to {new_status} (is_active={is_active})")
        return auditor
