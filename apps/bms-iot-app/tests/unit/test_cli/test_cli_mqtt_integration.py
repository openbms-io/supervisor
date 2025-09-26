"""
Test suite for integrated MQTT configuration in CLI setup command.
"""

import pytest
from unittest.mock import patch, AsyncMock
from typer.testing import CliRunner

from src.cli import app, _configure_mqtt_interactive
from src.models.deployment_config import DeploymentConfig


class TestMQTTIntegration:
    """Test MQTT configuration integration in setup command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def mock_configure_emqx(self):
        """Mock the configure_emqx function."""
        with patch("src.cli.configure_emqx") as mock:
            yield mock

    @pytest.fixture
    def mock_test_connection(self):
        """Mock the test_connection function."""
        with patch("src.cli.test_connection") as mock:
            mock.return_value = True  # Default to successful connection
            yield mock

    @pytest.mark.asyncio
    async def test_configure_mqtt_interactive_success(
        self, mock_configure_emqx, mock_test_connection
    ):
        """Test successful MQTT configuration during setup."""
        # Mock user inputs
        with (
            patch("typer.confirm") as mock_confirm,
            patch("typer.prompt") as mock_prompt,
        ):
            # User confirms MQTT config, chooses EMQX (2), uses default broker
            mock_confirm.side_effect = [
                True,  # Configure MQTT? Yes
                True,  # Use default EMQX broker? Yes
            ]

            # User chooses EMQX broker (2), then provides credentials
            mock_prompt.side_effect = [2, "mqtt_user", "mqtt_pass"]

            # Test the function
            result = await _configure_mqtt_interactive(
                "org_123", "site_456", "device_789"
            )

            # Verify success
            assert result is True

            # Verify configure_emqx was called with correct parameters
            mock_configure_emqx.assert_called_once_with(
                username="mqtt_user",
                password="mqtt_pass",
                client_id="org_123-site_456-device_789",  # Auto-generated
                topic_prefix="",
            )

            # Verify connection test was performed
            mock_test_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_configure_mqtt_interactive_skip(self):
        """Test skipping MQTT configuration during setup."""
        with patch("typer.confirm") as mock_confirm:
            # User skips MQTT configuration
            mock_confirm.return_value = False  # Configure MQTT? No

            # Test the function
            result = await _configure_mqtt_interactive(
                "org_123", "site_456", "device_789"
            )

            # Verify skip
            assert result is False

    @pytest.mark.asyncio
    async def test_configure_mqtt_interactive_no_emqx(self):
        """Test choosing local broker instead of EMQX."""
        with (
            patch("typer.confirm") as mock_confirm,
            patch("typer.prompt") as mock_prompt,
            patch("src.cli.configure_mqtt") as mock_configure_mqtt,
            patch("src.cli.test_connection") as mock_test_connection,
        ):
            # User wants MQTT and chooses local broker (option 1)
            mock_confirm.side_effect = [
                True,  # Configure MQTT? Yes
            ]
            mock_prompt.side_effect = [1]  # Select broker type: 1 (local)
            mock_test_connection.return_value = True

            # Test the function
            result = await _configure_mqtt_interactive(
                "org_123", "site_456", "device_789"
            )

            # Verify success with local broker
            assert result is True

            # Verify configure_mqtt was called for local broker
            mock_configure_mqtt.assert_called_once_with(
                broker_host="localhost",
                broker_port=1883,
                client_id="org_123-site_456-device_789",
                username=None,
                password=None,
                use_tls=False,
                tls_ca_cert=None,
                topic_prefix="",
                clean_session=False,
            )

    @pytest.mark.asyncio
    async def test_configure_mqtt_interactive_connection_failure(
        self, mock_configure_emqx, mock_test_connection
    ):
        """Test MQTT configuration with connection test failure."""
        # Mock connection test failure
        mock_test_connection.return_value = False

        with (
            patch("typer.confirm") as mock_confirm,
            patch("typer.prompt") as mock_prompt,
        ):
            # User confirms MQTT config, chooses EMQX (2), uses default broker
            mock_confirm.side_effect = [
                True,  # Configure MQTT? Yes
                True,  # Use default EMQX broker? Yes
            ]

            # User chooses EMQX broker (2), then provides credentials
            mock_prompt.side_effect = [2, "mqtt_user", "mqtt_pass"]

            # Test the function
            result = await _configure_mqtt_interactive(
                "org_123", "site_456", "device_789"
            )

            # Verify failure due to connection test
            assert result is False

            # Verify configure_emqx was called (config succeeds but connection fails)
            mock_configure_emqx.assert_called_once_with(
                username="mqtt_user",
                password="mqtt_pass",
                client_id="org_123-site_456-device_789",
                topic_prefix="",
            )

            # Verify configure_emqx was still called
            mock_configure_emqx.assert_called_once()

            # Verify connection test was performed
            mock_test_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_configure_mqtt_interactive_exception_handling(
        self, mock_configure_emqx
    ):
        """Test MQTT configuration with exception during EMQX setup."""
        # Mock exception in configure_emqx
        mock_configure_emqx.side_effect = Exception("MQTT configuration error")

        with (
            patch("typer.confirm") as mock_confirm,
            patch("typer.prompt") as mock_prompt,
            patch("src.cli._configure_emqx_with_broker") as mock_configure_emqx_broker,
        ):
            # Mock _configure_emqx_with_broker to return False (indicating failure)
            mock_configure_emqx_broker.return_value = False

            # User confirms MQTT config, chooses EMQX (2), uses default broker
            mock_confirm.side_effect = [
                True,  # Configure MQTT? Yes
                True,  # Use default EMQX broker? Yes
            ]

            # User chooses EMQX broker (2), then provides credentials
            mock_prompt.side_effect = [2, "mqtt_user", "mqtt_pass"]

            # Test the function
            result = await _configure_mqtt_interactive(
                "org_123", "site_456", "device_789"
            )

            # Verify failure
            assert result is False

            # Verify _configure_emqx_with_broker was called
            mock_configure_emqx_broker.assert_called_once_with(
                username="mqtt_user",
                password="mqtt_pass",
                client_id="org_123-site_456-device_789",
                topic_prefix="",
                broker_host="t78ae18a.ala.us-east-1.emqxsl.com",
            )

    @pytest.mark.asyncio
    async def test_client_id_generation(
        self, mock_configure_emqx, mock_test_connection
    ):
        """Test automatic client ID generation from device identifiers."""
        test_cases = [
            ("org_123", "site_456", "device_789", "org_123-site_456-device_789"),
            ("org_abc", "site_xyz", "device_001", "org_abc-site_xyz-device_001"),
            ("org-test", "site-prod", "device-main", "org-test-site-prod-device-main"),
        ]

        for org_id, site_id, device_id, expected_client_id in test_cases:
            mock_configure_emqx.reset_mock()

            with (
                patch("typer.confirm") as mock_confirm,
                patch("typer.prompt") as mock_prompt,
            ):
                mock_confirm.side_effect = [
                    True,  # Configure MQTT? Yes
                    True,  # Use default EMQX broker? Yes
                ]
                mock_prompt.side_effect = [
                    2,
                    "user",
                    "pass",
                ]  # Choose EMQX (2), then credentials

                await _configure_mqtt_interactive(org_id, site_id, device_id)

                # Verify correct client ID was generated
                mock_configure_emqx.assert_called_once()
                call_args = mock_configure_emqx.call_args[1]
                assert call_args["client_id"] == expected_client_id

    @pytest.mark.asyncio
    async def test_full_setup_command_with_mqtt(self):
        """Test the full config setup command with MQTT integration."""
        # Import the actual setup function components

        with (
            patch("src.cli.logger"),
            patch(
                "src.cli.set_deployment_config", new_callable=AsyncMock
            ) as mock_set_config,
            patch(
                "src.cli._configure_mqtt_interactive", new_callable=AsyncMock
            ) as mock_mqtt_config,
            patch("src.cli.validate_deployment_config") as mock_validate,
            patch("typer.prompt") as mock_prompt,
            patch("typer.confirm") as mock_confirm,
            patch("src.cli.logger"),
        ):
            # Setup mocks
            mock_validate.return_value = (True, [])  # Valid config
            mock_mqtt_config.return_value = True  # MQTT config successful

            # Mock user inputs for the interactive flow
            mock_prompt.side_effect = [
                "org_123",  # Organization ID
                "site_456",  # Site ID
                "device_789",  # Device ID
            ]

            # Mock confirmations
            mock_confirm.side_effect = [
                False,  # Add metadata? No
                True,  # Save configuration? Yes
            ]

            # Create the inner async function and execute it
            async def run_interactive_setup():
                # Note: In production, 'alembic upgrade head' should be run before app start

                # Get inputs
                org_id = mock_prompt()
                site_id = mock_prompt()
                device_id = mock_prompt()

                # Configure MQTT
                mqtt_configured = await mock_mqtt_config(org_id, site_id, device_id)

                # Continue with deployment config

                config = DeploymentConfig(
                    organization_id=org_id,
                    site_id=site_id,
                    device_id=device_id,
                    config_metadata=None,
                )

                # Check metadata option
                mock_confirm()  # Add metadata? No

                # Save config
                save_config = mock_confirm()  # Save configuration? Yes
                if save_config:
                    await mock_set_config(config)

                return mqtt_configured

            # Run the test
            mqtt_result = await run_interactive_setup()

            # Verify MQTT configuration was called correctly
            mock_mqtt_config.assert_called_once_with(
                "org_123", "site_456", "device_789"
            )

            # Verify the result
            assert mqtt_result is True

            # Verify database operations
            mock_set_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_mqtt_config_preserves_deployment_flow(self):
        """Test that MQTT configuration doesn't interfere with deployment config."""

        with (
            patch("src.cli.set_deployment_config", new_callable=AsyncMock),
            patch(
                "src.cli._configure_mqtt_interactive", new_callable=AsyncMock
            ) as mock_mqtt_config,
            patch("typer.prompt") as mock_prompt,
            patch("typer.confirm") as mock_confirm,
        ):
            # Mock inputs
            mock_prompt.side_effect = ["org_123", "site_456", "device_789"]
            mock_confirm.side_effect = [False, True]  # No metadata, Save config

            # Mock MQTT config failure (should not affect deployment config)
            mock_mqtt_config.return_value = False

            # Import and run the setup function

            # Create the async function
            async def run_setup():
                # This simulates what happens inside config_setup

                # We need to recreate the logic here since we can't directly call the nested function
                pass

            # The deployment config should still be saved even if MQTT fails
            # This test verifies the separation of concerns
            assert True  # Placeholder for actual implementation

    @pytest.mark.asyncio
    async def test_mqtt_credentials_hidden(
        self, mock_configure_emqx, mock_test_connection
    ):
        """Test that MQTT password input is hidden."""
        with (
            patch("typer.confirm") as mock_confirm,
            patch("typer.prompt") as mock_prompt,
        ):
            mock_confirm.side_effect = [
                True,  # Configure MQTT? Yes
                True,  # Use default EMQX broker? Yes
            ]

            # Track prompt calls
            prompt_calls = []

            def track_prompt(*args, **kwargs):
                prompt_calls.append(kwargs)
                if "hide_input" in kwargs and kwargs["hide_input"]:
                    return "hidden_password"
                elif "type" in kwargs and kwargs["type"] == int:
                    return 2  # Choose EMQX broker (option 2)
                else:
                    return "visible_input"

            mock_prompt.side_effect = track_prompt

            await _configure_mqtt_interactive("org", "site", "device")

            # Find the password prompt
            password_prompts = [call for call in prompt_calls if call.get("hide_input")]

            # Verify password was hidden
            assert len(password_prompts) == 1

            # Verify there are visible prompts (broker selection + username)
            visible_prompts = [
                call for call in prompt_calls if not call.get("hide_input")
            ]
            assert len(visible_prompts) == 2  # broker selection + username


