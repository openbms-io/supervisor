"""
BMS IoT Application Command Line Interface.
Provides commands for BACnet monitoring and MQTT integration.
"""

import asyncio
from typing import Optional

import typer
from rich.console import Console

from src.utils.logger import logger

# from src.simulator.bacnet_simulator_config import DEVICE_CONFIGS, GATEWAY_CONFIG, WRITE_CONFIG
# from apps.bms_bacnet_simulator.bacnet_simulator_config import SIMULATOR_CONFIG

# from apps.bms_bacnet_simulator.bacnet_simulator import MultiSimulationManager
from src.network.credentials import save_credentials
from .network.mqtt_adapter import (
    configure_mqtt,
    configure_emqx,
    test_connection,
    get_current_config,
    publish_message,
)
from .network.mqtt_config import emqx_cloud_config_template

from src.main import main as main_entrypoint
from src.models.deployment_config import (
    DeploymentConfig,
    set_deployment_config,
    get_current_deployment_config,
    validate_deployment_config,
    has_valid_deployment_config,
)

# Set up rich console for direct output
console = Console()

# Initialize Typer app
app = typer.Typer()
mqtt_app = typer.Typer()
config_app = typer.Typer()
app.add_typer(mqtt_app, name="mqtt", help="MQTT client commands and configuration")
app.add_typer(config_app, name="config", help="Deployment configuration management")


# Helper functions to consolidate repetitive MQTT logic
def _configure_emqx_with_broker(
    username: str,
    password: str,
    client_id: str,
    topic_prefix: str = "",
    broker_host: Optional[str] = None,
) -> bool:
    """Configure EMQX with default or custom broker.

    Args:
        username: MQTT username
        password: MQTT password
        client_id: MQTT client ID
        topic_prefix: Topic prefix
        broker_host: Custom broker host (uses default if None)

    Returns:
        bool: True if configuration successful, False otherwise
    """
    try:
        if broker_host and broker_host != emqx_cloud_config_template.broker_host:
            # Use custom broker
            configure_mqtt(
                broker_host=broker_host,
                broker_port=8883,  # EMQX always uses 8883 for TLS
                client_id=client_id,
                username=username,
                password=password,
                use_tls=True,  # Always use TLS for EMQX
                tls_ca_cert=None,  # Will use default cert if available
                topic_prefix=topic_prefix,
            )
            logger.info(
                f"✓ MQTT configured successfully with custom broker: {broker_host} (TLS enabled)"
            )
        else:
            # Use default EMQX broker
            configure_emqx(
                username=username,
                password=password,
                client_id=client_id,
                topic_prefix=topic_prefix,
            )
            logger.info(
                "✓ MQTT configured successfully with default broker (TLS enabled)"
            )
        return True

    except FileNotFoundError as e:
        logger.error(f"Certificate file not found: {e}")
        logger.info(
            "Please ensure the CA certificate is available or use a custom broker"
        )
        return False
    except Exception as e:
        logger.error(f"MQTT configuration error: {e}")
        logger.info(
            "You can reconfigure later with: python -m src.cli mqtt config-emqx"
        )
        return False


def _get_mqtt_credentials_interactive() -> tuple[str, str]:
    """Get MQTT credentials from user input.

    Returns:
        tuple: (username, password)
    """
    mqtt_username = typer.prompt("MQTT Username")
    mqtt_password = typer.prompt("MQTT Password", hide_input=True)
    return mqtt_username, mqtt_password


def _get_broker_choice_interactive() -> str:
    """Get broker choice from user input.

    Returns:
        str: Broker hostname choice
    """
    logger.info("\n🔗 MQTT Broker Selection")
    logger.info("Choose your MQTT broker type:")
    logger.info("1. Local broker (localhost:1883, no TLS)")
    logger.info("2. EMQX Cloud broker (TLS enabled)")

    try:
        choice = typer.prompt("Select broker type", type=int, default=1)
    except (ValueError, TypeError):
        logger.error("Invalid choice. Using localhost.")
        return "localhost"

    if choice == 1:
        return "localhost"
    elif choice == 2:
        default_broker = emqx_cloud_config_template.broker_host
        use_default = typer.confirm(
            f"Use default EMQX broker ({default_broker})?", default=True
        )

        if use_default:
            return default_broker
        else:
            return typer.prompt(
                "Enter your EMQX broker hostname (e.g., yourbroker.emqxsl.com)"
            )
    else:
        logger.error("Invalid choice. Using localhost.")
        return "localhost"


