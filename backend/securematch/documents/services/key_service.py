import logging
from crypto_engine.peks import generate_rsa_keypair, get_public_key_fingerprint

logger = logging.getLogger(__name__)

def generate_keys():
    """
    Generates a new RSA 2048-bit keypair.
    Returns (private_key_pem, public_key_pem).
    """
    return generate_rsa_keypair()

def get_fingerprint(public_key_pem):
    """
    Generates SHA-256 fingerprint for public key.
    """
    return get_public_key_fingerprint(public_key_pem)

def rotate_auditor_keys(auditor):
    """
    Rotates keys for the given auditor:
    - Generates new RSA keypair
    - Increments key version
    - Replaces public key
    - Archives previous key via logging/audit trail
    Returns (new_private_key, new_public_key, new_version)
    """
    old_public_key = auditor.public_key
    old_version = auditor.key_version

    # Generate new keypair
    private_key, public_key = generate_keys()

    # Rotate attributes
    auditor.public_key = public_key
    auditor.key_version += 1
    auditor.save()

    # Log archival of previous key
    logger.info(
        f"Archived previous key version {old_version} for auditor {auditor.id} "
        f"(Fingerprint: {get_fingerprint(old_public_key)})"
    )

    return private_key, public_key, auditor.key_version
