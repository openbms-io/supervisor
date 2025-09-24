import BAC0
import json
from typing import Any, Optional, Union, Dict
import asyncio
from src.actors.messages.message_type import BacnetReaderConfig
from src.models.bacnet_types import (
    POINT_TYPES,
)
from src.utils.logger import logger
from src.utils.performance import performance_metrics


def convert_bacnet_health_value(prop_name: str, value: Any) -> Any:
    """
    Convert BACnet health properties to Python native types.
    Excludes presentValue which should remain as-is for string storage.

    Args:
        prop_name: Name of the property being converted
        value: Raw BACnet value to convert

    Returns:
        Converted Python native type for health properties, original value for others
    """
    if value is None:
        return None

    # Skip presentValue - keep as-is for string storage
    if prop_name == "presentValue":
        return value

    if hasattr(value, "__class__"):
        class_name = value.__class__.__name__

        # Convert health-related BACnet types only
        if prop_name == "eventState" and "EventState" in class_name:
            return str(value)  # "fault" from <EventState: fault>
        elif prop_name == "reliability" and "Reliability" in class_name:
            return str(
                value
            )  # "no-fault-detected" from <Reliability: no-fault-detected>
        elif prop_name == "outOfService":
            # Handle integer to boolean conversion
            if isinstance(value, int):
                return bool(value)
            elif "Boolean" in class_name:
                return bool(value)
        elif prop_name == "statusFlags":
            return value  # Keep StatusFlags object for special processing

    # Handle integer to boolean for outOfService
    if prop_name == "outOfService" and isinstance(value, int) and value in [0, 1]:
        return bool(value)

    return value


