"""Configuration formatter utilities for clean CLI output."""

from typing import Optional, Dict, Union
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from rich.console import Group
from rich.text import Text

from src.models.deployment_config import DeploymentConfigModel
from src.network.mqtt_config import MQTTConfig


def format_deployment_config(config: DeploymentConfigModel) -> Table:
    """Format deployment configuration as a Rich table."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="cyan", width=20)
    table.add_column("Value", style="white")

    table.add_row("Organization ID", config.organization_id)
    table.add_row("Site ID", config.site_id)
    table.add_row("Device ID", config.device_id)
    if config.config_metadata:
        table.add_row("Metadata", str(config.config_metadata))
    table.add_row("Created", config.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    table.add_row("Updated", config.updated_at.strftime("%Y-%m-%d %H:%M:%S"))

    return table


def format_mqtt_config(mqtt_config: Dict[str, Union[str, int, bool, None]]) -> Table:
    """Format MQTT configuration as a Rich table."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="cyan", width=20)
    table.add_column("Value", style="white")

    # Just display what's in the config
    table.add_row(
        "Broker",
        f"{mqtt_config.get('broker_host', 'Not set')}:{mqtt_config.get('broker_port', 'N/A')}",
    )
    table.add_row("Client ID", str(mqtt_config.get("client_id", "Not set")))
    table.add_row("Username", str(mqtt_config.get("username", "Not set")))
    table.add_row(
        "TLS", "✓ Enabled" if mqtt_config.get("use_tls", False) else "✗ Disabled"
    )
    table.add_row("QoS", str(mqtt_config.get("qos", 1)))
    table.add_row("Clean Session", str(mqtt_config.get("clean_session", True)))
    table.add_row("Topic Prefix", mqtt_config.get("topic_prefix", "") or "None")

    return table


def format_mqtt_config_from_object(mqtt_config: MQTTConfig) -> Table:
    """Format MQTT configuration from MQTTConfig object.

    Args:
        mqtt_config: MQTTConfig object containing MQTT settings
    """
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="cyan", width=20)
    table.add_column("Value", style="white")

    # Determine broker type for display
    if mqtt_config.broker_host == "localhost":
        broker_display = f"localhost:{mqtt_config.broker_port} (Local)"
    elif "emqxsl.com" in mqtt_config.broker_host:
        broker_display = (
            f"{mqtt_config.broker_host}:{mqtt_config.broker_port} (EMQX Cloud)"
        )
    else:
        broker_display = f"{mqtt_config.broker_host}:{mqtt_config.broker_port} (Custom)"

    table.add_row("Broker", broker_display)
    table.add_row("Client ID", mqtt_config.client_id)
    table.add_row(
        "Username", mqtt_config.username if mqtt_config.username else "Not set"
    )
    table.add_row("TLS", "✓ Enabled" if mqtt_config.use_tls else "✗ Disabled")
    table.add_row("QoS", str(mqtt_config.qos))
    table.add_row("Clean Session", str(mqtt_config.clean_session))
    table.add_row(
        "Topic Prefix", mqtt_config.topic_prefix if mqtt_config.topic_prefix else "None"
    )

    return table


def format_combined_config(
    deployment_config: DeploymentConfigModel,
    mqtt_config: Dict[str, Union[str, int, bool, None]],
) -> Panel:
    """Format both deployment and MQTT config in a single panel."""
    # Create section headers
    deploy_header = Text("📋 Deployment Configuration", style="bold cyan")
    mqtt_header = Text("\n📡 MQTT Configuration", style="bold cyan")

    # Create tables
    deploy_table = format_deployment_config(deployment_config)
    mqtt_table = format_mqtt_config(mqtt_config)

    # Combine into a group
    content = Group(deploy_header, deploy_table, mqtt_header, mqtt_table)

    # Create panel
    panel = Panel(
        content,
        title="[bold]BMS IoT Configuration[/bold]",
        border_style="bright_blue",
        padding=(1, 2),
    )

    return panel


def print_config_summary(
    console: Console,
    deployment_config: DeploymentConfigModel,
    mqtt_config: Optional[Dict[str, Union[str, int, bool, None]]] = None,
) -> None:
    """Print formatted configuration summary to console.

    Args:
        console: Rich console instance
        deployment_config: Deployment configuration model from database
        mqtt_config: Optional MQTT configuration dictionary
    """
    if mqtt_config:
        panel = format_combined_config(deployment_config, mqtt_config)
    else:
        # Just show deployment config if no MQTT config
        panel = Panel(
            format_deployment_config(deployment_config),
            title="[bold]BMS IoT Deployment Configuration[/bold]",
            border_style="bright_blue",
            padding=(1, 2),
        )

    console.print()
    console.print(panel)
    console.print()
