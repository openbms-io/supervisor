"""Shared BACnet types and enums."""

from enum import Enum
from typing import Optional, List


class BacnetObjectTypeEnum(str, Enum):
    ANALOG_INPUT = "analogInput"
    ANALOG_OUTPUT = "analogOutput"
    ANALOG_VALUE = "analogValue"
    BINARY_INPUT = "binaryInput"
    BINARY_OUTPUT = "binaryOutput"
    BINARY_VALUE = "binaryValue"
    MULTI_STATE_INPUT = "multiStateInput"
    MULTI_STATE_OUTPUT = "multiStateOutput"
    MULTI_STATE_VALUE = "multiStateValue"


# The pointtypes are for the bacpypes object types.
POINT_TYPES = {
    "analog-input": BacnetObjectTypeEnum.ANALOG_INPUT,
    "analog-output": BacnetObjectTypeEnum.ANALOG_OUTPUT,
    "analog-value": BacnetObjectTypeEnum.ANALOG_VALUE,
    "binary-input": BacnetObjectTypeEnum.BINARY_INPUT,
    "binary-output": BacnetObjectTypeEnum.BINARY_OUTPUT,
    "binary-value": BacnetObjectTypeEnum.BINARY_VALUE,
    "multi-state-input": BacnetObjectTypeEnum.MULTI_STATE_INPUT,
    "multi-state-output": BacnetObjectTypeEnum.MULTI_STATE_OUTPUT,
    "multi-state-value": BacnetObjectTypeEnum.MULTI_STATE_VALUE,
}


def get_point_types() -> List[str]:
    return list(POINT_TYPES.keys())


def convert_point_type_to_bacnet_object_type(
    point_type: str,
) -> Optional[BacnetObjectTypeEnum]:
    return POINT_TYPES.get(point_type)
