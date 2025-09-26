import uuid
import random
import string


def generate_org_id() -> str:
    """Generate a cloud-compatible organization ID in format: org_xxxxxxxx"""
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"org_{suffix}"


def generate_site_id() -> str:
    """Generate a cloud-compatible site ID using UUID v4"""
    return str(uuid.uuid4())


def generate_device_id() -> str:
    """Generate a cloud-compatible device ID using UUID v4"""
    return str(uuid.uuid4())


def generate_all_ids() -> tuple[str, str, str]:
    """Generate all three IDs at once. Returns (org_id, site_id, device_id)"""
    return generate_org_id(), generate_site_id(), generate_device_id()