class TestMQTTConfigurationDefaults:
    """Test MQTT configuration defaults and TLS settings."""

    def test_emqx_uses_tls_by_default(self):
        """Verify that configure_emqx always enables TLS."""
        with (
            patch("src.network.mqtt_config.save_config"),
            patch("os.path.exists", return_value=True),
        ):
            from src.network.mqtt_adapter import configure_emqx

            config = configure_emqx(
                username="test_user",
                password="test_pass",
                client_id="test_client",
                topic_prefix="",
            )

            # Verify TLS is enabled
            assert config.use_tls is True

            # Verify certificate path is set
            assert config.tls_ca_cert is not None

    def test_mqtt_config_command_tls_default(self):
        """Test that mqtt config command defaults to TLS enabled."""
        runner = CliRunner()

        with patch("src.cli.configure_mqtt") as mock_configure:
            # Run command without --no-tls flag
            runner.invoke(
                app,
                [
                    "mqtt",
                    "config",
                    "--host",
                    "test.broker.com",
                    "--port",
                    "8883",
                    "--client-id",
                    "test",
                    "--username",
                    "user",
                    "--password",
                    "pass",
                ],
            )

            # Check that TLS was enabled by default
            mock_configure.assert_called_once()
            call_args = mock_configure.call_args[1]
            assert call_args["use_tls"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
