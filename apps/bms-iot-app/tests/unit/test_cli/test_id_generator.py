"""
Test suite for ID generator utility functions.
"""

import pytest
import uuid
from src.utils.id_generator import (
    generate_org_id,
    generate_site_id,
    generate_device_id,
    generate_all_ids,
)


class TestIdGenerator:
    """Test ID generation utility functions."""

    def test_generate_org_id_format(self):
        """Test that organization ID follows the correct format."""
        org_id = generate_org_id()

        # Should start with 'org_'
        assert org_id.startswith(
            "org_"
        ), f"Expected org_id to start with 'org_', got: {org_id}"

        # Should be exactly 12 characters total (org_ + 8 chars)
        assert len(org_id) == 12, f"Expected org_id length 12, got: {len(org_id)}"

        # The suffix should be alphanumeric lowercase
        suffix = org_id[4:]  # Remove 'org_' prefix
        assert len(suffix) == 8, f"Expected suffix length 8, got: {len(suffix)}"
        assert suffix.islower(), f"Expected lowercase suffix, got: {suffix}"
        assert suffix.isalnum(), f"Expected alphanumeric suffix, got: {suffix}"

    def test_generate_org_id_uniqueness(self):
        """Test that multiple calls generate unique organization IDs."""
        org_ids = [generate_org_id() for _ in range(10)]

        # All should be unique
        assert len(set(org_ids)) == 10, "Generated org_ids should be unique"

    def test_generate_site_id_format(self):
        """Test that site ID is a valid UUID."""
        site_id = generate_site_id()

        # Should be a valid UUID
        try:
            uuid_obj = uuid.UUID(site_id)
            assert str(uuid_obj) == site_id, "Should be a properly formatted UUID"
        except ValueError:
            pytest.fail(f"Expected valid UUID, got: {site_id}")

    def test_generate_device_id_format(self):
        """Test that device ID is a valid UUID."""
        device_id = generate_device_id()

        # Should be a valid UUID
        try:
            uuid_obj = uuid.UUID(device_id)
            assert str(uuid_obj) == device_id, "Should be a properly formatted UUID"
        except ValueError:
            pytest.fail(f"Expected valid UUID, got: {device_id}")

    def test_generate_site_id_uniqueness(self):
        """Test that multiple calls generate unique site IDs."""
        site_ids = [generate_site_id() for _ in range(10)]

        # All should be unique
        assert len(set(site_ids)) == 10, "Generated site_ids should be unique"

    def test_generate_device_id_uniqueness(self):
        """Test that multiple calls generate unique device IDs."""
        device_ids = [generate_device_id() for _ in range(10)]

        # All should be unique
        assert len(set(device_ids)) == 10, "Generated device_ids should be unique"

    def test_generate_all_ids(self):
        """Test that generate_all_ids returns tuple with correct formats."""
        org_id, site_id, device_id = generate_all_ids()

        # Test org_id format
        assert org_id.startswith(
            "org_"
        ), f"Expected org_id to start with 'org_', got: {org_id}"
        assert len(org_id) == 12, f"Expected org_id length 12, got: {len(org_id)}"

        # Test site_id is UUID
        try:
            uuid.UUID(site_id)
        except ValueError:
            pytest.fail(f"Expected valid UUID for site_id, got: {site_id}")

        # Test device_id is UUID
        try:
            uuid.UUID(device_id)
        except ValueError:
            pytest.fail(f"Expected valid UUID for device_id, got: {device_id}")

    def test_generate_all_ids_uniqueness(self):
        """Test that generate_all_ids returns unique values across calls."""
        results = [generate_all_ids() for _ in range(5)]

        # Extract each type of ID
        org_ids = [result[0] for result in results]
        site_ids = [result[1] for result in results]
        device_ids = [result[2] for result in results]

        # All should be unique within their type
        assert len(set(org_ids)) == 5, "Generated org_ids should be unique"
        assert len(set(site_ids)) == 5, "Generated site_ids should be unique"
        assert len(set(device_ids)) == 5, "Generated device_ids should be unique"

    def test_cloud_compatibility_format(self):
        """Test that generated IDs match expected cloud format."""
        org_id, site_id, device_id = generate_all_ids()

        # Organization ID should match cloud format: org_xxxxxxxx
        assert org_id.startswith("org_")
        assert len(org_id.split("_")[1]) == 8

        # Site and device IDs should be standard UUID format
        # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (36 chars with dashes)
        assert len(site_id) == 36 and site_id.count("-") == 4
        assert len(device_id) == 36 and device_id.count("-") == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
