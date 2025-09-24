"""BACnet monitoring module using bacpypes."""

import json
import uuid
from typing import Dict, List, Optional, Any
from src.config.config import DEFAULT_CONTROLLER_PORT
from src.models.bacnet_types import (
    convert_point_type_to_bacnet_object_type,
    get_point_types,
)
from src.utils.utils import extract_property_dict_camel

# import BAC0
from src.models.bacnet_wrapper_manager import (
    bacnet_wrapper_manager,
)
from src.actors.messages.message_type import BacnetReaderConfig

# from src.simulator.bacnet_simulator_config import READ_CONFIG
from src.models.bacnet_config import BacnetDeviceInfo, insert_bacnet_config_json
from src.models.bacnet_config import get_latest_bacnet_config_json_as_list
from src.models.controller_points import (
    ControllerPointsModel,
    insert_controller_point,
    bulk_insert_controller_points,
)
from src.utils.bacnet_health_processor import BACnetHealthProcessor
from src.utils.logger import logger
from src.utils.performance import performance_metrics


class BACnetMonitor:
    def __init__(self):
        """Initialize the BACnet monitor."""
        pass

    def _create_controller_point_model(
        self,
        iot_device_point_id: str,
        controller_id: str,
        point_id: int,
        bacnet_object_type: str,
        present_value: Optional[str],
        controller_ip_address: str,
        controller_device_id: str,
        units: Optional[str],
        all_properties_data: Optional[Dict] = None,
        error_info: Optional[str] = None,
    ) -> ControllerPointsModel:
        """
        Helper method to create ControllerPointsModel with all optional properties.

        Args:
            iot_device_point_id: IOT device point identifier
            controller_id: Controller identifier
            point_id: Point identifier
            bacnet_object_type: BACnet object type
            present_value: Present value as string
            controller_ip_address: Controller IP address
            controller_device_id: Controller device ID
            units: Units for the point
            all_properties_data: Dictionary containing all health and optional properties
            error_info: Error information if fallback occurred

        Returns:
            ControllerPointsModel instance with all parameters set
        """
        # Use empty dict if no all_properties_data provided (fallback case)
        all_properties_data = all_properties_data or {}

        return ControllerPointsModel(
            iot_device_point_id=iot_device_point_id,
            controller_id=controller_id,
            point_id=point_id,
            bacnet_object_type=bacnet_object_type,
            present_value=present_value,
            controller_ip_address=controller_ip_address,
            controller_device_id=controller_device_id,
            controller_port=DEFAULT_CONTROLLER_PORT,
            units=units,
            is_uploaded=False,
            # Health properties
            status_flags=all_properties_data.get("status_flags"),
            event_state=all_properties_data.get("event_state"),
            out_of_service=all_properties_data.get("out_of_service"),
            reliability=all_properties_data.get("reliability"),
            error_info=error_info or all_properties_data.get("error_info"),
            # Value Limit Properties
            min_pres_value=all_properties_data.get("min_pres_value"),
            max_pres_value=all_properties_data.get("max_pres_value"),
            high_limit=all_properties_data.get("high_limit"),
            low_limit=all_properties_data.get("low_limit"),
            resolution=all_properties_data.get("resolution"),
            # Control Properties
            priority_array=all_properties_data.get("priority_array"),
            relinquish_default=all_properties_data.get("relinquish_default"),
            # Notification Configuration Properties
            cov_increment=all_properties_data.get("cov_increment"),
            time_delay=all_properties_data.get("time_delay"),
            time_delay_normal=all_properties_data.get("time_delay_normal"),
            notification_class=all_properties_data.get("notification_class"),
            notify_type=all_properties_data.get("notify_type"),
            deadband=all_properties_data.get("deadband"),
            limit_enable=all_properties_data.get("limit_enable"),
            # Event Properties
            event_enable=all_properties_data.get("event_enable"),
            acked_transitions=all_properties_data.get("acked_transitions"),
            event_time_stamps=all_properties_data.get("event_time_stamps"),
            event_message_texts=all_properties_data.get("event_message_texts"),
            event_message_texts_config=all_properties_data.get(
                "event_message_texts_config"
            ),
            # Algorithm Control Properties
            event_detection_enable=all_properties_data.get("event_detection_enable"),
            event_algorithm_inhibit_ref=all_properties_data.get(
                "event_algorithm_inhibit_ref"
            ),
            event_algorithm_inhibit=all_properties_data.get("event_algorithm_inhibit"),
            reliability_evaluation_inhibit=all_properties_data.get(
                "reliability_evaluation_inhibit"
            ),
        )

    async def initialize(self) -> None:
        """Initialize the BACnet monitor (compatibility method for actor)."""
        # No-op since initialization now happens in initialize_bacnet_readers()
        # This method exists for backward compatibility with bacnet_monitoring_actor.py
        pass

    async def initialize_bacnet_readers(
        self, reader_configs: List[BacnetReaderConfig]
    ) -> None:
        """Initialize BACnet wrapper manager with reader configurations."""
        logger.info(f"Initializing {len(reader_configs)} BACnet readers")

        # Simple call - wrapper manager handles all internal cleanup automatically
        await bacnet_wrapper_manager.initialize_readers(reader_configs)

        # Get actual count of successfully initialized readers
        actual_initialized_count = len(bacnet_wrapper_manager.get_all_wrappers())
        logger.info(
            f"Successfully initialized BACnet wrapper manager with {actual_initialized_count} active readers"
        )

    async def discover_devices(self, device_address_list: List[str]):
        """Discover BACnet devices on the network using all available wrappers."""
        devices: List[Dict] = []

        # Get all available wrappers
        all_wrappers = bacnet_wrapper_manager.get_all_wrappers()

        for wrapper_id, wrapper in all_wrappers.items():
            logger.info(f"Discovering devices using wrapper {wrapper.instance_id}")
            for address in device_address_list:
                try:
                    who_is_devices = await wrapper.who_is(address=address)
                    logger.info(
                        f"Wrapper {wrapper.instance_id} found devices at {address}: {who_is_devices}"
                    )
                    for device in who_is_devices:
                        device_instance, device_id = device.iAmDeviceIdentifier
                        device_info = {
                            "iam_device_identifier": device.iAmDeviceIdentifier,
                            "vendor_id": device.vendorID,
                            "device_id": device_id,
                            "address": device.pduSource,
                            "discovered_by_reader": wrapper.instance_id,  # Track which wrapper found this device
                        }
                        devices.append(device_info)
                except Exception as e:
                    logger.error(
                        f"Wrapper {wrapper.instance_id} failed to discover devices at {address}: {e}"
                    )
                    continue

        logger.info(f"Total devices discovered: {len(devices)}")
        return devices

    def display_device_info(self, device_id: int):
        """Display information about a specific device."""
        pass

    async def get_object_list(self, controller_ip_address: str, device_id: int):
        """Get a list of objects for a specific device."""
        # Get wrapper for this operation
        wrapper = await bacnet_wrapper_manager.get_wrapper_for_operation()
        if not wrapper:
            raise RuntimeError("No BACnet wrapper available for operation")

        object_list = await wrapper.read_object_list(controller_ip_address, device_id)
        logger.info(f"Object list: {object_list}")

        return object_list

    def display_object_info(self, device_id: int, object_type: str, object_id: int):
        """Display information about a specific object."""
        pass

    async def monitor_objects(self, device_id: int, interval: int):
        """Monitor all objects of a specific device."""
        pass

    @performance_metrics("monitor_all_devices")
    async def monitor_all_devices(self):
        """Monitor all devices and their objects on the network using available wrappers."""
        logger.info("STARTED: Monitoring all devices")
        # Get controllers from the database
        controllers = await get_latest_bacnet_config_json_as_list()
        if not controllers:
            logger.warning("No controllers found in the database")
            return

        # Log available wrappers
        all_wrappers = bacnet_wrapper_manager.get_all_wrappers()
        logger.info(f"Starting monitoring with {len(all_wrappers)} available wrappers")

        # Log wrapper utilization before starting
        if all_wrappers:
            utilization_info = await bacnet_wrapper_manager.get_utilization_info()
            logger.info(f"Wrapper utilization before monitoring: {utilization_info}")

        for controller in controllers:
            # Build bulk read request for all points on this controller
            point_requests = []
            point_metadata = {}  # Store metadata for each point

            for each_object in controller.object_list:
                units = (
                    getattr(each_object.properties, "units", None)
                    if each_object.properties
                    else None
                )

                # Get available properties based on configuration
                object_properties_dict = None
                if hasattr(each_object, "properties") and each_object.properties:
                    # Convert properties object to dict if needed
                    if hasattr(each_object.properties, "__dict__"):
                        object_properties_dict = each_object.properties.__dict__
                    elif isinstance(each_object.properties, dict):
                        object_properties_dict = each_object.properties
                    else:
                        logger.info(
                            f"Unknown properties type: {type(each_object.properties)}"
                        )

                # Only read properties that are available for this object
                properties_to_read = self.get_available_device_properties(
                    object_properties_dict
                )
                logger.info(
                    f"Reading device properties for {each_object.iot_device_point_id}, {each_object.type}, {each_object.point_id}: {properties_to_read}"
                )
                if (
                    len(properties_to_read) == 1
                    and properties_to_read[0] == "presentValue"
                ):
                    logger.warning(
                        f"No additional device properties to read for {each_object.iot_device_point_id}, {each_object.type}, {each_object.point_id}"
                    )

                # Add to bulk request
                point_requests.append(
                    {
                        "object_type": each_object.type,
                        "object_id": each_object.point_id,
                        "properties": properties_to_read,
                    }
                )

                # Store metadata for processing results later
                object_key = f"{each_object.type}:{each_object.point_id}"
                point_metadata[object_key] = {
                    "iot_device_point_id": each_object.iot_device_point_id,
                    "units": units,
                    "object": each_object,
                }

            if not point_requests:
                logger.warning(
                    f"No points to read for controller {controller.controller_ip_address}"
                )
                continue

            # Get wrapper for this controller's bulk operation
            wrapper = await bacnet_wrapper_manager.get_wrapper_for_operation()
            if not wrapper:
                logger.error(
                    f"No wrapper available for controller {controller.controller_ip_address}"
                )
                continue

            try:
                # Execute bulk read for all points on this controller
                logger.info(
                    f"Executing bulk read for {len(point_requests)} points on controller {controller.controller_ip_address}"
                )
                bulk_results = await wrapper.read_multiple_points(
                    device_ip=controller.controller_ip_address,
                    point_requests=point_requests,
                )

                # Collect all successful points for bulk insertion
                controller_points_to_insert = []
                fallback_points = []

                # Process results for each point
                for object_key, raw_properties in bulk_results.items():
                    if object_key not in point_metadata:
                        logger.warning(
                            f"Received result for unknown point: {object_key}"
                        )
                        continue

                    metadata = point_metadata[object_key]
                    each_object = metadata["object"]
                    units = metadata["units"]

                    try:
                        if raw_properties:  # Non-empty result
                            # Extract present value
                            present_value = raw_properties.get("presentValue")

                            logger.info(
                                f"Read value for {metadata['iot_device_point_id']} using wrapper {wrapper.instance_id}: {raw_properties}"
                            )

                            # Process health properties (including optional BACnet properties)
                            health_data = (
                                BACnetHealthProcessor.process_all_health_properties(
                                    raw_properties
                                )
                            )
                            # Process optional BACnet properties
                            optional_properties = (
                                BACnetHealthProcessor.process_all_optional_properties(
                                    raw_properties
                                )
                            )
                            # Merge health and optional properties
                            health_data.update(optional_properties)
                            logger.debug(f"Health data: {health_data}")

                            # Create controller point with health data for bulk insert
                            controller_point = self._create_controller_point_model(
                                iot_device_point_id=metadata["iot_device_point_id"],
                                controller_id=controller.controller_id,
                                point_id=each_object.point_id,
                                bacnet_object_type=each_object.type,
                                present_value=(
                                    str(present_value)
                                    if present_value is not None
                                    else None
                                ),
                                controller_ip_address=controller.controller_ip_address,
                                controller_device_id=controller.device_id,
                                units=units,
                                all_properties_data=health_data,
                            )
                            controller_points_to_insert.append(controller_point)
                        else:
                            # Empty result - add to fallback list
                            logger.warning(
                                f"Empty bulk read result for {metadata['iot_device_point_id']}, will attempt individual fallback"
                            )
                            fallback_points.append((each_object, units))

                    except Exception as e:
                        logger.debug(
                            f"Failed to process bulk read result for {metadata['iot_device_point_id']}: {e}"
                        )
                        # Add to fallback list
                        fallback_points.append((each_object, units))

                # Bulk insert all successful controller points
                if controller_points_to_insert:
                    try:
                        logger.info(
                            f"Bulk inserting {len(controller_points_to_insert)} controller points for {controller.controller_ip_address}"
                        )
                        await bulk_insert_controller_points(controller_points_to_insert)
                        logger.info(
                            f"Successfully bulk inserted {len(controller_points_to_insert)} points for controller {controller.controller_ip_address}"
                        )
                    except Exception as bulk_insert_error:
                        logger.error(
                            f"Bulk insert failed for controller {controller.controller_ip_address}: {bulk_insert_error}"
                        )
                        # Fallback to individual inserts for these points
                        for point in controller_points_to_insert:
                            try:
                                await insert_controller_point(point)
                            except Exception as individual_error:
                                logger.error(
                                    f"Individual insert fallback also failed for point {point.iot_device_point_id}: {individual_error}"
                                )

                # Handle fallback individual reads for failed bulk read points
                for each_object, units in fallback_points:
                    await self._fallback_individual_read(
                        wrapper, controller, each_object, units
                    )

            except Exception as e:
                logger.warning(
                    f"Bulk read failed for controller {controller.controller_ip_address}: {e}"
                )
                logger.info(
                    f"Falling back to individual reads for {len(point_requests)} points"
                )

                # Fallback to individual reads for all points on this controller
                # Note: Could potentially optimize this with bulk collection + bulk insert too,
                # but keeping individual for fallback simplicity since bulk read already failed
                for request in point_requests:
                    object_key = f"{request['object_type']}:{request['object_id']}"
                    if object_key in point_metadata:
                        metadata = point_metadata[object_key]
                        await self._fallback_individual_read(
                            wrapper, controller, metadata["object"], metadata["units"]
                        )

        # Log wrapper utilization after monitoring
        if all_wrappers:
            utilization_info = await bacnet_wrapper_manager.get_utilization_info()
            logger.info(f"Wrapper utilization after monitoring: {utilization_info}")

        logger.info("FINISHED: Monitoring all devices")

    async def _fallback_individual_read(self, wrapper, controller, each_object, units):
        """
        Fallback to individual point reading when bulk read fails.

        Args:
            wrapper: BACnet wrapper to use for reading
            controller: Controller object
            each_object: Point object to read
            units: Units for the point
        """
        point_read_success = False

        try:
            # Get available properties based on configuration
            object_properties_dict = None
            if hasattr(each_object, "properties") and each_object.properties:
                # Convert properties object to dict if needed
                if hasattr(each_object.properties, "__dict__"):
                    object_properties_dict = each_object.properties.__dict__
                elif isinstance(each_object.properties, dict):
                    object_properties_dict = each_object.properties

            # Only read properties that are available for this object
            properties_to_read = self.get_available_device_properties(
                object_properties_dict
            )

            raw_properties = await wrapper.read_properties(
                device_ip=controller.controller_ip_address,
                object_type=each_object.type,
                object_id=each_object.point_id,
                properties=properties_to_read,
            )

            # Extract present value
            present_value = raw_properties.get("presentValue")

            logger.info(
                f"Individual fallback read value for {each_object.iot_device_point_id} using wrapper {wrapper.instance_id}: {raw_properties}"
            )

            # Process health properties (including optional BACnet properties)
            health_data = BACnetHealthProcessor.process_all_health_properties(
                raw_properties
            )
            # Process optional BACnet properties
            optional_properties = BACnetHealthProcessor.process_all_optional_properties(
                raw_properties
            )
            # Merge health and optional properties
            health_data.update(optional_properties)
            logger.debug(f"Health data: {health_data}")

            # Create controller point with health data
            controller_point = self._create_controller_point_model(
                iot_device_point_id=each_object.iot_device_point_id,
                controller_id=controller.controller_id,
                point_id=each_object.point_id,
                bacnet_object_type=each_object.type,
                present_value=(
                    str(present_value) if present_value is not None else None
                ),
                controller_ip_address=controller.controller_ip_address,
                controller_device_id=controller.device_id,
                units=units,
                all_properties_data=health_data,
            )
            await insert_controller_point(controller_point)

            point_read_success = True

        except Exception as e:
            logger.debug(
                f"Wrapper {wrapper.instance_id} failed to read properties for {each_object.iot_device_point_id}: {e}"
            )
            # Try fallback with present value only
            try:
                read_value = await wrapper.read_present_value(
                    controller.controller_ip_address,
                    each_object.type,
                    each_object.point_id,
                )
                logger.info(
                    f"Fallback read value from wrapper {wrapper.instance_id}: {read_value}"
                )
                # Create fallback controller point with error info
                error_info = json.dumps(
                    {
                        "error_class": "monitor.py",
                        "error_code": f"Failed to read properties with health properties. Falling back to present value only. Error: {e}",
                    }
                )
                controller_point = self._create_controller_point_model(
                    iot_device_point_id=each_object.iot_device_point_id,
                    controller_id=controller.controller_id,
                    point_id=each_object.point_id,
                    bacnet_object_type=each_object.type,
                    present_value=str(read_value),
                    controller_ip_address=controller.controller_ip_address,
                    controller_device_id=controller.device_id,
                    units=units,
                    all_properties_data=None,  # No properties data on fallback
                    error_info=error_info,
                )
                await insert_controller_point(controller_point)
                point_read_success = True
            except Exception as fallback_error:
                logger.debug(
                    f"Wrapper {wrapper.instance_id} fallback also failed for {each_object.iot_device_point_id}: {fallback_error}"
                )

        if not point_read_success:
            logger.error(
                f"All wrappers failed to read point {each_object.iot_device_point_id} on controller {controller.controller_ip_address}"
            )

    async def stop_monitor(self):
        """Stop the BAC0 application"""
        # The original stop logic would go here
        logger.info("Stopping BAC0 core (if running)...")

    def is_point_type(self, obj_data):
        point_type = get_point_types()
        obj_type, point_id = obj_data

        # We check what type of object it is and if it is a point type we return true.
        # Its from bacpypes.object and not clear what messages we can send to it.
        if obj_type.asn1 in point_type:
            return True
        return False

    def get_available_device_properties(
        self, object_properties: Optional[dict]
    ) -> List[str]:
        """Get list of available device properties based on stored configuration.
        Includes both health monitoring properties and device configuration properties.

        Args:
            object_properties: Dictionary of properties from BACnet configuration

        Returns:
            List of property names that are available for this object
        """

        # Always try to read presentValue as it's essential
        available = ["presentValue"]

        if not object_properties:
            # If no properties info, return minimal set
            logger.debug(
                "No properties configuration available, using minimal property set"
            )
            return available

        # Device properties to check (health monitoring + device configuration properties)
        monitorable_properties = [
            # Existing health properties
            "statusFlags",
            "eventState",
            "outOfService",
            "reliability",
            # Value limit properties
            "minPresValue",
            "maxPresValue",
            "highLimit",
            "lowLimit",
            "resolution",
            # Control properties
            "priorityArray",
            "relinquishDefault",
            # Notification configuration
            "covIncrement",
            "timeDelay",
            "timeDelayNormal",
            "notificationClass",
            "notifyType",
            "deadband",
            "limitEnable",
            # Event properties
            "eventEnable",
            "ackedTransitions",
            "eventTimeStamps",
            "eventMessageTexts",
            "eventMessageTextsConfig",
            # Algorithm control properties
            "eventDetectionEnable",
            "eventAlgorithmInhibitRef",
            "eventAlgorithmInhibit",
            "reliabilityEvaluationInhibit",
        ]

        # Only add properties that exist in the configuration
        for prop in monitorable_properties:
            if prop in object_properties:
                # Check if the property is not null (some objects have statusFlags: null)
                if object_properties[prop] is not None:
                    available.append(prop)
                else:
                    logger.debug(
                        f"Property {prop} exists but is null in configuration, skipping"
                    )
            else:
                logger.debug(f"Property {prop} not found in object configuration")

        logger.info(f"Available properties to read: {available}")
        return available

    async def fetch_from_bacnet_network_and_save_config(
        self, iotDeviceControllers: List[dict]
    ):
        """Fetch and save a configuration from the BACnet network into the database."""
        logger.info(
            f"Fetching and saving config for iotDeviceControllers: {iotDeviceControllers}"
        )
        bacnet_device_infos = await self.fetch_config(iotDeviceControllers)
        logger.info(f"Bacnet device infos: {len(bacnet_device_infos)}")
        await insert_bacnet_config_json(bacnet_device_infos)
        logger.info("Bacnet device infos saved to database")

    async def fetch_config(self, iotDeviceControllers: List[dict]):
        devices: List[Dict] = []

        # Get all available wrappers
        all_wrappers = bacnet_wrapper_manager.get_all_wrappers()

        for iotDeviceController in iotDeviceControllers:
            controller_ip_address = iotDeviceController["ipAddress"]
            controller_device_id = iotDeviceController["controllerDeviceId"]
            controller_id = iotDeviceController["id"]
            logger.info(
                f"Fetching config for controller: {controller_ip_address} {controller_device_id} {controller_id}"
            )

            # Try each wrapper until one succeeds or all fail
            device_found = False
            for wrapper_id, wrapper in all_wrappers.items():
                try:
                    logger.info(
                        f"Trying to discover controller {controller_ip_address} using wrapper {wrapper.instance_id}"
                    )
                    who_is_devices = await wrapper.who_is(controller_ip_address)

                    if not who_is_devices:
                        logger.info(
                            f"No devices found at {controller_ip_address} using wrapper {wrapper.instance_id}"
                        )
                        continue

                    for device in who_is_devices:
                        device_instance, device_id = device.iAmDeviceIdentifier
                        object_list = await wrapper.read_object_list(
                            ip=controller_ip_address, device_id=device_id
                        )

                        logger.info(
                            f"controller_ip_address: {controller_ip_address}, device_id: {device_id}, Object list: {object_list}"
                        )
                        filtered_object_list = [
                            obj for obj in object_list if self.is_point_type(obj)
                        ]
                        filtered_object_list_mapped = await self._map_and_enrich_object_list(
                            controller_id=controller_id,
                            controller_ip_address=controller_ip_address,
                            filtered_object_list=filtered_object_list,
                            wrapper=wrapper,  # Pass the wrapper for property reading
                        )

                        device_info = {
                            "vendor_id": device.vendorID,
                            "device_id": device_id,
                            "controller_ip_address": controller_ip_address,
                            "controller_device_id": device_id,  # This is redundant, adding it for clarity due to too many ids.
                            "controller_id": controller_id,
                            "object_list": filtered_object_list_mapped,
                            "configured_by_reader": wrapper.instance_id,  # Track which wrapper was used
                        }

                        devices.append(device_info)
                        device_found = True
                        logger.info(
                            f"Successfully configured controller {controller_ip_address} using wrapper {wrapper.instance_id}"
                        )
                        break  # Found device, no need to try other wrappers

                    if device_found:
                        break  # Successfully found device with this wrapper

                except Exception as e:
                    logger.error(
                        f"Wrapper {wrapper.instance_id} failed to fetch config for controller {controller_ip_address}: {e}"
                    )
                    continue

            if not device_found:
                logger.error(
                    f"Failed to configure controller {controller_ip_address} with any available wrapper"
                )

        logger.info(f"Devices: {len(devices)}")
        bacnet_device_infos = [BacnetDeviceInfo(**device) for device in devices]
        logger.info(f"Bacnet device infos: {len(bacnet_device_infos)}")
        return bacnet_device_infos

    async def _map_and_enrich_object_list(
        self,
        controller_id: str,
        controller_ip_address: str,
        filtered_object_list,
        wrapper: Optional[Any] = None,
    ):
        filtered_object_list_mapped: List[Dict[str, Any]] = [
            {
                "type": (
                    lambda bacnet_type: (
                        bacnet_type.value if bacnet_type is not None else None
                    )
                )(convert_point_type_to_bacnet_object_type(obj_type.asn1)),
                "point_id": point_id,
                # Deterministically generate a uuid for the iot device point
                # using the controller_id and point_id
                "iot_device_point_id": str(
                    uuid.uuid5(uuid.NAMESPACE_URL, f"{controller_id}-{point_id}")
                ),
            }
            for obj_type, point_id in filtered_object_list
        ]

        # Wrapper must be provided - fail fast if not
        if wrapper is None:
            raise ValueError(
                "Wrapper is required for mapping and enriching object list"
            )
        wrapper_to_use = wrapper

        for obj in filtered_object_list_mapped:
            object_type = obj["type"]
            point_id = obj["point_id"]

            # Skip if type or point_id is None
            if object_type is None or point_id is None:
                obj["properties"] = {}
                continue

            # Ensure object_type is string and point_id is int
            if not isinstance(object_type, str) or not isinstance(point_id, int):
                obj["properties"] = {}
                continue

            try:
                properties = await wrapper_to_use.read_all_properties(
                    device_ip=controller_ip_address,
                    object_type=object_type,
                    object_id=point_id,
                )

                properties_dict = extract_property_dict_camel(properties)
                status_flags = properties_dict["statusFlags"]
                # Convert the status flags to a string
                # values are -> in-alarm;fault;overridden;out-of-service
                status_flags = str(status_flags) or None
                properties_dict["statusFlags"] = status_flags
                obj["properties"] = properties_dict
                logger.info(
                    f"Filtered object list was successfully mapped and enriched. {obj}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to get properties for {object_type} {point_id}: {e}"
                )
                obj["properties"] = {}  # Set empty properties on failure

        return filtered_object_list_mapped
