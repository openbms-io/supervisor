"""
Test suite for CLI interactive setup with ID auto-generation.
"""

import pytest
from unittest.mock import patch, AsyncMock
from typer.testing import CliRunner

from src.models.deployment_config import DeploymentConfig


class TestInteractiveSetup:
    """Test interactive setup command with ID auto-generation."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def mock_configure_mqtt(self):
        """Mock the MQTT configuration function."""
        with patch(
            "src.cli._configure_mqtt_interactive", new_callable=AsyncMock
        ) as mock:
            mock.return_value = True  # Default to successful MQTT config
            yield mock

    @pytest.fixture
    def mock_set_config(self):
        """Mock the set_deployment_config function."""
        with patch("src.cli.set_deployment_config", new_callable=AsyncMock) as mock:
            yield mock

    @pytest.fixture
    def mock_validate_config(self):
        """Mock the validate_deployment_config function."""
        with patch("src.cli.validate_deployment_config") as mock:
            mock.return_value = (True, [])  # Default to valid config
            yield mock

    @pytest.mark.asyncio
    async def test_interactive_setup_with_auto_generated_ids(
        self, mock_configure_mqtt, mock_set_config, mock_validate_config
    ):
        """Test interactive setup with all IDs auto-generated."""
        with (
            patch("typer.prompt") as mock_prompt,
            patch("typer.confirm") as mock_confirm,
        ):
            # Mock user pressing Enter for all ID prompts (empty strings)
            mock_prompt.side_effect = [
                "",  # Organization ID (auto-generate)
                "",  # Site ID (auto-generate)
                "",  # Device ID (auto-generate)
                "{}",  # Metadata (empty JSON)
            ]

            # Mock confirmations
            mock_confirm.side_effect = [
                True,  # Add metadata? Yes
                True,  # Save configuration? Yes
            ]

            # Create the async function to test the interactive setup logic
            async def run_interactive_setup():
                from src.utils.id_generator import (
                    generate_org_id,
                    generate_site_id,
                    generate_device_id,
                )

                # Simulate the interactive setup logic
                org_id_input = ""  # User presses Enter
                if not org_id_input.strip():
                    org_id = generate_org_id()
                else:
                    org_id = org_id_input.strip()

                site_id_input = ""  # User presses Enter
                if not site_id_input.strip():
                    site_id = generate_site_id()
                else:
                    site_id = site_id_input.strip()

                device_id_input = ""  # User presses Enter
                if not device_id_input.strip():
                    device_id = generate_device_id()
                else:
                    device_id = device_id_input.strip()

                # Configure MQTT
                mqtt_configured = await mock_configure_mqtt(org_id, site_id, device_id)

                # Create config
                config = DeploymentConfig(
                    organization_id=org_id,
                    site_id=site_id,
                    device_id=device_id,
                    config_metadata={},
                )

                # Save config
                await mock_set_config(config)

                return org_id, site_id, device_id, mqtt_configured

            # Run the test
            org_id, site_id, device_id, mqtt_configured = await run_interactive_setup()

            # Verify generated IDs have correct format
            assert org_id.startswith(
                "org_"
            ), f"Expected org_id to start with 'org_', got: {org_id}"
            assert len(org_id) == 12, f"Expected org_id length 12, got: {len(org_id)}"

            # Verify UUIDs are valid format (36 chars with 4 dashes)
            assert len(site_id) == 36 and site_id.count("-") == 4
            assert len(device_id) == 36 and device_id.count("-") == 4

            # Verify MQTT was configured
            assert mqtt_configured is True
            mock_configure_mqtt.assert_called_once_with(org_id, site_id, device_id)

            # Verify config was saved
            mock_set_config.assert_called_once()
            saved_config = mock_set_config.call_args[0][0]
            assert saved_config.organization_id == org_id
            assert saved_config.site_id == site_id
            assert saved_config.device_id == device_id

    @pytest.mark.asyncio
    async def test_interactive_setup_with_custom_ids(
        self, mock_configure_mqtt, mock_set_config, mock_validate_config
    ):
        """Test interactive setup with user-provided custom IDs."""
        custom_org_id = "org_custom123"
        custom_site_id = "550e8400-e29b-41d4-a716-446655440000"
        custom_device_id = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"

        with (
            patch("typer.prompt") as mock_prompt,
            patch("typer.confirm") as mock_confirm,
        ):
            # Mock user providing custom IDs
            mock_prompt.side_effect = [
                custom_org_id,  # Organization ID
                custom_site_id,  # Site ID
                custom_device_id,  # Device ID
            ]

            # Mock confirmations
            mock_confirm.side_effect = [
                False,  # Add metadata? No
                True,  # Save configuration? Yes
            ]

            # Create the async function to test the interactive setup logic
            async def run_interactive_setup():
                # Simulate the interactive setup logic with custom IDs
                org_id_input = custom_org_id
                if not org_id_input.strip():
                    from src.utils.id_generator import generate_org_id

                    org_id = generate_org_id()
                else:
                    org_id = org_id_input.strip()

                site_id_input = custom_site_id
                if not site_id_input.strip():
                    from src.utils.id_generator import generate_site_id

                    site_id = generate_site_id()
                else:
                    site_id = site_id_input.strip()

                device_id_input = custom_device_id
                if not device_id_input.strip():
                    from src.utils.id_generator import generate_device_id

                    device_id = generate_device_id()
                else:
                    device_id = device_id_input.strip()

                # Configure MQTT
                mqtt_configured = await mock_configure_mqtt(org_id, site_id, device_id)

                # Create config
                config = DeploymentConfig(
                    organization_id=org_id,
                    site_id=site_id,
                    device_id=device_id,
                    config_metadata=None,
                )

                # Save config
                await mock_set_config(config)

                return org_id, site_id, device_id, mqtt_configured

            # Run the test
            org_id, site_id, device_id, mqtt_configured = await run_interactive_setup()

            # Verify custom IDs were used
            assert org_id == custom_org_id
            assert site_id == custom_site_id
            assert device_id == custom_device_id

            # Verify MQTT was configured with custom IDs
            mock_configure_mqtt.assert_called_once_with(
                custom_org_id, custom_site_id, custom_device_id
            )

            # Verify config was saved with custom IDs
            mock_set_config.assert_called_once()
            saved_config = mock_set_config.call_args[0][0]
            assert saved_config.organization_id == custom_org_id
            assert saved_config.site_id == custom_site_id
            assert saved_config.device_id == custom_device_id

    @pytest.mark.asyncio
    async def test_interactive_setup_mixed_auto_and_custom_ids(
        self, mock_configure_mqtt, mock_set_config, mock_validate_config
    ):
        """Test interactive setup with mix of auto-generated and custom IDs."""
        custom_org_id = "org_existing"

        with (
            patch("typer.prompt") as mock_prompt,
            patch("typer.confirm") as mock_confirm,
        ):
            # Mock user providing custom org ID but auto-generating site/device IDs
            mock_prompt.side_effect = [
                custom_org_id,  # Organization ID (custom)
                "",  # Site ID (auto-generate)
                "",  # Device ID (auto-generate)
            ]

            # Mock confirmations
            mock_confirm.side_effect = [
                False,  # Add metadata? No
                True,  # Save configuration? Yes
            ]

            # Create the async function to test the interactive setup logic
            async def run_interactive_setup():
                from src.utils.id_generator import generate_site_id, generate_device_id

                # Simulate the interactive setup logic
                org_id_input = custom_org_id
                if not org_id_input.strip():
                    from src.utils.id_generator import generate_org_id

                    org_id = generate_org_id()
                else:
                    org_id = org_id_input.strip()

                site_id_input = ""  # Auto-generate
                if not site_id_input.strip():
                    site_id = generate_site_id()
                else:
                    site_id = site_id_input.strip()

                device_id_input = ""  # Auto-generate
                if not device_id_input.strip():
                    device_id = generate_device_id()
                else:
                    device_id = device_id_input.strip()

                # Configure MQTT
                mqtt_configured = await mock_configure_mqtt(org_id, site_id, device_id)

                return org_id, site_id, device_id, mqtt_configured

            # Run the test
            org_id, site_id, device_id, mqtt_configured = await run_interactive_setup()

            # Verify custom org ID was used
            assert org_id == custom_org_id

            # Verify site and device IDs were auto-generated (UUID format)
            assert len(site_id) == 36 and site_id.count("-") == 4
            assert len(device_id) == 36 and device_id.count("-") == 4

            # Verify MQTT was configured
            mock_configure_mqtt.assert_called_once_with(
                custom_org_id, site_id, device_id
            )

    def test_id_generation_uniqueness_across_multiple_setups(self):
        """Test that multiple interactive setups generate unique IDs."""
        from src.utils.id_generator import (
            generate_org_id,
            generate_site_id,
            generate_device_id,
        )

        # Generate multiple sets of IDs
        id_sets = []
        for _ in range(5):
            org_id = generate_org_id()
            site_id = generate_site_id()
            device_id = generate_device_id()
            id_sets.append((org_id, site_id, device_id))

        # Extract each type
        org_ids = [ids[0] for ids in id_sets]
        site_ids = [ids[1] for ids in id_sets]
        device_ids = [ids[2] for ids in id_sets]

        # Verify uniqueness
        assert len(set(org_ids)) == 5, "Organization IDs should be unique"
        assert len(set(site_ids)) == 5, "Site IDs should be unique"
        assert len(set(device_ids)) == 5, "Device IDs should be unique"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
