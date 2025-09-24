"""
Test deployment runtime configuration.

User Story: As a developer, I want deployment runtime config to validate correctly
"""

import pytest
from src.config.deployment_runtime_config import DeploymentRuntimeConfig


class TestDeploymentRuntimeConfig:
    """Test DeploymentRuntimeConfig dataclass"""

    def test_valid_deployment_runtime_config(self):
        """Test: Valid deployment runtime config creation"""
        config = DeploymentRuntimeConfig(
            organization_id="org_123", site_id="site_456", device_id="device_789"
        )

        assert config.organization_id == "org_123"
        assert config.site_id == "site_456"
        assert config.device_id == "device_789"
        assert config.config_metadata is None

    def test_deployment_runtime_config_with_metadata(self):
        """Test: Deployment runtime config with metadata"""
        metadata = {"version": "1.0", "environment": "production"}
        config = DeploymentRuntimeConfig(
            organization_id="org_123",
            site_id="site_456",
            device_id="device_789",
            config_metadata=metadata,
        )

        assert config.config_metadata == metadata

    def test_deployment_runtime_config_immutability(self):
        """Test: DeploymentRuntimeConfig is immutable (frozen dataclass)"""
        config = DeploymentRuntimeConfig(
            organization_id="org_123", site_id="site_456", device_id="device_789"
        )

        # Should raise an exception when trying to modify
        with pytest.raises(Exception):  # FrozenInstanceError in dataclasses
            config.organization_id = "new_org"

    def test_empty_organization_id_validation(self):
        """Test: Empty organization_id raises ValueError"""
        with pytest.raises(ValueError, match="organization_id cannot be empty"):
            DeploymentRuntimeConfig(
                organization_id="", site_id="site_456", device_id="device_789"
            )

    def test_whitespace_organization_id_validation(self):
        """Test: Whitespace-only organization_id raises ValueError"""
        with pytest.raises(ValueError, match="organization_id cannot be empty"):
            DeploymentRuntimeConfig(
                organization_id="   ", site_id="site_456", device_id="device_789"
            )

    def test_empty_site_id_validation(self):
        """Test: Empty site_id raises ValueError"""
        with pytest.raises(ValueError, match="site_id cannot be empty"):
            DeploymentRuntimeConfig(
                organization_id="org_123", site_id="", device_id="device_789"
            )

    def test_whitespace_site_id_validation(self):
        """Test: Whitespace-only site_id raises ValueError"""
        with pytest.raises(ValueError, match="site_id cannot be empty"):
            DeploymentRuntimeConfig(
                organization_id="org_123", site_id="   ", device_id="device_789"
            )

    def test_empty_device_id_validation(self):
        """Test: Empty device_id raises ValueError"""
        with pytest.raises(ValueError, match="device_id cannot be empty"):
            DeploymentRuntimeConfig(
                organization_id="org_123", site_id="site_456", device_id=""
            )

    def test_whitespace_device_id_validation(self):
        """Test: Whitespace-only device_id raises ValueError"""
        with pytest.raises(ValueError, match="device_id cannot be empty"):
            DeploymentRuntimeConfig(
                organization_id="org_123", site_id="site_456", device_id="   "
            )

    def test_none_values_validation(self):
        """Test: None values raise ValueError due to __post_init__ validation"""
        with pytest.raises(ValueError, match="organization_id cannot be empty"):
            DeploymentRuntimeConfig(
                organization_id=None, site_id="site_456", device_id="device_789"
            )

        with pytest.raises(ValueError, match="site_id cannot be empty"):
            DeploymentRuntimeConfig(
                organization_id="org_123", site_id=None, device_id="device_789"
            )

        with pytest.raises(ValueError, match="device_id cannot be empty"):
            DeploymentRuntimeConfig(
                organization_id="org_123", site_id="site_456", device_id=None
            )

    def test_multiple_validation_errors(self):
        """Test: Multiple validation errors are caught"""
        # This tests that __post_init__ validation is applied
        with pytest.raises(ValueError, match="organization_id cannot be empty"):
            DeploymentRuntimeConfig(
                organization_id="",  # Empty
                site_id="",  # Also empty, but org_id error comes first
                device_id="",  # Also empty
            )


class TestDeploymentRuntimeConfigEdgeCases:
    """Test edge cases for DeploymentRuntimeConfig"""

    def test_config_metadata_types(self):
        """Test: Various metadata types are accepted"""
        # Dictionary metadata
        config1 = DeploymentRuntimeConfig(
            organization_id="org_123",
            site_id="site_456",
            device_id="device_789",
            config_metadata={"key": "value"},
        )
        assert config1.config_metadata == {"key": "value"}

        # Empty dictionary
        config2 = DeploymentRuntimeConfig(
            organization_id="org_123",
            site_id="site_456",
            device_id="device_789",
            config_metadata={},
        )
        assert config2.config_metadata == {}

        # Complex nested structure
        complex_metadata = {
            "environment": "production",
            "features": ["bacnet", "mqtt"],
            "settings": {"timeout": 30, "retries": 3},
        }
        config3 = DeploymentRuntimeConfig(
            organization_id="org_123",
            site_id="site_456",
            device_id="device_789",
            config_metadata=complex_metadata,
        )
        assert config3.config_metadata == complex_metadata

    def test_string_representation(self):
        """Test: String representation contains key information"""
        config = DeploymentRuntimeConfig(
            organization_id="org_123", site_id="site_456", device_id="device_789"
        )

        str_repr = str(config)
        assert "org_123" in str_repr
        assert "site_456" in str_repr
        assert "device_789" in str_repr

    def test_equality_comparison(self):
        """Test: Config objects with same values are equal"""
        config1 = DeploymentRuntimeConfig(
            organization_id="org_123", site_id="site_456", device_id="device_789"
        )

        config2 = DeploymentRuntimeConfig(
            organization_id="org_123", site_id="site_456", device_id="device_789"
        )

        assert config1 == config2

        # Different configs should not be equal
        config3 = DeploymentRuntimeConfig(
            organization_id="org_different", site_id="site_456", device_id="device_789"
        )

        assert config1 != config3

    def test_hashable(self):
        """Test: Config objects are hashable (due to frozen=True)"""
        config1 = DeploymentRuntimeConfig(
            organization_id="org_123", site_id="site_456", device_id="device_789"
        )

        config2 = DeploymentRuntimeConfig(
            organization_id="org_456", site_id="site_789", device_id="device_012"
        )

        # Should be able to use as dictionary keys or in sets
        config_set = {config1, config2}
        assert len(config_set) == 2

        config_dict = {config1: "value1", config2: "value2"}
        assert config_dict[config1] == "value1"
        assert config_dict[config2] == "value2"