class BACnetWrapper:
    """Single BAC0 instance wrapper for a specific BACnet reader configuration."""

    def __init__(self, reader_config: BacnetReaderConfig) -> None:
        self.reader_config = reader_config
        self.ip = reader_config.ip_address
        self.subnet_mask = reader_config.subnet_mask
        self.device_id = reader_config.bacnet_device_id
        self.port = reader_config.port
        self.bbmd_enabled = reader_config.bbmd_enabled
        self.bbmd_server_ip = reader_config.bbmd_server_ip

        # BAC0 instance and connection state
        self._bacnet: Optional[BAC0.lite] = None
        self._bacnet_connected = False
        self._lock: Optional[asyncio.Lock] = None

        # Reader availability tracking
        self._active_operations = 0

        logger.info(f"[{self.instance_id}] Initialized BACnetWrapper")

    @property
    def instance_id(self) -> str:
        """Get instance identifier for logger."""
        return f"{self.reader_config.id}({self.ip}:{self.port})"

    async def is_busy(self) -> bool:
        """Check if the wrapper is currently busy with operations."""
        lock = await self.get_lock()
        async with lock:
            return self._active_operations > 0

    async def get_active_operations_count(self) -> int:
        """Get the current number of active operations."""
        lock = await self.get_lock()
        async with lock:
            return self._active_operations

    async def get_lock(self) -> asyncio.Lock:
        """Get or create the asyncio lock for thread-safe operations."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def start(self) -> None:
        """Initialize BAC0 connection when event loop is running."""
        if not self._bacnet_connected:
            try:
                connect_params = {
                    "ip": self.ip,
                    "deviceId": self.device_id,
                    "port": self.port,
                    "ping": True,
                }

                # Add BBMD configuration if enabled
                if self.bbmd_enabled and self.bbmd_server_ip:
                    connect_params["bbmdAddress"] = self.bbmd_server_ip
                    logger.info(
                        f"[{self.instance_id}] Connecting with BBMD server: {self.bbmd_server_ip}"
                    )

                logger.info(
                    f"[{self.instance_id}] Connecting to BAC0 with params: {connect_params}"
                )
                self._bacnet = BAC0.connect(**connect_params)
                self._bacnet_connected = True
                logger.info(f"[{self.instance_id}] BAC0 connection established")
            except Exception as e:
                logger.error(f"[{self.instance_id}] Failed to connect BAC0: {e}")
                raise

    async def read(self, command: str) -> Any:
        """Thread-safe read operation."""
        if not self._bacnet_connected:
            await self.start()

        if self._bacnet is None:
            raise RuntimeError("BACnet connection not established")

        lock = await self.get_lock()
        async with lock:
            self._active_operations += 1
            try:
                logger.info(
                    f"[{self.instance_id}] Read command: {command} (active ops: {self._active_operations})"
                )
                return await self._bacnet.read(command)
            finally:
                self._active_operations -= 1

    @performance_metrics("bacnet_read_multiple")
    async def read_multiple(self, command: str) -> Any:
        """Thread-safe read multiple operation."""
        if not self._bacnet_connected:
            await self.start()

        if self._bacnet is None:
            raise RuntimeError("BACnet connection not established")

        lock = await self.get_lock()
        async with lock:
            self._active_operations += 1
            try:
                logger.debug(
                    f"[{self.instance_id}] Read multiple command: {command} (active ops: {self._active_operations})"
                )
                output = await self._bacnet.readMultiple(
                    args=command, show_property_name=True
                )
                logger.info(f"[{self.instance_id}] Read multiple output: {output}")
                return output
            finally:
                self._active_operations -= 1

    async def read_present_value(
        self, device_ip: str, object_type: str, object_id: int
    ) -> Any:
        """Thread-safe read present value operation."""
        read_command = f"{device_ip} {object_type} {object_id} presentValue"
        return await self.read(read_command)

    async def read_all_properties(
        self, device_ip: str, object_type: str, object_id: int
    ) -> Any:
        """Thread-safe read all properties operation."""
        read_command = f"{device_ip} {object_type} {object_id} all"
        return await self.read_multiple(read_command)

    @performance_metrics(
        "bacnet_read_properties", {"device": "device_ip", "count": "properties"}
    )
    async def read_properties(
        self, device_ip: str, object_type: str, object_id: int, properties: list
    ) -> Any:
        """
        Thread-safe read specific properties operation.

        Args:
            device_ip: IP address of the BACnet device
            object_type: BACnet object type (e.g., 'analogInput', 'analogOutput')
            object_id: Object instance ID
            properties: List of property names to read

        Returns:
            Dictionary containing the requested properties mapped to their values

        Example:
            properties = ['presentValue', 'statusFlags', 'eventState', 'outOfService', 'reliability']
            result = await bacnet_wrapper.read_properties("192.168.1.100", "analogInput", 1, properties)
            # Returns: {'presentValue': 72.5, 'statusFlags': [0,1,0,0], 'eventState': 'normal', ...}
        """
        if not self._bacnet_connected:
            await self.start()

        if self._bacnet is None:
            raise RuntimeError("BACnet connection not established")

        lock = await self.get_lock()
        async with lock:
            self._active_operations += 1
            try:
                # Build command for multiple properties
                # Format: "device_ip object_type object_id property1 property2 property3"
                properties_str = " ".join(properties)
                read_command = f"{device_ip} {object_type} {object_id} {properties_str}"

                logger.info(
                    f"[{self.instance_id}] Reading properties: {read_command} (active ops: {self._active_operations})"
                )

                _rpm = {
                    "address": device_ip,  # Replace with device address
                    "objects": {f"{object_type}:{object_id}": properties},
                }

                # _rpm = {
                #     'address': '192.168.2.100:47808',  # Replace with device address
                #     'objects': {
                #         'analogInput:1094': ['objectName', 'presentValue', 'statusFlags', 'units', 'description'],
                #         'analogValue:4410': ['objectName', 'presentValue', 'statusFlags', 'units', 'description']
                #     }
                # }

                try:
                    logger.info(f"READ COMMAND >>>> {read_command}")
                    result = await self._bacnet.readMultiple(
                        args=read_command, show_property_name=True
                    )
                except IndexError as index_error:
                    logger.error(
                        f"[{self.instance_id}] BAC0 readMultiple IndexError - likely BAC0 library bug or malformed BACnet response: {index_error}"
                    )
                    logger.error(
                        f"[{self.instance_id}] Problematic command: {read_command}"
                    )
                    logger.error(
                        f"[{self.instance_id}] Device: {device_ip}, Object: {object_type}:{object_id}, Properties: {properties}"
                    )
                    raise Exception(
                        f"BAC0 readMultiple IndexError - likely BAC0 library bug or malformed BACnet response: {index_error}"
                    )
                except Exception as read_exception:
                    logger.error(
                        f"[{self.instance_id}] readMultiple call failed: {type(read_exception).__name__}: {read_exception}"
                    )
                    raise

                # Log result structure for debugging if needed
                logger.debug(
                    f"[{self.instance_id}] readMultiple result type: {type(result)}, length: {len(result) if isinstance(result, list) else 'N/A'}"
                )

                logger.info(f"RESULT >>>> {result}")
                # Convert list result to dictionary mapping property names to values
                property_dict: Dict[str, Any] = {}
                if isinstance(result, list):
                    # Validate that we have a reasonable result structure
                    if len(result) == 0:
                        logger.warning(
                            f"[{self.instance_id}] readMultiple returned empty list for properties {properties}"
                        )
                        # Set all properties to None
                        for prop_name in properties:
                            property_dict[prop_name] = None
                    else:
                        # Map each property name to its corresponding value in the result list
                        for i, prop_name in enumerate(properties):
                            if i < len(result):
                                property_dict[prop_name] = result[i]
                                logger.debug(f"[{self.instance_id}] Mapped {prop_name}")
                            else:
                                logger.warning(
                                    f"[{self.instance_id}] Property {prop_name} not found in result (index {i} >= {len(result)}), setting to None"
                                )
                                property_dict[prop_name] = None
                else:
                    # If result is not a list, log the unexpected format
                    logger.warning(
                        f"[{self.instance_id}] Unexpected result format from readMultiple: {type(result)}"
                    )
                    logger.warning(
                        f"[{self.instance_id}] Non-list result content: {result}"
                    )
                    # Try to handle single value responses
                    if len(properties) == 1:
                        logger.info(
                            f"[{self.instance_id}] Single property request, using result as-is"
                        )
                        property_dict[properties[0]] = result
                    else:
                        logger.error(
                            f"[{self.instance_id}] Cannot map non-list result to multiple properties"
                        )
                        return result

                # Extract actual values from BACnet objects and handle ErrorType objects
                extracted_dict: Dict[str, Any] = {}
                for prop_name, raw_value in property_dict.items():
                    try:
                        # Log property extraction for debugging
                        logger.info(
                            f"[{self.instance_id}] Extracting property {prop_name}: type={type(raw_value)}"
                        )

                        if isinstance(raw_value, tuple):
                            logger.info(
                                f"[{self.instance_id}] Property {prop_name} is tuple with length {len(raw_value)}"
                            )
                            if len(raw_value) >= 1:
                                actual_value = raw_value[0]
                                logger.debug(
                                    f"[{self.instance_id}] Property {prop_name} tuple[0]: type={type(actual_value)}, value={actual_value}"
                                )

                                # Handle ErrorType objects (property doesn't exist or can't be read)
                                if hasattr(
                                    actual_value, "__class__"
                                ) and "ErrorType" in str(actual_value.__class__):
                                    error_class = getattr(
                                        actual_value, "errorClass", "unknown"
                                    )
                                    error_code = getattr(
                                        actual_value, "errorCode", "unknown"
                                    )
                                    logger.warning(
                                        f"[{self.instance_id}] Property {prop_name} returned ErrorType: {actual_value},  ({type(actual_value).__name__}), setting to None. errorClass:{error_class}, errorCode: {error_code}"
                                    )
                                    error_info = {
                                        "error_class": error_class,
                                        "error_code": error_code,
                                    }
                                    # JSON serializable error object
                                    json_error_info = json.dumps(error_info)
                                    extracted_dict["error_info"] = json_error_info
                                else:
                                    # Apply selective conversion for health properties only
                                    if prop_name in [
                                        "statusFlags",
                                        "eventState",
                                        "outOfService",
                                        "reliability",
                                    ]:
                                        converted_value = convert_bacnet_health_value(
                                            prop_name, actual_value
                                        )
                                        logger.debug(
                                            f"[{self.instance_id}] Property {prop_name} converted: {actual_value} -> {converted_value}"
                                        )
                                        extracted_dict[prop_name] = converted_value
                                    else:
                                        extracted_dict[prop_name] = (
                                            actual_value  # Keep presentValue as-is
                                        )
                            else:
                                logger.warning(
                                    f"[{self.instance_id}] Property {prop_name} is empty tuple, setting to None"
                                )
                                extracted_dict[prop_name] = None
                        elif isinstance(raw_value, list):
                            logger.debug(
                                f"[{self.instance_id}] Property {prop_name} is list with length {len(raw_value)}"
                            )
                            if len(raw_value) >= 1:
                                actual_value = raw_value[0]
                                logger.debug(
                                    f"[{self.instance_id}] Property {prop_name} list[0]: type={type(actual_value)}, value={actual_value}"
                                )
                                # Handle as if it were tuple[0]
                                if prop_name in [
                                    "statusFlags",
                                    "eventState",
                                    "outOfService",
                                    "reliability",
                                ]:
                                    extracted_dict[prop_name] = (
                                        convert_bacnet_health_value(
                                            prop_name, actual_value
                                        )
                                    )
                                else:
                                    extracted_dict[prop_name] = actual_value
                            else:
                                logger.warning(
                                    f"[{self.instance_id}] Property {prop_name} is empty list, setting to None"
                                )
                                extracted_dict[prop_name] = None
                        else:
                            # If not a tuple or list, use the value as-is or convert if health property
                            logger.debug(
                                f"[{self.instance_id}] Property {prop_name} is neither tuple nor list, using as-is"
                            )
                            if prop_name in [
                                "statusFlags",
                                "eventState",
                                "outOfService",
                                "reliability",
                            ]:
                                extracted_dict[prop_name] = convert_bacnet_health_value(
                                    prop_name, raw_value
                                )
                            else:
                                extracted_dict[prop_name] = raw_value
                    except Exception as e:
                        logger.error(
                            f"[{self.instance_id}] Failed to extract value for property {prop_name} (raw_value={raw_value}): {e}"
                        )
                        logger.error(
                            f"[{self.instance_id}] Exception type: {type(e).__name__}, details: {str(e)}"
                        )
                        extracted_dict[prop_name] = None

                logger.info(
                    f"[{self.instance_id}] Extracted properties: {extracted_dict}"
                )
                return extracted_dict

            except Exception as e:
                logger.error(
                    f"[{self.instance_id}] Failed to read properties {properties} from {device_ip} {object_type} {object_id}: {e}"
                )
                raise
            finally:
                self._active_operations -= 1

    @performance_metrics(
        "bacnet_bulk_read", {"device": "device_ip", "count": "point_requests"}
    )
    async def read_multiple_points(self, device_ip: str, point_requests: list) -> dict:
        """
        Read multiple points in a single BAC0 ReadPropertyMultiple query.

        Args:
            device_ip: IP address of the BACnet device
            point_requests: List of dicts with keys: 'object_type', 'object_id', 'properties'
                           e.g., [{'object_type': 'analogInput', 'object_id': 1, 'properties': ['presentValue', 'statusFlags']}, ...]

        Returns:
            Dict mapping "object_type:object_id" to property dictionaries
            e.g., {'analogInput:1': {'presentValue': 72.5, 'statusFlags': 'normal'}, ...}
        """
        if not self._bacnet_connected:
            await self.start()

        if self._bacnet is None:
            raise RuntimeError("BACnet connection not established")

        if not point_requests:
            return {}

        lock = await self.get_lock()
        async with lock:
            self._active_operations += 1
            try:
                # Build ReadPropertyMultiple request for all points
                _rpm: Dict[str, Any] = {"address": device_ip, "objects": {}}

                # Add each point to the request
                for req in point_requests:
                    object_key = f"{req['object_type']}:{req['object_id']}"
                    _rpm["objects"][object_key] = req["properties"]

                logger.info(
                    f"[{self.instance_id}] Reading {len(point_requests)} points in single query from {device_ip}: {list(_rpm['objects'].keys())}"
                )
                logger.info(
                    f"[{self.instance_id}] BAC0 readMultiple input _rpm: {_rpm}"
                )

                # Execute the bulk read
                # BAC0 readMultiple requires both args and request_dict parameters
                # Use device_ip for args parameter (same format as working individual reads)
                result = await self._bacnet.readMultiple(
                    args=device_ip, request_dict=_rpm, show_property_name=True
                )

                # Comprehensive debug logging for the response
                logger.info(
                    f"[{self.instance_id}] BAC0 readMultiple raw output type: {type(result)}"
                )
                logger.info(
                    f"[{self.instance_id}] BAC0 readMultiple raw output length: {len(result) if hasattr(result, '__len__') else 'N/A'}"
                )
                logger.info(
                    f"[{self.instance_id}] BAC0 readMultiple raw output content: {result}"
                )

                # Try to understand the structure better
                if isinstance(result, dict):
                    logger.info(
                        f"[{self.instance_id}] Result is dict with keys: {list(result.keys())}"
                    )
                    for key, value in result.items():
                        logger.info(
                            f"[{self.instance_id}] Dict key '{key}' -> type: {type(value)}, value: {value}"
                        )
                elif isinstance(result, list):
                    logger.info(
                        f"[{self.instance_id}] Result is list with {len(result)} items"
                    )
                    for i, item in enumerate(result):
                        logger.info(
                            f"[{self.instance_id}] List item [{i}] -> type: {type(item)}, value: {item}"
                        )
                else:
                    logger.info(
                        f"[{self.instance_id}] Result is neither dict nor list: {repr(result)}"
                    )

                # Parse results back to expected format
                return self._parse_bulk_read_result(result, point_requests)

            except Exception as e:
                logger.error(
                    f"[{self.instance_id}] Bulk read failed for {len(point_requests)} points on {device_ip}: {e}"
                )
                raise
            finally:
                self._active_operations -= 1

    def _parse_bulk_read_result(self, result: Any, point_requests: list) -> dict:
        """
        Parse the BAC0 readMultiple result into the expected format.

        Args:
            result: Raw result from BAC0 readMultiple
            point_requests: Original point requests for reference

        Returns:
            Dict mapping "object_type:object_id" to property dictionaries
        """
        logger.info(f"[{self.instance_id}] Starting _parse_bulk_read_result")
        logger.info(f"[{self.instance_id}] Parse input result type: {type(result)}")
        logger.info(
            f"[{self.instance_id}] Parse input point_requests: {point_requests}"
        )

        parsed_results = {}

        try:
            logger.info(f"[{self.instance_id}] Entering parse logic")

            # Handle different result formats from BAC0
            if isinstance(result, dict):
                logger.info(f"[{self.instance_id}] Handling dict result format")
                logger.info(f"[{self.instance_id}] Dict keys: {list(result.keys())}")

                # Parse BAC0 bulk read result using existing object mapping
                parsed_results = self._parse_bac0_bulk_result(result, point_requests)

            elif isinstance(result, list):
                logger.info(
                    f"[{self.instance_id}] Handling list result format with {len(result)} items"
                )

                # If result is a list, try to map back to objects
                # This is more complex and depends on BAC0's actual response format
                logger.warning(
                    f"[{self.instance_id}] Got list result from bulk read, may need manual parsing"
                )

                # For now, create empty results for each requested point
                for req in point_requests:
                    object_key = f"{req['object_type']}:{req['object_id']}"
                    logger.info(
                        f"[{self.instance_id}] Creating empty result for {object_key}"
                    )
                    parsed_results[object_key] = {}

            else:
                logger.error(
                    f"[{self.instance_id}] Unexpected result type from bulk read: {type(result)}"
                )
                # Create empty results as fallback
                for req in point_requests:
                    object_key = f"{req['object_type']}:{req['object_id']}"
                    logger.info(
                        f"[{self.instance_id}] Creating fallback empty result for {object_key}"
                    )
                    parsed_results[object_key] = {}

        except Exception as e:
            logger.error(
                f"[{self.instance_id}] Exception in _parse_bulk_read_result: {e}"
            )
            logger.error(f"[{self.instance_id}] Exception type: {type(e)}")
            import traceback

            logger.error(
                f"[{self.instance_id}] Exception traceback: {traceback.format_exc()}"
            )

            # Create empty results as fallback
            for req in point_requests:
                object_key = f"{req['object_type']}:{req['object_id']}"
                parsed_results[object_key] = {}

        logger.info(
            f"[{self.instance_id}] Final parsed bulk read results: {parsed_results}"
        )
        return parsed_results

    def _parse_bac0_bulk_result(self, result: dict, point_requests: list) -> dict:
        """
        Parse BAC0 bulk read result using existing object type mapping.

        Args:
            result: BAC0 readMultiple result dict
            point_requests: Original point requests for reference

        Returns:
            Dict mapping "object_type:object_id" to property dictionaries
        """
        parsed_results = {}

        # Create reverse mapping from POINT_TYPES: BacnetObjectTypeEnum.value -> bacpypes key
        # POINT_TYPES: {'analog-value': BacnetObjectTypeEnum.ANALOG_VALUE, ...}
        # BacnetObjectTypeEnum.ANALOG_VALUE.value = 'analogValue'
        bac0_to_enum_mapping = {}
        for bacpypes_key, enum_value in POINT_TYPES.items():
            # bacpypes_key: 'analog-value', enum_value.value: 'analogValue'
            bac0_to_enum_mapping[bacpypes_key] = enum_value.value

        logger.info(
            f"[{self.instance_id}] Using existing object mapping: {bac0_to_enum_mapping}"
        )

        # Create mapping from BAC0 result keys to our expected keys
        bac0_key_mapping: Dict[str, str] = {}
        for bac0_key in result.keys():
            # Parse BAC0 key format: 'analog-value,10' -> ('analog-value', '10')
            if "," in bac0_key:
                obj_type_bac0, obj_id_str = bac0_key.split(",", 1)
                obj_id = int(obj_id_str)

                # Use existing mapping to convert BAC0 object type to our format
                if obj_type_bac0 in bac0_to_enum_mapping:
                    our_obj_type = bac0_to_enum_mapping[obj_type_bac0]
                    our_key = f"{our_obj_type}:{obj_id}"
                    bac0_key_mapping[our_key] = bac0_key
                    logger.info(
                        f"[{self.instance_id}] Key mapping: {our_key} -> {bac0_key}"
                    )
                else:
                    logger.warning(
                        f"[{self.instance_id}] Unknown object type in BAC0 result: {obj_type_bac0}"
                    )

        # Process each requested point using the mapping
        for req in point_requests:
            object_key = f"{req['object_type']}:{req['object_id']}"
            logger.info(f"[{self.instance_id}] Looking for object_key: {object_key}")

            if object_key in bac0_key_mapping:
                bac0_key = bac0_key_mapping[object_key]
                raw_properties = result[bac0_key]
                logger.info(
                    f"[{self.instance_id}] Found {object_key} as {bac0_key}: {raw_properties}"
                )

                # Convert BAC0 property format to our expected format
                converted_properties = self._convert_bac0_properties(raw_properties)
                parsed_results[object_key] = converted_properties
                logger.info(
                    f"[{self.instance_id}] Converted properties for {object_key}: {converted_properties}"
                )
            else:
                logger.warning(
                    f"[{self.instance_id}] Missing {object_key} in result, setting empty"
                )
                parsed_results[object_key] = {}

        return parsed_results

    def _convert_bac0_properties(self, raw_properties: list) -> dict:
        """
        Convert BAC0 property format to our expected format.

        BAC0 returns: [(<PropertyIdentifier: present-value>, (25.0, <PropertyIdentifier: present-value>)), ...]
        We need: {'presentValue': 25.0, 'statusFlags': 'in-alarm;fault;overridden;out-of-service', ...}
        """
        converted = {}

        try:
            for prop_tuple in raw_properties:
                if len(prop_tuple) >= 2:
                    prop_identifier, prop_value_tuple = prop_tuple

                    # Extract property name from PropertyIdentifier using built-in attr method
                    prop_name_raw = prop_identifier.attr

                    # Convert property name to camelCase
                    prop_name_mapping = {
                        "present-value": "presentValue",
                        "status-flags": "statusFlags",
                        "event-state": "eventState",
                        "out-of-service": "outOfService",
                        "reliability": "reliability",
                    }

                    prop_name = prop_name_mapping.get(prop_name_raw, prop_name_raw)

                    # Extract actual value (first element of the tuple)
                    if (
                        isinstance(prop_value_tuple, tuple)
                        and len(prop_value_tuple) >= 1
                    ):
                        actual_value = prop_value_tuple[0]

                        # Apply health value conversion (same as individual reads)
                        converted_value = convert_bacnet_health_value(
                            prop_name, actual_value
                        )
                        converted[prop_name] = converted_value

                        logger.debug(
                            f"[{self.instance_id}] Converted property {prop_name_raw} -> {prop_name}: {actual_value} -> {converted_value}"
                        )
                    else:
                        logger.warning(
                            f"[{self.instance_id}] Unexpected property value format for {prop_name_raw}: {prop_value_tuple}"
                        )
                        converted[prop_name] = None

        except Exception as e:
            logger.error(f"[{self.instance_id}] Error converting BAC0 properties: {e}")
            logger.error(f"[{self.instance_id}] Raw properties: {raw_properties}")

        return converted

    async def who_is(self, address: str) -> Any:
        """Thread-safe who_is operation."""
        if not self._bacnet_connected:
            await self.start()

        if self._bacnet is None:
            raise RuntimeError("BACnet connection not established")

        lock = await self.get_lock()
        async with lock:
            self._active_operations += 1
            try:
                logger.debug(
                    f"[{self.instance_id}] Who is query: {address} (active ops: {self._active_operations})"
                )
                return await self._bacnet.who_is(address)
            finally:
                self._active_operations -= 1

    async def read_object_list(self, ip: str, device_id: int) -> Any:
        """Thread-safe read object list operation."""
        if self._bacnet is None:
            raise RuntimeError(f"[{self.instance_id}] BAC0 instance not initialized")
        return await self._bacnet.read(
            args=f"{ip} device {device_id} objectList", show_property_name=True
        )

    async def write_with_priority(
        self,
        ip: str,
        objectType: str,
        point_id: int,
        present_value: Union[int, float],
        priority: int = 8,
    ) -> Union[int, float]:
        """Thread-safe write operation with priority."""
        # f"{target_controller.controller_ip_address} {target_object.properties.get('objectType')} {target_object.point_id} presentValue {value_to_write} - 8"
        response = await self.write(
            f"{ip} {objectType} {point_id} presentValue {present_value} - {priority}"
        )
        logger.info(f"[{self.instance_id}] Write response: {response}")
        read_value_after_write = await self.read_present_value(
            device_ip=ip, object_type=objectType, object_id=point_id
        )

        logger.info(
            f"[{self.instance_id}] Read value after write: {read_value_after_write}"
        )

        if read_value_after_write != present_value:
            logger.error(
                f"[{self.instance_id}] Write failed: {read_value_after_write} != {present_value}"
            )
            raise Exception(
                f"Write failed: {read_value_after_write} != {present_value}"
            )

        return read_value_after_write

    async def write(self, command: str) -> Any:
        """Thread-safe write operation."""
        if not self._bacnet_connected:
            await self.start()

        if self._bacnet is None:
            raise RuntimeError("BACnet connection not established")

        lock = await self.get_lock()
        async with lock:
            self._active_operations += 1
            try:
                logger.info(
                    f"[{self.instance_id}] Write command: {command} (active ops: {self._active_operations})"
                )
                response = await self._bacnet._write(command)
                logger.info(f"[{self.instance_id}] Write response: {response}")
                return response
            finally:
                self._active_operations -= 1

    async def is_connected(self) -> bool:
        """Thread-safe connection status check."""
        lock = await self.get_lock()
        async with lock:
            return self._bacnet_connected

    async def disconnect(self) -> bool:
        """Thread-safe disconnect operation."""
        logger.info(f"[{self.instance_id}] Disconnecting BAC0")
        lock = await self.get_lock()
        async with lock:
            if self._bacnet_connected and self._bacnet:
                try:
                    await self._bacnet._disconnect()
                    logger.info(
                        f"[{self.instance_id}] Sleeping for 5 seconds to allow BAC0 to disconnect..."
                    )
                    await asyncio.sleep(5.0)
                    self._bacnet_connected = False
                    self._bacnet = None
                    logger.info(f"[{self.instance_id}] Disconnected BAC0")
                    return True
                except Exception as e:
                    logger.error(f"[{self.instance_id}] Failed to disconnect BAC0: {e}")
                    return False
            return False  # Already disconnected
