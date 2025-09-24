"""
Test deployment configuration model.

User Story: As a developer, I want deployment configuration to be validated correctly
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from src.models.deployment_config import (
    DeploymentConfig,
    DeploymentConfigModel,
    set_deployment_config,
    get_current_deployment_config,
    get_current_deployment_config_as_dict,
    validate_deployment_config,
    has_valid_deployment_config,
)


class TestDeploymentConfig:
    """Test DeploymentConfig Pydantic model"""

    def test_deployment_config_creation(self):
        """Test: Deployment config model creation with required fields"""
        config = DeploymentConfig(
            organization_id="org_123", site_id="site_456", device_id="device_789"
        )

        assert config.organization_id == "org_123"
        assert config.site_id == "site_456"
        assert config.device_id == "device_789"
        assert config.config_metadata is None

    def test_deployment_config_with_metadata(self):
        """Test: Deployment config with metadata"""
        metadata = {"version": "1.0", "environment": "production"}
        config = DeploymentConfig(
            organization_id="org_123",
            site_id="site_456",
            device_id="device_789",
            config_metadata=metadata,
        )

        assert config.config_metadata == metadata

    def test_deployment_config_model_creation(self):
        """Test: SQLModel deployment config creation"""
        config_model = DeploymentConfigModel(
            organization_id="org_123", site_id="site_456", device_id="device_789"
        )

        assert config_model.organization_id == "org_123"
        assert config_model.site_id == "site_456"
        assert config_model.device_id == "device_789"
        assert config_model.config_metadata is None
        assert isinstance(config_model.created_at, datetime)
        assert isinstance(config_model.updated_at, datetime)


class TestDeploymentConfigValidation:
    """Test deployment config validation functions"""

    def test_valid_deployment_config(self):
        """Test: Valid deployment configuration passes validation"""
        config = DeploymentConfig(
            organization_id="org_123", site_id="site_456", device_id="device_789"
        )

        is_valid, errors = validate_deployment_config(config)

        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_organization_id_empty(self):
        """Test: Empty organization_id fails validation"""
        config = DeploymentConfig(
            organization_id="", site_id="site_456", device_id="device_789"
        )

        is_valid, errors = validate_deployment_config(config)

        assert is_valid is False
        assert "organization_id is required and cannot be empty" in errors

    def test_invalid_organization_id_whitespace(self):
        """Test: Whitespace-only organization_id fails validation"""
        config = DeploymentConfig(
            organization_id="   ", site_id="site_456", device_id="device_789"
        )

        is_valid, errors = validate_deployment_config(config)

        assert is_valid is False
        assert "organization_id is required and cannot be empty" in errors

    def test_invalid_organization_id_prefix(self):
        """Test: Organization_id without 'org_' prefix fails validation"""
        config = DeploymentConfig(
            organization_id="123", site_id="site_456", device_id="device_789"
        )

        is_valid, errors = validate_deployment_config(config)

        assert is_valid is False
        assert "organization_id should start with 'org_'" in errors

    def test_invalid_site_id_empty(self):
        """Test: Empty site_id fails validation"""
        config = DeploymentConfig(
            organization_id="org_123", site_id="", device_id="device_789"
        )

        is_valid, errors = validate_deployment_config(config)

        assert is_valid is False
        assert "site_id is required and cannot be empty" in errors

    def test_invalid_device_id_empty(self):
        """Test: Empty device_id fails validation"""
        config = DeploymentConfig(
            organization_id="org_123", site_id="site_456", device_id=""
        )

        is_valid, errors = validate_deployment_config(config)

        assert is_valid is False
        assert "device_id is required and cannot be empty" in errors

    def test_multiple_validation_errors(self):
        """Test: Multiple validation errors are collected"""
        config = DeploymentConfig(
            organization_id="123",  # Missing org_ prefix
            site_id="",  # Empty
            device_id="   ",  # Whitespace only
        )

        is_valid, errors = validate_deployment_config(config)

        assert is_valid is False
        assert len(errors) == 3
        assert "organization_id should start with 'org_'" in errors
        assert "site_id is required and cannot be empty" in errors
        assert "device_id is required and cannot be empty" in errors


class TestDeploymentConfigDatabaseOperations:
    """Test database operations for deployment config"""

    @pytest.mark.asyncio
    async def test_set_deployment_config(self):
        """Test: Set/update deployment configuration"""
        with patch("src.models.deployment_config.get_session") as mock_get_session:
            mock_session = AsyncMock()

            # Create async context manager mock
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            # Mock existing config query result (empty)
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.delete = AsyncMock()
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()

            config = DeploymentConfig(
                organization_id="org_123",
                site_id="site_456",
                device_id="device_789",
                config_metadata={"test": "data"},
            )

            result = await set_deployment_config(config)

            assert isinstance(result, DeploymentConfigModel)
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_deployment_config_replaces_existing(self):
        """Test: Set deployment config replaces existing config"""
        with patch("src.models.deployment_config.get_session") as mock_get_session:
            mock_session = AsyncMock()

            # Create async context manager mock
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            # Mock existing config
            existing_config = Mock(spec=DeploymentConfigModel)
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = [existing_config]
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.delete = AsyncMock()
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()

            config = DeploymentConfig(
                organization_id="org_456", site_id="site_789", device_id="device_012"
            )

            result = await set_deployment_config(config)

            # Should delete existing config
            mock_session.delete.assert_called_once_with(existing_config)
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            assert isinstance(result, DeploymentConfigModel)

    @pytest.mark.asyncio
    async def test_get_current_deployment_config_exists(self):
        """Test: Get current deployment config when one exists"""
        with patch("src.models.deployment_config.get_session") as mock_get_session:
            mock_session = AsyncMock()

            # Create async context manager mock
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            # Mock config exists
            mock_config = Mock(spec=DeploymentConfigModel)
            mock_result = Mock()
            mock_result.scalars.return_value.first.return_value = mock_config
            mock_session.execute = AsyncMock(return_value=mock_result)

            result = await get_current_deployment_config()

            assert result == mock_config
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_deployment_config_none(self):
        """Test: Get current deployment config when none exists"""
        with patch("src.models.deployment_config.get_session") as mock_get_session:
            mock_session = AsyncMock()

            # Create async context manager mock
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            # Mock no config exists
            mock_result = Mock()
            mock_result.scalars.return_value.first.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)

            result = await get_current_deployment_config()

            assert result is None

    @pytest.mark.asyncio
    async def test_get_current_deployment_config_as_dict_exists(self):
        """Test: Get current deployment config as dict when one exists"""
        with patch(
            "src.models.deployment_config.get_current_deployment_config"
        ) as mock_get_config:
            mock_config = Mock(spec=DeploymentConfigModel)
            mock_config.organization_id = "org_123"
            mock_config.site_id = "site_456"
            mock_config.device_id = "device_789"
            mock_config.config_metadata = {"test": "data"}
            mock_get_config.return_value = mock_config

            result = await get_current_deployment_config_as_dict()

            expected = {
                "organization_id": "org_123",
                "site_id": "site_456",
                "device_id": "device_789",
                "config_metadata": {"test": "data"},
            }
            assert result == expected

    @pytest.mark.asyncio
    async def test_get_current_deployment_config_as_dict_none(self):
        """Test: Get current deployment config as dict when none exists"""
        with patch(
            "src.models.deployment_config.get_current_deployment_config"
        ) as mock_get_config:
            mock_get_config.return_value = None

            result = await get_current_deployment_config_as_dict()

            assert result is None

    @pytest.mark.asyncio
    async def test_get_current_deployment_config_as_dict_none_metadata(self):
        """Test: Get current deployment config as dict with None metadata"""
        with patch(
            "src.models.deployment_config.get_current_deployment_config"
        ) as mock_get_config:
            mock_config = Mock(spec=DeploymentConfigModel)
            mock_config.organization_id = "org_123"
            mock_config.site_id = "site_456"
            mock_config.device_id = "device_789"
            mock_config.config_metadata = None
            mock_get_config.return_value = mock_config

            result = await get_current_deployment_config_as_dict()

            expected = {
                "organization_id": "org_123",
                "site_id": "site_456",
                "device_id": "device_789",
                "config_metadata": {},
            }
            assert result == expected


class TestHasValidDeploymentConfig:
    """Test has_valid_deployment_config function"""

    @pytest.mark.asyncio
    async def test_has_valid_deployment_config_valid(self):
        """Test: Valid deployment config returns True"""
        with patch(
            "src.models.deployment_config.get_current_deployment_config"
        ) as mock_get_config:
            mock_config = Mock(spec=DeploymentConfigModel)
            mock_config.organization_id = "org_123"
            mock_config.site_id = "site_456"
            mock_config.device_id = "device_789"
            mock_config.config_metadata = None
            mock_get_config.return_value = mock_config

            is_valid, errors = await has_valid_deployment_config()

            assert is_valid is True
            assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_has_valid_deployment_config_none(self):
        """Test: No deployment config returns False"""
        with patch(
            "src.models.deployment_config.get_current_deployment_config"
        ) as mock_get_config:
            mock_get_config.return_value = None

            is_valid, errors = await has_valid_deployment_config()

            assert is_valid is False
            assert len(errors) == 1
            assert (
                "No deployment configuration found. Run 'config set' to configure."
                in errors
            )

    @pytest.mark.asyncio
    async def test_has_valid_deployment_config_invalid(self):
        """Test: Invalid deployment config returns False"""
        with patch(
            "src.models.deployment_config.get_current_deployment_config"
        ) as mock_get_config:
            mock_config = Mock(spec=DeploymentConfigModel)
            mock_config.organization_id = "123"  # Invalid - no org_ prefix
            mock_config.site_id = ""  # Invalid - empty
            mock_config.device_id = "device_789"
            mock_config.config_metadata = None
            mock_get_config.return_value = mock_config

            is_valid, errors = await has_valid_deployment_config()

            assert is_valid is False
            assert len(errors) == 2
            assert "organization_id should start with 'org_'" in errors
            assert "site_id is required and cannot be empty" in errors


class TestDeploymentConfigEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_set_deployment_config_session_failure(self):
        """Test: Set deployment config handles session failure"""
        with patch("src.models.deployment_config.get_session") as mock_get_session:
            # Mock context manager that raises exception on enter
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(
                side_effect=RuntimeError("Failed to get database session")
            )
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            config = DeploymentConfig(
                organization_id="org_123", site_id="site_456", device_id="device_789"
            )

            # Should raise RuntimeError
            with pytest.raises(RuntimeError, match="Failed to get database session"):
                await set_deployment_config(config)

    @pytest.mark.asyncio
    async def test_database_operations_with_session_failure(self):
        """Test: Database operations handle session failures gracefully"""
        with patch("src.models.deployment_config.get_session") as mock_get_session:
            # Mock context manager that raises exception on enter
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(
                side_effect=RuntimeError("Failed to get database session")
            )
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            # Test get_current_deployment_config raises exception on session failure
            with pytest.raises(RuntimeError, match="Failed to get database session"):
                await get_current_deployment_config()

    def test_validate_deployment_config_none_values(self):
        """Test: Validation handles None values correctly"""
        # This should not happen in practice due to Pydantic model validation,
        # but test defensive handling
        config = DeploymentConfig(
            organization_id="org_123", site_id="site_456", device_id="device_789"
        )

        # Manually set to None to test edge case
        config.organization_id = None
        config.site_id = None
        config.device_id = None

        is_valid, errors = validate_deployment_config(config)

        assert is_valid is False
        assert len(errors) >= 3  # Should catch the None values
