from enum import Enum


class MonitoringStatusEnum(str, Enum):
    ACTIVE = "active"
    STOPPED = "stopped"
    ERROR = "error"
    INITIALIZING = "initializing"


class ConnectionStatusEnum(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
