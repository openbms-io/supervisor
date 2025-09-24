from pydantic import BaseModel
from enum import Enum
from typing import Union, Optional
from src.models.controller_points import ControllerPointsModel
from packages.mqtt_topics.topics_loader import CommandNameEnum
from src.models.device_status_enums import MonitoringStatusEnum, ConnectionStatusEnum


class ConfigUploadResponsePayload(BaseModel):
    success: bool


class BacnetReaderConfig(BaseModel):
    id: str
    ip_address: str
    subnet_mask: int
    bacnet_device_id: int
    port: int
    bbmd_enabled: bool
    bbmd_server_ip: Optional[str] = None
    is_active: bool


class ConfigUploadPayload(BaseModel):
    urlToUploadConfig: str
    jwtToken: str
    iotDeviceControllers: list[dict]
    bacnetReaders: Optional[list[BacnetReaderConfig]] = []
    # devicePointIPAddresses: list[str]


class PointPublishPayload(BaseModel):
    points: list[ControllerPointsModel]


class DeviceRebootPayload(BaseModel):
    iot_device_id: str


class PointValuePayload(BaseModel):
    ip: str
    object_type: str
    object_id: int
    value: float


class SetValueToPointRequestPayload(BaseModel):
    iotDevicePointId: str
    pointInstanceId: str
    controllerId: str
    presentValue: Union[float, int]
    stateText: Optional[list[str]] = None
    commandId: str
    commandType: CommandNameEnum


class SetValueToPointResponsePayload(BaseModel):
    success: bool
    message: str
    commandId: str


class ImmediateUploadTriggerPayload(BaseModel):
    reason: str = "manual_write"  # Reason for immediate upload


class MonitoringControlPayload(BaseModel):
    commandId: str
    commandType: CommandNameEnum
    presentValue: Union[float, int]


class MonitoringControlResponsePayload(BaseModel):
    success: bool
    message: str
    commandId: str


class ForceHeartbeatPayload(BaseModel):
    reason: str = (
        "status_change"  # Reason for force heartbeat (monitoring_change, connection_change, etc.)
    )


class HeartbeatStatusPayload(BaseModel):
    # System metrics
    cpu_usage_percent: Optional[float] = None
    memory_usage_percent: Optional[float] = None
    disk_usage_percent: Optional[float] = None
    temperature_celsius: Optional[float] = None
    uptime_seconds: Optional[int] = None
    load_average: Optional[float] = None

    # BMS-specific metrics
    monitoring_status: Optional[MonitoringStatusEnum] = None
    mqtt_connection_status: Optional[ConnectionStatusEnum] = None
    bacnet_connection_status: Optional[ConnectionStatusEnum] = None
    bacnet_devices_connected: Optional[int] = None
    bacnet_points_monitored: Optional[int] = None


class ActorName(str, Enum):
    MQTT = "MQTT"
    BACNET = "BACNET"
    BACNET_WRITER = "BACNET_WRITER"
    UPLOADER = "UPLOADER"
    BROADCAST = "BROADCAST"  # For sending messages to all actors.
    CLEANER = "CLEANER"  # Added for cleaner_actor
    HEARTBEAT = "HEARTBEAT"  # Added for heartbeat_actor
    SYSTEM_METRICS = "SYSTEM_METRICS"  # Added for system_metrics_actor


class ActorMessageType(str, Enum):
    CONFIG_UPLOAD_REQUEST = "CONFIG_UPLOAD_REQUEST"
    CONFIG_UPLOAD_RESPONSE = "CONFIG_UPLOAD_RESPONSE"
    DEVICE_REBOOT = "DEVICE_REBOOT"
    POINT_PUBLISH_REQUEST = "POINT_PUBLISH_REQUEST"
    POINT_PUBLISH_RESPONSE = "POINT_PUBLISH_RESPONSE"
    DELETE_UPLOADED_POINTS = "DELETE_UPLOADED_POINTS"  # Added for delete_actor
    SET_VALUE_TO_POINT_REQUEST = "SET_VALUE_TO_POINT_REQUEST"
    SET_VALUE_TO_POINT_RESPONSE = "SET_VALUE_TO_POINT_RESPONSE"
    IMMEDIATE_UPLOAD_TRIGGER = "IMMEDIATE_UPLOAD_TRIGGER"
    HEARTBEAT_STATUS = "HEARTBEAT_STATUS"  # Added for heartbeat status
    START_MONITORING_REQUEST = "START_MONITORING_REQUEST"
    STOP_MONITORING_REQUEST = "STOP_MONITORING_REQUEST"
    START_MONITORING_RESPONSE = "START_MONITORING_RESPONSE"
    STOP_MONITORING_RESPONSE = "STOP_MONITORING_RESPONSE"
    FORCE_HEARTBEAT_REQUEST = "FORCE_HEARTBEAT_REQUEST"


AllowedPayloadTypes = Union[
    ConfigUploadPayload,
    DeviceRebootPayload,
    PointPublishPayload,
    ConfigUploadResponsePayload,
    SetValueToPointRequestPayload,
    SetValueToPointResponsePayload,
    ImmediateUploadTriggerPayload,
    HeartbeatStatusPayload,
    MonitoringControlPayload,
    MonitoringControlResponsePayload,
    ForceHeartbeatPayload,
]


class ActorMessage(BaseModel):
    sender: ActorName
    receiver: ActorName
    message_type: ActorMessageType
    payload: Optional[AllowedPayloadTypes]