def _configure_local_broker(client_id: str) -> bool:
    """Configure local MQTT broker (localhost, no TLS, no credentials, persistent sessions).

    Args:
        client_id: MQTT client ID

    Returns:
        bool: True if configuration successful, False otherwise
    """
    try:
        configure_mqtt(
            broker_host="localhost",
            broker_port=1883,
            client_id=client_id,
            username=None,
            password=None,
            use_tls=False,
            tls_ca_cert=None,
            topic_prefix="",
            clean_session=False,
        )
        logger.info(
            "✓ MQTT configured for local broker (localhost:1883, no TLS, persistent sessions)"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to configure local MQTT broker: {e}")
        return False


def _test_and_report_connection() -> bool:
    """Test MQTT connection and report results.

    Returns:
        bool: True if connection successful, False otherwise
    """
    logger.info("Testing MQTT connection...")
    if test_connection():
        logger.info("✓ MQTT connection test successful!")
        return True
    else:
        logger.warning("⚠️ MQTT connection test failed")
        logger.info(
            "You can reconfigure later with: python -m src.cli mqtt config-emqx"
        )
        return False


@app.command()
def set_credentials(
    client_id: str = typer.Argument(..., help="Client ID for authentication"),
    secret_key: str = typer.Argument(..., help="Secret key for authentication"),
):
    """Set authentication credentials."""
    try:
        save_credentials(client_id, secret_key)
        logger.info(f"Credentials saved for client ID: {client_id}")
    except Exception as e:
        logger.error(f"Failed to save credentials: {e}")
        raise typer.Exit(1)


@mqtt_app.command("config")
def cmd_configure_mqtt(
    broker_host: str = typer.Option(
        "localhost", "--host", "-h", help="MQTT broker hostname or IP"
    ),
    broker_port: int = typer.Option(1883, "--port", "-p", help="MQTT broker port"),
    client_id: str = typer.Option(
        "bms-iot-client", "--client-id", help="MQTT client ID"
    ),
    username: Optional[str] = typer.Option(
        None, "--username", "-u", help="MQTT username"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-P", help="MQTT password"
    ),
    use_tls: bool = typer.Option(
        True, "--tls/--no-tls", help="Use TLS for MQTT connection (default: enabled)"
    ),
    tls_ca_cert: Optional[str] = typer.Option(
        None, "--ca-cert", help="Path to CA certificate file"
    ),
    topic_prefix: str = typer.Option(
        "bms/monitoring", "--topic-prefix", "-t", help="MQTT topic prefix"
    ),
    clean_session: bool = typer.Option(
        True,
        "--clean-session/--persistent-session",
        help="Use clean session (default: True)",
    ),
):
    """Configure MQTT client connection parameters (TLS enabled by default)."""
    try:
        configure_mqtt(
            broker_host=broker_host,
            broker_port=broker_port,
            client_id=client_id,
            username=username,
            password=password,
            use_tls=use_tls,
            tls_ca_cert=tls_ca_cert,
            topic_prefix=topic_prefix,
            clean_session=clean_session,
        )
    except Exception as e:
        logger.error(f"Failed to configure MQTT: {e}")
        raise typer.Exit(1)


@mqtt_app.command("config-emqx")
def cmd_configure_emqx_mqtt(
    username: str = typer.Option(
        ..., "--username", "-u", help="MQTT username for EMQX"
    ),
    password: str = typer.Option(
        ..., "--password", "-P", help="MQTT password for EMQX"
    ),
    client_id: str = typer.Option(
        "bms-iot-client", "--client-id", help="MQTT client ID"
    ),
    topic_prefix: str = typer.Option(
        "", "--topic-prefix", "-t", help="MQTT topic prefix"
    ),
    broker_host: Optional[str] = typer.Option(
        None,
        "--broker",
        "-b",
        help="Custom EMQX broker hostname (defaults to t78ae18a.ala.us-east-1.emqxsl.com)",
    ),
):
    """Configure MQTT client for EMQX with TLS."""
    success = _configure_emqx_with_broker(
        username=username,
        password=password,
        client_id=client_id,
        topic_prefix=topic_prefix,
        broker_host=broker_host,
    )

    if not success:
        raise typer.Exit(1)


@mqtt_app.command("test")
def cmd_test_mqtt_connection():
    """Test MQTT connection with current configuration."""
    if not test_connection():
        raise typer.Exit(1)


@mqtt_app.command("show")
def cmd_show_mqtt_config():
    """Show current MQTT configuration."""
    config = get_current_config()
    for key, value in config.items():
        logger.info(f"  {key}: {value}")


@mqtt_app.command("publish")
def cmd_publish_test_message(
    topic: str = typer.Option("test", "--topic", "-t", help="MQTT topic to publish to"),
    message: str = typer.Option(
        None, "--message", "-m", help="Message content (optional)"
    ),
    temperature: Optional[float] = typer.Option(
        None, "--temp", help="Temperature value (optional)"
    ),
    humidity: Optional[float] = typer.Option(
        None, "--humidity", help="Humidity value (optional)"
    ),
):
    """Publish a test message to the MQTT broker."""
    success = publish_message(
        topic=topic, message=message, temperature=temperature, humidity=humidity
    )
    if not success:
        raise typer.Exit(1)


@config_app.command("set")
def config_set(
    org_id: str = typer.Option(
        ..., "--org-id", help="Organization ID (e.g., org_2wPf0VwqcNbhrc0F0j3iws2TCkq)"
    ),
    site_id: str = typer.Option(..., "--site-id", help="Site ID (UUID format)"),
    device_id: str = typer.Option(
        ..., "--device-id", help="IoT Device ID (UUID format)"
    ),
    config_metadata: Optional[str] = typer.Option(
        None, "--config-metadata", help="Additional metadata as JSON string"
    ),
):
    """Set deployment configuration for organization, site, and device IDs."""

    async def _set_config():
        # Parse metadata if provided
        metadata_dict = None
        if config_metadata:
            try:
                import json

                metadata_dict = json.loads(config_metadata)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in config_metadata: {e}")
                raise typer.Exit(1)

        # Create and validate config
        config = DeploymentConfig(
            organization_id=org_id,
            site_id=site_id,
            device_id=device_id,
            config_metadata=metadata_dict,
        )

        is_valid, errors = validate_deployment_config(config)
        if not is_valid:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            raise typer.Exit(1)

        # Save configuration
        try:
            await set_deployment_config(config)
            logger.info("Deployment configuration saved successfully!")
            logger.info(f"Organization ID: {org_id}")
            logger.info(f"Site ID: {site_id}")
            logger.info(f"Device ID: {device_id}")
            if metadata_dict:
                logger.info(f"Metadata: {metadata_dict}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise typer.Exit(1)

    asyncio.run(_set_config())


@config_app.command("show")
def config_show():
    """Show current deployment configuration."""

    async def _show_config():
        config = await get_current_deployment_config()
        if not config:
            logger.warning("No deployment configuration found.")
            logger.info("Run 'config set' to configure deployment settings.")
            return

        logger.info("Current deployment configuration:")
        logger.info(f"  Organization ID: {config.organization_id}")
        logger.info(f"  Site ID: {config.site_id}")
        logger.info(f"  Device ID: {config.device_id}")
        if config.config_metadata:
            logger.info(f"  Metadata: {config.config_metadata}")
        logger.info(f"  Created: {config.created_at}")
        logger.info(f"  Updated: {config.updated_at}")

    asyncio.run(_show_config())


@config_app.command("validate")
def config_validate():
    """Validate current deployment configuration."""

    async def _validate_config():
        is_valid, errors = await has_valid_deployment_config()
        if is_valid:
            logger.info("✓ Deployment configuration is valid and ready to use.")
        else:
            logger.error("✗ Deployment configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            raise typer.Exit(1)

    asyncio.run(_validate_config())


async def _configure_mqtt_interactive(
    org_id: str, site_id: str, device_id: str
) -> bool:
    """Configure MQTT interactively during setup.

    Args:
        org_id: Organization ID
        site_id: Site ID
        device_id: Device ID

    Returns:
        bool: True if configuration successful, False otherwise
    """
    logger.info("\n📡 MQTT Configuration")
    logger.info("Configure MQTT connection for device communication")

    # Ask if user wants to configure MQTT
    if not typer.confirm("Configure MQTT now?", default=True):
        logger.info("Skipping MQTT configuration")
        logger.info(
            "You can configure it later with: python -m src.cli mqtt config-emqx"
        )
        return False

    # Get broker choice
    broker_host = _get_broker_choice_interactive()

    # Auto-generate client ID from device identifiers
    mqtt_client_id = f"{org_id}-{site_id}-{device_id}"
    logger.info(f"Using auto-generated client ID: {mqtt_client_id}")

    # Configure based on broker type
    if broker_host == "localhost":
        # Configure local broker (no credentials needed)
        if not _configure_local_broker(client_id=mqtt_client_id):
            return False
    else:
        # Configure cloud broker (EMQX)
        mqtt_username, mqtt_password = _get_mqtt_credentials_interactive()
        if not _configure_emqx_with_broker(
            username=mqtt_username,
            password=mqtt_password,
            client_id=mqtt_client_id,
            topic_prefix="",
            broker_host=broker_host,
        ):
            return False

    # Test connection and report results
    return _test_and_report_connection()


@config_app.command("setup")
def config_setup(
    interactive: bool = typer.Option(
        False, "--interactive", help="Interactive setup wizard"
    ),
):
    """Setup deployment configuration with interactive prompts."""
    if not interactive:
        logger.info("Use --interactive flag for guided setup")
        return

    async def _interactive_setup():
        logger.info("🔧 BMS IoT Deployment Configuration Setup")
        logger.info("This wizard will help you configure your deployment settings.")
        logger.info("")

        # Get organization ID
        org_id = typer.prompt("Organization ID (should start with 'org_')")

        # Get site ID
        site_id = typer.prompt("Site ID (UUID format)")

        # Get device ID
        device_id = typer.prompt("IoT Device ID (UUID format)")

        # Configure MQTT
        mqtt_configured = await _configure_mqtt_interactive(org_id, site_id, device_id)

        logger.info("")  # Add spacing before continuing

        # Optional metadata
        add_metadata = typer.confirm("Add metadata? (optional)", default=False)
        metadata_dict = None
        if add_metadata:
            metadata_json = typer.prompt("Metadata (JSON format)", default="{}")
            try:
                import json

                metadata_dict = json.loads(metadata_json)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                raise typer.Exit(1)

        # Create and validate config
        config = DeploymentConfig(
            organization_id=org_id,
            site_id=site_id,
            device_id=device_id,
            config_metadata=metadata_dict,
        )

        is_valid, errors = validate_deployment_config(config)
        if not is_valid:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            raise typer.Exit(1)

        # Confirm and save
        logger.info("")
        logger.info("Configuration summary:")
        logger.info(f"  Organization ID: {org_id}")
        logger.info(f"  Site ID: {site_id}")
        logger.info(f"  Device ID: {device_id}")
        if metadata_dict:
            logger.info(f"  Metadata: {metadata_dict}")

        if typer.confirm("Save this configuration?"):
            try:
                await set_deployment_config(config)
                logger.info("✓ Configuration saved successfully!")
                if mqtt_configured:
                    logger.info(
                        f"✓ MQTT configured with client ID: {org_id}-{site_id}-{device_id}"
                    )
                else:
                    logger.info(
                        "ℹ️  MQTT not configured. Run 'python -m src.cli mqtt config-emqx' to configure"
                    )
                logger.info("You can now run 'run-main' to start the IoT application.")
            except Exception as e:
                logger.error(f"Failed to save configuration: {e}")
                raise typer.Exit(1)
        else:
            logger.info("Configuration not saved.")

    asyncio.run(_interactive_setup())


@app.command()
def run_main():
    """Run the main MQTT and BACnet monitor event loop (from main.py)."""
    asyncio.run(main_entrypoint())


if __name__ == "__main__":
    app()
