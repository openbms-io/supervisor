import logging
from typing import Optional, Union
import ipaddress
from src.actors.messages.message_type import (
    SetValueToPointRequestPayload,
    SetValueToPointResponsePayload,
)
from src.models.bacnet_wrapper_manager import (
    bacnet_wrapper_manager,
    get_default_bacnet_wrapper,
)
from src.models.bacnet_wrapper import BACnetWrapper
from src.models.bacnet_config import (
    BacnetDeviceInfo,
    BacnetObjectInfo,
    get_latest_bacnet_config_json_as_list,
)
from src.models.controller_points import ControllerPointsModel, insert_controller_point
from src.config.config import DEFAULT_CONTROLLER_PORT

logger = logging.getLogger(__name__)


class BACnetWriter:
    def __init__(self):
        self.bacnet_wrapper_manager = bacnet_wrapper_manager

    async def start(self):
        """Initialize the BACnet writer and its dependencies."""
        # Writer relies on readers being initialized by the monitoring actor
        pass

    async def write_value_to_point(
        self, payload: SetValueToPointRequestPayload
    ) -> tuple[SetValueToPointResponsePayload, Optional[ControllerPointsModel]]:
        """
        Write a value to a BACnet point and return the response plus database record.

        Args:
            payload: SetValueToPointRequestPayload containing the write request details

        Returns:
            Tuple of (response_payload, database_record) where database_record is None if write failed
        """
        logger.info(
            f"Processing set value request for point {payload.iotDevicePointId}"
        )

        try:
            # Extract payload data
            controller_id = payload.controllerId
            point_instance_id = payload.pointInstanceId
            value_to_write = payload.presentValue

            # Get controller configuration
            target_controller, target_object = await self._find_target_point(
                controller_id, point_instance_id
            )

            # Perform the BACnet write operation
            written_value = await self._perform_write_operation(
                target_controller, target_object, value_to_write
            )

            # Create database record for the successful write
            db_record = await self._create_database_record(
                payload, written_value, target_controller, target_object
            )

            # Return success response and database record
            response = SetValueToPointResponsePayload(
                success=True,
                message=f"Successfully wrote value {written_value} to point {payload.iotDevicePointId}",
                commandId=payload.commandId,
            )

            return response, db_record

        except Exception as e:
            logger.error(
                f"Failed to write value to point {payload.iotDevicePointId}: {e}"
            )

            # Return error response with no database record
            response = SetValueToPointResponsePayload(
                success=False,
                message=f"Failed to write value to point {payload.iotDevicePointId}: {str(e)}",
                commandId=payload.commandId,
            )

            return response, None

    async def _find_target_point(self, controller_id: str, point_instance_id: str):
        """
        Find the target controller and object from the configuration.

        Args:
            controller_id: ID of the target controller
            point_instance_id: ID of the target point

        Returns:
            Tuple of (target_controller, target_object)

        Raises:
            ValueError: If controller or point not found
        """
        # Get the controller configuration
        controllers = await get_latest_bacnet_config_json_as_list()
        if not controllers:
            raise ValueError("No controllers found in configuration")

        # Find the specific controller
        target_controller = None
        for controller in controllers:
            if controller.controller_id == controller_id:
                target_controller = controller
                break

        if not target_controller:
            raise ValueError(f"Controller {controller_id} not found in configuration")

        # Find the specific point within the controller
        target_object = None
        for obj in target_controller.object_list:
            if str(obj.point_id) == point_instance_id:
                target_object = obj
                break

        if not target_object:
            raise ValueError(
                f"Point {point_instance_id} not found in controller {controller_id}"
            )

        return target_controller, target_object

    async def _perform_write_operation(
        self,
        target_controller: BacnetDeviceInfo,
        target_object: BacnetObjectInfo,
        value_to_write: Union[int, float],
    ):
        """
        Perform the actual BACnet write operation.

        Args:
            target_controller: Controller configuration object
            target_object: Point configuration object
            value_to_write: Value to write to the point

        Returns:
            The actual value written (verified by reading back)

        Raises:
            Exception: If write operation fails
        """
        # Extract write operation parameters
        object_type = target_object.properties.get("objectType")
        point_id = target_object.point_id
        controller_ip_address = target_controller.controller_ip_address

        logger.info(f"Target object type: {object_type}")
        logger.info(
            f"Writing value {value_to_write} to {controller_ip_address} {object_type} {point_id}"
        )

        # Find the appropriate wrapper for this controller
        wrapper = await self._find_wrapper_for_controller(controller_ip_address)
        if not wrapper:
            raise Exception(
                f"No BACnet wrapper available to reach controller {controller_ip_address}"
            )

        logger.info(
            f"Using wrapper {wrapper.instance_id} for controller {controller_ip_address}"
        )

        # Perform the write with priority 8 (manual priority)
        # Priority 8 is manual operator priority
        # Priority 1 would be life safety and critical priority
        written_value = await wrapper.write_with_priority(
            ip=controller_ip_address,
            objectType=object_type,
            point_id=point_id,
            present_value=value_to_write,
            priority=8,
        )

        logger.info(
            f"Successfully wrote and verified value {written_value} to point {point_id}"
        )
        return written_value

    async def _create_database_record(
        self,
        payload: SetValueToPointRequestPayload,
        written_value: Union[int, float],
        target_controller: BacnetDeviceInfo,
        target_object: BacnetObjectInfo,
    ) -> ControllerPointsModel:
        """
        Create and store a database record for the manual write.

        Args:
            payload: Original write request payload
            written_value: The actual value that was written and verified
            target_controller: Controller configuration object
            target_object: Point configuration object

        Returns:
            ControllerPointsModel: The created database record
        """
        # Create a controller points record for the manual write
        write_record = ControllerPointsModel(
            iot_device_point_id=target_object.iot_device_point_id,
            controller_id=target_controller.controller_id,
            point_id=target_object.point_id,
            bacnet_object_type=target_object.type,
            present_value=str(written_value),
            controller_ip_address=target_controller.controller_ip_address,
            controller_device_id=target_controller.device_id,
            controller_port=DEFAULT_CONTROLLER_PORT,
            units=(
                getattr(target_object.properties, "units", None)
                if target_object.properties
                else None
            ),
            is_uploaded=False,  # Will be processed by uploader
        )

        # Write to local database (same as bacnet_monitoring_actor does)
        await insert_controller_point(write_record)
        logger.info(
            f"Stored manual write to local DB: point_id={target_object.point_id}, value={written_value}"
        )

        return write_record

    async def _find_wrapper_for_controller(
        self, controller_ip: str
    ) -> Optional[BACnetWrapper]:
        """Find the best BACnet wrapper to communicate with a specific controller IP."""
        # Get all available wrappers
        all_wrappers = self.bacnet_wrapper_manager.get_all_wrappers()

        if not all_wrappers:
            # Fallback to default wrapper if available
            return get_default_bacnet_wrapper()

        try:
            controller_ip_obj = ipaddress.IPv4Address(controller_ip)

            # Find the wrapper whose IP is on the same subnet as the controller
            for reader_id, wrapper in all_wrappers.items():
                try:
                    # Check if they're on the same subnet using configured subnet mask
                    wrapper_network = ipaddress.IPv4Network(
                        f"{wrapper.ip}/{wrapper.subnet_mask}", strict=False
                    )
                    if controller_ip_obj in wrapper_network:
                        logger.info(
                            f"Found wrapper {wrapper.instance_id} on same network for controller {controller_ip}"
                        )
                        return wrapper

                except (ipaddress.AddressValueError, ValueError):
                    logger.warning(
                        f"Invalid IP address for wrapper {reader_id}: {wrapper.ip}"
                    )
                    continue

            # If no network match found, return the first available wrapper
            first_wrapper = next(iter(all_wrappers.values()))
            logger.info(
                f"No network match found, using first available wrapper {first_wrapper.instance_id} for controller {controller_ip}"
            )
            return first_wrapper

        except (ipaddress.AddressValueError, ValueError):
            logger.warning(f"Invalid controller IP address: {controller_ip}")
            # Return first available wrapper as fallback
            return (
                next(iter(all_wrappers.values()))
                if all_wrappers
                else get_default_bacnet_wrapper()
            )
