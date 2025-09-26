import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from typing import TypedDict, cast
from pydantic import BaseModel
from enum import Enum

# Add more as your schema grows

class TopicConfig(BaseModel):
    topic: str
    qos: int = 1
    retain: bool = False

class CommandEntry(BaseModel):
    request: TopicConfig
    response: TopicConfig

class CommandSection(BaseModel):
    get_config: CommandEntry
    reboot: CommandEntry
    set_value_to_point: CommandEntry
    start_monitoring: CommandEntry
    stop_monitoring: CommandEntry
    # Add more commands as your schema grows

class StatusSection(BaseModel):
    heartbeat: TopicConfig

class DataSection(BaseModel):
    point: Optional[TopicConfig] = None
    point_bulk: Optional[TopicConfig] = None

class AlertManagementSection(BaseModel):
    acknowledge: TopicConfig
    resolve: TopicConfig

class Topics(BaseModel):
    command: CommandSection  # Always present
    status: StatusSection
    data: DataSection
    alert_management: AlertManagementSection

class CommandNameEnum(str, Enum):
    get_config = "get_config"
    reboot = "reboot"
    set_value_to_point = "set_value_to_point"
    start_monitoring = "start_monitoring"
    stop_monitoring = "stop_monitoring"
    # Add more commands as your schema grows

def load_mqtt_topics() -> Topics:
    mqtt_topics_path = Path(__file__).parent / 'topics.json'
    with open(mqtt_topics_path) as f:
        data = json.load(f)
    return Topics.model_validate(data)

def build_mqtt_topic_dict(
    organization_id: str,
    site_id: str,
    iot_device_id: str,
    controller_device_id: Optional[str] = None,
    iot_device_point_id: Optional[str] = None,
) -> Topics:
    """
    Build a full MQTT topic Topics model with placeholders replaced for the new topics.json schema, including controller_device_id and iot_device_point_id as optional.

    Args:
        organization_id (str): Organization identifier.
        site_id (str): Site identifier.
        iot_device_id (str): IoT device identifier.
        controller_device_id (Optional[str]): Controller device identifier.
        iot_device_point_id (Optional[str]): IoT device point identifier.

    Returns:
        Topics: A Topics Pydantic model with actual values filled in (or placeholders if not provided).
    """
    # Treat empty strings as None for optional fields
    if controller_device_id == "":
        controller_device_id = None
    if iot_device_point_id == "":
        iot_device_point_id = None
    # Validate that required values are not empty strings
    for name, value in {
        "organization_id": organization_id,
        "site_id": site_id,
        "iot_device_id": iot_device_id,
    }.items():
        if not value:
            raise ValueError(f"Missing placeholder value for {name}.")

    templates = load_mqtt_topics().model_dump()

    values = {
        "organization_id": organization_id,
        "site_id": site_id,
        "iot_device_id": iot_device_id,
    }
    if controller_device_id is not None:
        values["controller_device_id"] = controller_device_id
    if iot_device_point_id is not None:
        values["iot_device_point_id"] = iot_device_point_id

    def replace_placeholders(template_str: str) -> str:
        try:
            # Only replace placeholders for which we have values; leave others as is
            return template_str.format_map(Default(dict(values)))
        except KeyError as e:
            return template_str  # Leave the placeholder as is

    class Default(dict):
        def __missing__(self, key):
            return '{' + key + '}'

    def fill_templates(node: Any, parent_key: Optional[str] = None) -> Any:
        if isinstance(node, dict):
            result: dict[str, Any] = {}
            for key, value in node.items():
                # If we're in the 'data' section and the key is 'point', handle special logic
                if parent_key == 'data' and key == 'point':
                    if controller_device_id is None or iot_device_point_id is None:
                        result[key] = None
                    else:
                        result[key] = fill_templates(value, key)
                else:
                    result[key] = fill_templates(value, key)
            return result
        elif isinstance(node, str):
            return replace_placeholders(node)
        else:
            return node

    filled = fill_templates(templates)
    return Topics.model_validate(filled)

def build_mqtt_command_topic(
    organization_id: str,
    site_id: str,
    iot_device_id: str,
) -> CommandSection:
    """
    Build and return the CommandSection Pydantic model for the given device IDs.
    """
    topics = build_mqtt_topic_dict(
        organization_id=organization_id,
        site_id=site_id,
        iot_device_id=iot_device_id,
    )
    return topics.command


def build_mqtt_status_topic(
    organization_id: str,
    site_id: str,
    iot_device_id: str,
) -> StatusSection:
    """
    Build and return the StatusSection Pydantic model for the given device IDs.
    """
    topics = build_mqtt_topic_dict(
        organization_id=organization_id,
        site_id=site_id,
        iot_device_id=iot_device_id,
    )
    return topics.status


def build_mqtt_data_topic(
    organization_id: str,
    site_id: str,
    iot_device_id: str,
    controller_device_id: Optional[str] = None,
    iot_device_point_id: Optional[str] = None,
) -> DataSection:
    """
    Build and return the DataSection Pydantic model for the given device IDs.
    """
    topics = build_mqtt_topic_dict(
        organization_id=organization_id,
        site_id=site_id,
        iot_device_id=iot_device_id,
        controller_device_id=controller_device_id,
        iot_device_point_id=iot_device_point_id,
    )
    return topics.data


def build_mqtt_alert_management_topic(
    organization_id: str,
    site_id: str,
    iot_device_id: str,
) -> AlertManagementSection:
    """
    Build and return the AlertManagementSection Pydantic model for the given device IDs.
    """
    topics = build_mqtt_topic_dict(
        organization_id=organization_id,
        site_id=site_id,
        iot_device_id=iot_device_id,
    )
    return topics.alert_management
