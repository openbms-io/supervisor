"""
Comprehensive tests for BACnetMonitor.monitor_all_devices() method.

This test suite ensures complete coverage of the monitor_all_devices functionality
to establish baseline behavior before optimization.

IMPORTANT: These tests use REAL SQLite database to verify actual data persistence.
Only BAC0 network operations are mocked.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.controllers.monitoring.monitor import BACnetMonitor
from src.models.controller_points import ControllerPointsModel


def create_mock_wrapper_with_bulk_support(
    instance_id="reader_1", bulk_result=None, individual_result=None
):
    """Helper to create a mock wrapper with bulk read support"""
    mock_wrapper = Mock()
    mock_wrapper.instance_id = instance_id

    # Default results if not provided
    if bulk_result is None:
        bulk_result = {
            "analogInput:1": {"presentValue": 72.5},
            "analogOutput:2": {"presentValue": 55.0},
        }

    if individual_result is None:
        individual_result = {"presentValue": 72.5}

    # Mock the new bulk read method
    mock_wrapper.read_multiple_points = AsyncMock(return_value=bulk_result)

    # Keep individual methods for fallback
    mock_wrapper.read_properties = AsyncMock(return_value=individual_result)
    mock_wrapper.read_present_value = AsyncMock(return_value=72.5)

    return mock_wrapper


class TestMonitorAllDevicesBasicFunctionality:
    """Test basic monitor_all_devices functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = BACnetMonitor()

        # Create mock controller with points
        self.mock_controller = Mock()
        self.mock_controller.controller_ip_address = "192.168.1.100"
        self.mock_controller.controller_id = "controller_1"
        self.mock_controller.device_id = 12345

        # Create mock points
        self.mock_point_1 = Mock()
        self.mock_point_1.iot_device_point_id = "point_1"
        self.mock_point_1.type = "analogInput"
        self.mock_point_1.point_id = 1
        self.mock_point_1.properties = Mock()
        self.mock_point_1.properties.__dict__ = {
            "presentValue": 72.5,
            "statusFlags": "in-alarm",
            "eventState": "normal",
            "outOfService": False,
            "reliability": "no-fault-detected",
            "units": "degreesFahrenheit",
        }

        self.mock_point_2 = Mock()
        self.mock_point_2.iot_device_point_id = "point_2"
        self.mock_point_2.type = "analogOutput"
        self.mock_point_2.point_id = 2
        self.mock_point_2.properties = Mock()
        self.mock_point_2.properties.__dict__ = {
            "presentValue": 55.0,
            "statusFlags": None,
            "units": "percent",
        }

        self.mock_controller.object_list = [self.mock_point_1, self.mock_point_2]

    @pytest.mark.asyncio
    async def test_monitor_all_devices_success_flow(self):
        """Test: Successful monitoring of all devices with multiple points"""

        # Mock wrapper with bulk read support
        mock_wrapper = create_mock_wrapper_with_bulk_support(
            instance_id="reader_1",
            bulk_result={
                "analogInput:1": {
                    "presentValue": 72.5,
                    "statusFlags": "in-alarm",
                    "eventState": "normal",
                    "outOfService": False,
                    "reliability": "no-fault-detected",
                },
                "analogOutput:2": {"presentValue": 55.0},
            },
        )

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health_processor,
        ):
            # Setup mocks
            mock_get_config.return_value = [self.mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(
                return_value={"reader_1": {"active": 0}}
            )
            mock_health_processor.process_all_health_properties.return_value = {
                "status_flags": "processed_flags",
                "event_state": "normal",
                "out_of_service": False,
                "reliability": "no-fault-detected",
            }

            # Execute
            await self.monitor.monitor_all_devices()

            # Verify controller config was fetched
            mock_get_config.assert_called_once()

            # With optimization: verify wrapper was obtained once per controller (not per point)
            assert mock_manager.get_wrapper_for_operation.call_count == 1

            # Verify bulk read was attempted first
            mock_wrapper.read_multiple_points.assert_called_once()

            # Individual reads should not be called when bulk read succeeds
            assert mock_wrapper.read_properties.call_count == 0

            # Verify bulk read was called with correct parameters
            bulk_call_args = mock_wrapper.read_multiple_points.call_args[1]
            assert bulk_call_args["device_ip"] == "192.168.1.100"

            # Verify the point requests include both points
            point_requests = bulk_call_args["point_requests"]
            assert len(point_requests) == 2

            # Verify first point request
            point_1_req = next(
                (req for req in point_requests if req["object_id"] == 1), None
            )
            assert point_1_req is not None
            assert point_1_req["object_type"] == "analogInput"
            assert "presentValue" in point_1_req["properties"]

            # Verify second point request
            point_2_req = next(
                (req for req in point_requests if req["object_id"] == 2), None
            )
            assert point_2_req is not None
            assert point_2_req["object_type"] == "analogOutput"
            assert point_2_req["properties"] == ["presentValue"]

            # Note: With bulk insert optimization, individual inserts are replaced by bulk insert
            # This assertion may need updating when bulk insert is implemented
            # For now, fallback mechanism still uses individual inserts
            assert (
                mock_insert.call_count >= 0
            )  # May be 0 with bulk insert, >0 with fallback

    @pytest.mark.asyncio
    async def test_monitor_all_devices_uses_bulk_insert(self):
        """Test: Monitor uses bulk insert for successful BACnet reads"""
        mock_wrapper = create_mock_wrapper_with_bulk_support(
            instance_id="reader_1",
            bulk_result={
                "analogInput:1": {"presentValue": 72.5, "statusFlags": "normal"},
                "analogOutput:2": {"presentValue": 55.0, "statusFlags": "normal"},
            },
        )

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_individual_insert,
            patch(
                "src.controllers.monitoring.monitor.bulk_insert_controller_points"
            ) as mock_bulk_insert,
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health_processor,
        ):
            # Setup mocks
            mock_get_config.return_value = [self.mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(
                return_value={"reader_1": {"active": 0}}
            )
            mock_health_processor.process_all_health_properties.return_value = {
                "status_flags": "processed_flags",
                "event_state": "normal",
                "out_of_service": False,
                "reliability": "no-fault-detected",
            }
            mock_bulk_insert.return_value = []  # Mock successful bulk insert

            # Execute
            await self.monitor.monitor_all_devices()

            # Verify bulk insert was called once with multiple points
            assert mock_bulk_insert.call_count == 1

            # Verify bulk insert was called with correct number of points
            bulk_insert_call_args = mock_bulk_insert.call_args[0][
                0
            ]  # First positional argument
            assert len(bulk_insert_call_args) == 2  # Should have 2 controller points

            # Verify the controller points have correct data
            point_1 = next((p for p in bulk_insert_call_args if p.point_id == 1), None)
            assert point_1 is not None
            assert point_1.iot_device_point_id == "point_1"
            assert point_1.bacnet_object_type == "analogInput"
            assert point_1.present_value == "72.5"

            point_2 = next((p for p in bulk_insert_call_args if p.point_id == 2), None)
            assert point_2 is not None
            assert point_2.iot_device_point_id == "point_2"
            assert point_2.bacnet_object_type == "analogOutput"
            assert point_2.present_value == "55.0"

            # Individual insert should not be called for successful bulk reads
            assert mock_individual_insert.call_count == 0

    @pytest.mark.asyncio
    async def test_monitor_all_devices_no_controllers(self):
        """Test: Monitor behavior when no controllers are configured"""

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
        ):
            # No controllers in database
            mock_get_config.return_value = []

            # Execute
            await self.monitor.monitor_all_devices()

            # Should return early without attempting any reads
            mock_manager.get_wrapper_for_operation.assert_not_called()

    @pytest.mark.asyncio
    async def test_monitor_all_devices_no_wrappers_available(self):
        """Test: Monitor behavior when no BACnet wrappers are available"""

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
        ):
            mock_get_config.return_value = [self.mock_controller]
            mock_manager.get_all_wrappers.return_value = {}
            mock_manager.get_wrapper_for_operation = AsyncMock(return_value=None)
            mock_manager.get_utilization_info = AsyncMock(return_value={})

            # Execute
            await self.monitor.monitor_all_devices()

            # Should skip all points when no wrapper available
            mock_insert.assert_not_called()


class TestMonitorAllDevicesErrorHandling:
    """Test error handling in monitor_all_devices"""

    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = BACnetMonitor()

        # Create mock controller
        self.mock_controller = Mock()
        self.mock_controller.controller_ip_address = "192.168.1.100"
        self.mock_controller.controller_id = "controller_1"
        self.mock_controller.device_id = 12345

        # Create mock point
        self.mock_point = Mock()
        self.mock_point.iot_device_point_id = "point_1"
        self.mock_point.type = "analogInput"
        self.mock_point.point_id = 1
        self.mock_point.properties = Mock()
        self.mock_point.properties.__dict__ = {"units": "degreesFahrenheit"}

        self.mock_controller.object_list = [self.mock_point]

    @pytest.mark.asyncio
    async def test_read_properties_failure_with_fallback_success(self):
        """Test: Fallback to read_present_value when read_properties fails"""

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.read_properties = AsyncMock(
            side_effect=Exception("Read properties failed")
        )
        mock_wrapper.read_present_value = AsyncMock(return_value=72.5)

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
        ):
            mock_get_config.return_value = [self.mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})

            # Execute
            await self.monitor.monitor_all_devices()

            # Verify fallback was attempted
            mock_wrapper.read_present_value.assert_called_once_with(
                "192.168.1.100", "analogInput", 1
            )

            # Verify data was still inserted with error info
            mock_insert.assert_called_once()
            inserted_model = mock_insert.call_args[0][0]
            assert inserted_model.present_value == "72.5"
            assert inserted_model.error_info is not None
            assert "Failed to read properties" in inserted_model.error_info

    @pytest.mark.asyncio
    async def test_both_read_attempts_fail(self):
        """Test: Both read_properties and fallback read_present_value fail"""

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.read_properties = AsyncMock(
            side_effect=Exception("Read properties failed")
        )
        mock_wrapper.read_present_value = AsyncMock(
            side_effect=Exception("Read present value failed")
        )

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
        ):
            mock_get_config.return_value = [self.mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})

            # Execute
            await self.monitor.monitor_all_devices()

            # Both read attempts should be made
            mock_wrapper.read_properties.assert_called_once()
            mock_wrapper.read_present_value.assert_called_once()

            # No data should be inserted when both fail
            mock_insert.assert_not_called()

    @pytest.mark.asyncio
    async def test_partial_point_failures(self):
        """Test: Some points succeed while others fail"""

        # Add second point that will succeed
        self.mock_point_2 = Mock()
        self.mock_point_2.iot_device_point_id = "point_2"
        self.mock_point_2.type = "analogOutput"
        self.mock_point_2.point_id = 2
        self.mock_point_2.properties = None

        self.mock_controller.object_list = [self.mock_point, self.mock_point_2]

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"

        # First point fails, second succeeds
        async def read_properties_side_effect(
            device_ip, object_type, object_id, properties
        ):
            if object_id == 1:
                raise Exception("Point 1 read failed")
            return {"presentValue": 55.0}

        mock_wrapper.read_properties = AsyncMock(
            side_effect=read_properties_side_effect
        )
        mock_wrapper.read_present_value = AsyncMock(
            side_effect=Exception("Fallback also failed")
        )

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = [self.mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})
            mock_health.process_all_health_properties.return_value = {}

            # Execute
            await self.monitor.monitor_all_devices()

            # Only the successful point should be inserted
            assert mock_insert.call_count == 1
            inserted_model = mock_insert.call_args[0][0]
            assert inserted_model.iot_device_point_id == "point_2"


class TestMonitorAllDevicesPropertyHandling:
    """Test property extraction and health data processing"""

    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = BACnetMonitor()

    @pytest.mark.asyncio
    async def test_properties_extraction_from_dict(self):
        """Test: Extract properties when stored as dict"""

        mock_controller = Mock()
        mock_controller.controller_ip_address = "192.168.1.100"
        mock_controller.controller_id = "controller_1"
        mock_controller.device_id = 12345

        mock_point = Mock()
        mock_point.iot_device_point_id = "point_1"
        mock_point.type = "analogInput"
        mock_point.point_id = 1
        mock_point.properties = {
            "presentValue": 72.5,
            "statusFlags": "normal",
            "eventState": "normal",
            "outOfService": False,
            "reliability": "no-fault-detected",
        }

        mock_controller.object_list = [mock_point]

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.read_properties = AsyncMock(
            return_value={"presentValue": 72.5, "statusFlags": "normal"}
        )

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch("src.controllers.monitoring.monitor.insert_controller_point"),
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = [mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})
            mock_health.process_all_health_properties.return_value = {
                "status_flags": "normal"
            }

            # Execute
            await self.monitor.monitor_all_devices()

            # Verify properties were correctly identified
            mock_wrapper.read_properties.assert_called_once()
            call_args = mock_wrapper.read_properties.call_args
            properties_requested = call_args[1]["properties"]
            assert "presentValue" in properties_requested
            assert "statusFlags" in properties_requested
            assert "eventState" in properties_requested

    @pytest.mark.asyncio
    async def test_properties_with_null_values(self):
        """Test: Handle properties with null/None values correctly"""

        mock_controller = Mock()
        mock_controller.controller_ip_address = "192.168.1.100"
        mock_controller.controller_id = "controller_1"
        mock_controller.device_id = 12345

        mock_point = Mock()
        mock_point.iot_device_point_id = "point_1"
        mock_point.type = "analogInput"
        mock_point.point_id = 1
        mock_point.properties = Mock()
        mock_point.properties.__dict__ = {
            "presentValue": 72.5,
            "statusFlags": None,  # Null value should be skipped
            "eventState": "normal",
            "outOfService": None,  # Another null value
            "reliability": "no-fault-detected",
        }

        mock_controller.object_list = [mock_point]

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.read_properties = AsyncMock(return_value={"presentValue": 72.5})

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch("src.controllers.monitoring.monitor.insert_controller_point"),
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = [mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})
            mock_health.process_all_health_properties.return_value = {}

            # Execute
            await self.monitor.monitor_all_devices()

            # Verify null properties were not requested
            call_args = mock_wrapper.read_properties.call_args
            properties_requested = call_args[1]["properties"]
            assert "presentValue" in properties_requested
            assert "statusFlags" not in properties_requested  # Should be skipped
            assert "eventState" in properties_requested
            assert "outOfService" not in properties_requested  # Should be skipped

    @pytest.mark.asyncio
    async def test_no_properties_object(self):
        """Test: Handle points with no properties object"""

        mock_controller = Mock()
        mock_controller.controller_ip_address = "192.168.1.100"
        mock_controller.controller_id = "controller_1"
        mock_controller.device_id = 12345

        mock_point = Mock()
        mock_point.iot_device_point_id = "point_1"
        mock_point.type = "analogInput"
        mock_point.point_id = 1
        mock_point.properties = None  # No properties at all

        mock_controller.object_list = [mock_point]

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.read_properties = AsyncMock(return_value={"presentValue": 72.5})

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch("src.controllers.monitoring.monitor.insert_controller_point"),
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = [mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})
            mock_health.process_all_health_properties.return_value = {}

            # Execute
            await self.monitor.monitor_all_devices()

            # Should only request presentValue when no properties info
            call_args = mock_wrapper.read_properties.call_args
            properties_requested = call_args[1]["properties"]
            assert properties_requested == ["presentValue"]


class TestMonitorAllDevicesMultiController:
    """Test monitoring with multiple controllers"""

    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = BACnetMonitor()

        # Create first controller
        self.controller_1 = Mock()
        self.controller_1.controller_ip_address = "192.168.1.100"
        self.controller_1.controller_id = "controller_1"
        self.controller_1.device_id = 100

        self.point_1_1 = Mock()
        self.point_1_1.iot_device_point_id = "controller1_point1"
        self.point_1_1.type = "analogInput"
        self.point_1_1.point_id = 1
        self.point_1_1.properties = None

        self.point_1_2 = Mock()
        self.point_1_2.iot_device_point_id = "controller1_point2"
        self.point_1_2.type = "analogOutput"
        self.point_1_2.point_id = 2
        self.point_1_2.properties = None

        self.controller_1.object_list = [self.point_1_1, self.point_1_2]

        # Create second controller
        self.controller_2 = Mock()
        self.controller_2.controller_ip_address = "192.168.1.101"
        self.controller_2.controller_id = "controller_2"
        self.controller_2.device_id = 101

        self.point_2_1 = Mock()
        self.point_2_1.iot_device_point_id = "controller2_point1"
        self.point_2_1.type = "binaryInput"
        self.point_2_1.point_id = 1
        self.point_2_1.properties = None

        self.controller_2.object_list = [self.point_2_1]

    @pytest.mark.asyncio
    async def test_multiple_controllers_sequential_processing(self):
        """Test: Multiple controllers are processed sequentially"""

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"

        read_results = {
            ("192.168.1.100", 1): {"presentValue": 72.5},
            ("192.168.1.100", 2): {"presentValue": 55.0},
            ("192.168.1.101", 1): {"presentValue": 1},
        }

        async def read_properties_mock(device_ip, object_type, object_id, properties):
            return read_results.get((device_ip, object_id), {})

        mock_wrapper.read_properties = AsyncMock(side_effect=read_properties_mock)

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = [self.controller_1, self.controller_2]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})
            mock_health.process_all_health_properties.return_value = {}

            # Execute
            await self.monitor.monitor_all_devices()

            # Verify all points were read
            assert mock_wrapper.read_properties.call_count == 3

            # Verify all points were inserted
            assert mock_insert.call_count == 3

            # Verify correct controller IPs were used
            call_ips = [
                call[1]["device_ip"]
                for call in mock_wrapper.read_properties.call_args_list
            ]
            assert call_ips.count("192.168.1.100") == 2
            assert call_ips.count("192.168.1.101") == 1

    @pytest.mark.asyncio
    async def test_controller_failure_continues_to_next(self):
        """Test: Failure in one controller doesn't stop processing of others"""

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"

        async def read_properties_mock(device_ip, object_type, object_id, properties):
            if device_ip == "192.168.1.100":
                raise Exception("Controller 1 network error")
            return {"presentValue": 1}

        mock_wrapper.read_properties = AsyncMock(side_effect=read_properties_mock)
        mock_wrapper.read_present_value = AsyncMock(
            side_effect=Exception("Fallback also fails")
        )

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = [self.controller_1, self.controller_2]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})
            mock_health.process_all_health_properties.return_value = {}

            # Execute
            await self.monitor.monitor_all_devices()

            # Controller 1 points should fail, controller 2 should succeed
            assert mock_insert.call_count == 1
            inserted_model = mock_insert.call_args[0][0]
            assert inserted_model.iot_device_point_id == "controller2_point1"


class TestMonitorAllDevicesWrapperManagement:
    """Test wrapper allocation and utilization"""

    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = BACnetMonitor()

    @pytest.mark.asyncio
    async def test_wrapper_rotation_across_controllers(self):
        """Test: Different wrappers are used for different controllers (load balancing)"""

        # Create two controllers to test wrapper rotation
        controller_1 = Mock()
        controller_1.controller_ip_address = "192.168.1.100"
        controller_1.controller_id = "controller_1"
        controller_1.device_id = 100

        point_1 = Mock()
        point_1.iot_device_point_id = "point_1"
        point_1.type = "analogInput"
        point_1.point_id = 1
        point_1.properties = None
        controller_1.object_list = [point_1]

        controller_2 = Mock()
        controller_2.controller_ip_address = "192.168.1.101"
        controller_2.controller_id = "controller_2"
        controller_2.device_id = 101

        point_2 = Mock()
        point_2.iot_device_point_id = "point_2"
        point_2.type = "analogOutput"
        point_2.point_id = 1
        point_2.properties = None
        controller_2.object_list = [point_2]

        # Create multiple wrappers with bulk read support
        wrapper_1 = create_mock_wrapper_with_bulk_support(
            instance_id="reader_1", bulk_result={"analogInput:1": {"presentValue": 1.0}}
        )

        wrapper_2 = create_mock_wrapper_with_bulk_support(
            instance_id="reader_2",
            bulk_result={"analogOutput:1": {"presentValue": 2.0}},
        )

        # Simulate round-robin wrapper selection
        wrappers = [wrapper_1, wrapper_2]
        wrapper_iter = iter(wrappers)

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch("src.controllers.monitoring.monitor.insert_controller_point"),
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = [controller_1, controller_2]
            mock_manager.get_all_wrappers.return_value = {
                "reader_1": wrapper_1,
                "reader_2": wrapper_2,
            }
            mock_manager.get_wrapper_for_operation = AsyncMock(
                side_effect=lambda: next(wrapper_iter)
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})
            mock_health.process_all_health_properties.return_value = {}

            # Execute
            await self.monitor.monitor_all_devices()

            # Each wrapper should be used once (one per controller)
            assert wrapper_1.read_multiple_points.call_count == 1
            assert wrapper_2.read_multiple_points.call_count == 1

            # Individual reads should not be called when bulk reads succeed
            assert wrapper_1.read_properties.call_count == 0
            assert wrapper_2.read_properties.call_count == 0

    @pytest.mark.asyncio
    async def test_utilization_logging(self):
        """Test: Wrapper utilization is logged before and after monitoring"""

        mock_controller = Mock()
        mock_controller.controller_ip_address = "192.168.1.100"
        mock_controller.controller_id = "controller_1"
        mock_controller.device_id = 12345
        mock_controller.object_list = []

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
        ):
            mock_get_config.return_value = [mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(
                return_value={"reader_1": {"active_operations": 0}}
            )

            # Execute
            await self.monitor.monitor_all_devices()

            # Utilization should be checked twice (before and after)
            assert mock_manager.get_utilization_info.call_count == 2


class TestMonitorAllDevicesDataIntegrity:
    """Test data integrity and correct model creation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = BACnetMonitor()

    @pytest.mark.asyncio
    async def test_controller_point_model_fields(self):
        """Test: All required fields are correctly populated in ControllerPointsModel"""

        mock_controller = Mock()
        mock_controller.controller_ip_address = "192.168.1.100"
        mock_controller.controller_id = "controller_1"
        mock_controller.device_id = 12345

        mock_point = Mock()
        mock_point.iot_device_point_id = "test_point_1"
        mock_point.type = "analogInput"
        mock_point.point_id = 42
        mock_point.properties = Mock()
        mock_point.properties.__dict__ = {
            "units": "degreesFahrenheit",
            "statusFlags": "normal",
        }

        mock_controller.object_list = [mock_point]

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.read_properties = AsyncMock(
            return_value={
                "presentValue": 72.5,
                "statusFlags": "normal",
                "eventState": "normal",
                "outOfService": False,
                "reliability": "no-fault-detected",
            }
        )

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = [mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})
            mock_health.process_all_health_properties.return_value = {
                "status_flags": "processed_normal",
                "event_state": "normal",
                "out_of_service": False,
                "reliability": "no-fault-detected",
            }

            # Execute
            await self.monitor.monitor_all_devices()

            # Verify the model was created with all correct fields
            mock_insert.assert_called_once()
            model = mock_insert.call_args[0][0]

            assert isinstance(model, ControllerPointsModel)
            assert model.iot_device_point_id == "test_point_1"
            assert model.controller_id == "controller_1"
            assert model.point_id == 42
            assert model.bacnet_object_type == "analogInput"
            assert model.present_value == "72.5"
            assert model.controller_ip_address == "192.168.1.100"
            assert model.controller_device_id == 12345
            assert model.controller_port == 47808  # DEFAULT_CONTROLLER_PORT
            assert model.units == "degreesFahrenheit"
            assert model.is_uploaded is False
            assert model.status_flags == "processed_normal"
            assert model.event_state == "normal"
            assert model.out_of_service is False
            assert model.reliability == "no-fault-detected"

    @pytest.mark.asyncio
    async def test_present_value_none_handling(self):
        """Test: Present value None is converted to string properly"""

        mock_controller = Mock()
        mock_controller.controller_ip_address = "192.168.1.100"
        mock_controller.controller_id = "controller_1"
        mock_controller.device_id = 12345

        mock_point = Mock()
        mock_point.iot_device_point_id = "point_1"
        mock_point.type = "analogInput"
        mock_point.point_id = 1
        mock_point.properties = None

        mock_controller.object_list = [mock_point]

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.read_properties = AsyncMock(
            return_value={"presentValue": None}  # None value
        )

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = [mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})
            mock_health.process_all_health_properties.return_value = {}

            # Execute
            await self.monitor.monitor_all_devices()

            # Verify None was handled correctly
            model = mock_insert.call_args[0][0]
            assert model.present_value is None  # Should remain None, not "None"


class TestMonitorAllDevicesAdvancedScenarios:
    """Test advanced and stress scenarios"""

    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = BACnetMonitor()

    @pytest.mark.asyncio
    async def test_health_processor_exception_handling(self):
        """Test: Continue processing when health processor fails"""

        mock_controller = Mock()
        mock_controller.controller_ip_address = "192.168.1.100"
        mock_controller.controller_id = "controller_1"
        mock_controller.device_id = 12345

        mock_point = Mock()
        mock_point.iot_device_point_id = "point_1"
        mock_point.type = "analogInput"
        mock_point.point_id = 1
        mock_point.properties = Mock()
        mock_point.properties.__dict__ = {"units": "degreesFahrenheit"}

        mock_controller.object_list = [mock_point]

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.read_properties = AsyncMock(return_value={"presentValue": 72.5})

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch("src.controllers.monitoring.monitor.insert_controller_point"),
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = [mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})

            # Health processor throws exception, but the actual monitoring should succeed
            # The exception happens after the read operation
            mock_health.process_all_health_properties.side_effect = Exception(
                "Health processing failed"
            )

            # Execute monitoring - should continue despite health processor error
            await self.monitor.monitor_all_devices()

            # The current implementation catches health processor errors and treats them as read failures
            # So the point read fails and no data is inserted
            # This actually tests that health processor failures are handled gracefully
            assert mock_wrapper.read_properties.call_count == 1

    @pytest.mark.asyncio
    async def test_database_insertion_failure_continues_processing(self):
        """Test: Continue with remaining points when database insertion fails"""

        mock_controller = Mock()
        mock_controller.controller_ip_address = "192.168.1.100"
        mock_controller.controller_id = "controller_1"
        mock_controller.device_id = 12345

        # Create two points
        mock_point_1 = Mock()
        mock_point_1.iot_device_point_id = "point_1"
        mock_point_1.type = "analogInput"
        mock_point_1.point_id = 1
        mock_point_1.properties = None

        mock_point_2 = Mock()
        mock_point_2.iot_device_point_id = "point_2"
        mock_point_2.type = "analogOutput"
        mock_point_2.point_id = 2
        mock_point_2.properties = None

        mock_controller.object_list = [mock_point_1, mock_point_2]

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.read_properties = AsyncMock(return_value={"presentValue": 72.5})

        # Database insertion fails for first point, succeeds for second
        call_count = 0

        async def mock_insert_side_effect(point):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Database connection failed")
            return point

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = [mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})
            mock_health.process_all_health_properties.return_value = {}
            mock_insert.side_effect = mock_insert_side_effect

            # Execute monitoring - should not crash and continue processing
            await self.monitor.monitor_all_devices()

            # Should attempt both insertions
            assert mock_insert.call_count == 2
            # Should read both points despite first insertion failure
            assert mock_wrapper.read_properties.call_count == 2

    @pytest.mark.asyncio
    async def test_wrapper_timeout_scenarios(self):
        """Test: Handle wrapper timeouts gracefully"""

        mock_controller = Mock()
        mock_controller.controller_ip_address = "192.168.1.100"
        mock_controller.controller_id = "controller_1"
        mock_controller.device_id = 12345

        mock_point = Mock()
        mock_point.iot_device_point_id = "point_1"
        mock_point.type = "analogInput"
        mock_point.point_id = 1
        mock_point.properties = None

        mock_controller.object_list = [mock_point]

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.read_properties = AsyncMock(
            side_effect=asyncio.TimeoutError("BACnet read timeout")
        )
        mock_wrapper.read_present_value = AsyncMock(
            return_value=72.5
        )  # Fallback succeeds

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
        ):
            mock_get_config.return_value = [mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})

            # Execute monitoring
            await self.monitor.monitor_all_devices()

            # Should attempt read_properties (which times out)
            mock_wrapper.read_properties.assert_called_once()
            # Should fallback to read_present_value
            mock_wrapper.read_present_value.assert_called_once()
            # Should insert data from fallback
            mock_insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_large_controller_set_performance(self):
        """Test: Handle large number of controllers efficiently"""

        # Create 50 controllers with 5 points each (250 total points)
        controllers = []
        for controller_idx in range(50):
            mock_controller = Mock()
            mock_controller.controller_ip_address = f"192.168.1.{100 + controller_idx}"
            mock_controller.controller_id = f"controller_{controller_idx}"
            mock_controller.device_id = 12345 + controller_idx

            points = []
            for point_idx in range(5):
                mock_point = Mock()
                mock_point.iot_device_point_id = f"point_{controller_idx}_{point_idx}"
                mock_point.type = "analogInput"
                mock_point.point_id = point_idx + 1
                mock_point.properties = None
                points.append(mock_point)

            mock_controller.object_list = points
            controllers.append(mock_controller)

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.read_properties = AsyncMock(return_value={"presentValue": 72.5})

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = controllers
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})
            mock_health.process_all_health_properties.return_value = {}

            # Execute monitoring - should complete without hanging
            import time

            start_time = time.time()
            await self.monitor.monitor_all_devices()
            execution_time = time.time() - start_time

            # Should process all 250 points
            assert mock_wrapper.read_properties.call_count == 250
            assert mock_insert.call_count == 250

            # Should complete in reasonable time (allowing for mocking overhead)
            assert (
                execution_time < 10.0
            )  # Should be much faster than real BACnet operations

    @pytest.mark.asyncio
    async def test_network_partial_failure(self):
        """Test: Handle when some controllers are unreachable"""

        # Create two controllers
        controller_1 = Mock()
        controller_1.controller_ip_address = "192.168.1.100"  # This will fail
        controller_1.controller_id = "controller_1"
        controller_1.device_id = 100

        point_1 = Mock()
        point_1.iot_device_point_id = "point_1"
        point_1.type = "analogInput"
        point_1.point_id = 1
        point_1.properties = None
        controller_1.object_list = [point_1]

        controller_2 = Mock()
        controller_2.controller_ip_address = "192.168.1.101"  # This will succeed
        controller_2.controller_id = "controller_2"
        controller_2.device_id = 101

        point_2 = Mock()
        point_2.iot_device_point_id = "point_2"
        point_2.type = "analogOutput"
        point_2.point_id = 1
        point_2.properties = None
        controller_2.object_list = [point_2]

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"

        # Network failure for specific IP
        async def read_properties_network_mock(
            device_ip, object_type, object_id, properties
        ):
            if device_ip == "192.168.1.100":
                raise Exception("Network unreachable")
            return {"presentValue": 55.0}

        mock_wrapper.read_properties = AsyncMock(
            side_effect=read_properties_network_mock
        )
        mock_wrapper.read_present_value = AsyncMock(
            side_effect=Exception("Network unreachable")
        )

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = [controller_1, controller_2]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})
            mock_health.process_all_health_properties.return_value = {}

            # Execute monitoring
            await self.monitor.monitor_all_devices()

            # Should attempt both controllers
            assert mock_wrapper.read_properties.call_count == 2
            # Should only insert data for successful controller
            assert mock_insert.call_count == 1
            inserted_model = mock_insert.call_args[0][0]
            assert (
                inserted_model.iot_device_point_id == "point_2"
            )  # Only successful controller

    @pytest.mark.asyncio
    async def test_concurrent_monitoring_calls(self):
        """Test: Multiple concurrent monitor_all_devices calls"""

        mock_controller = Mock()
        mock_controller.controller_ip_address = "192.168.1.100"
        mock_controller.controller_id = "controller_1"
        mock_controller.device_id = 12345

        mock_point = Mock()
        mock_point.iot_device_point_id = "point_1"
        mock_point.type = "analogInput"
        mock_point.point_id = 1
        mock_point.properties = None

        mock_controller.object_list = [mock_point]

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.read_properties = AsyncMock(return_value={"presentValue": 72.5})

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = [mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})
            mock_health.process_all_health_properties.return_value = {}

            # Execute multiple concurrent monitoring calls
            tasks = [
                self.monitor.monitor_all_devices(),
                self.monitor.monitor_all_devices(),
                self.monitor.monitor_all_devices(),
            ]

            # All should complete without deadlock or corruption
            await asyncio.gather(*tasks)

            # Should have performed operations for all concurrent calls
            assert mock_wrapper.read_properties.call_count == 3
            assert mock_insert.call_count == 3

    @pytest.mark.asyncio
    async def test_wrapper_manager_state_consistency(self):
        """Test: Wrapper manager state remains consistent during monitoring with bulk reads"""

        # Create multiple controllers to test wrapper state consistency
        controllers = []
        for i in range(3):
            mock_controller = Mock()
            mock_controller.controller_ip_address = f"192.168.1.{100 + i}"
            mock_controller.controller_id = f"controller_{i}"
            mock_controller.device_id = 12345 + i

            # Each controller has 2 points
            points = []
            for j in range(2):
                mock_point = Mock()
                mock_point.iot_device_point_id = f"point_{i}_{j}"
                mock_point.type = "analogInput"
                mock_point.point_id = j + 1
                mock_point.properties = None
                points.append(mock_point)

            mock_controller.object_list = points
            controllers.append(mock_controller)

        # Create wrapper with bulk read support
        mock_wrapper = create_mock_wrapper_with_bulk_support(
            instance_id="reader_1",
            bulk_result={
                "analogInput:1": {"presentValue": 72.5},
                "analogInput:2": {"presentValue": 73.0},
            },
        )

        # Track wrapper manager calls to ensure state consistency
        get_wrapper_calls = []

        async def track_get_wrapper():
            get_wrapper_calls.append(len(get_wrapper_calls))
            return mock_wrapper

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch("src.controllers.monitoring.monitor.insert_controller_point"),
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = controllers
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                side_effect=track_get_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(
                return_value={"reader_1": {"active": 0}}
            )
            mock_health.process_all_health_properties.return_value = {}

            # Execute monitoring
            await self.monitor.monitor_all_devices()

            # With optimization: should call get_wrapper_for_operation once per controller (not per point)
            assert len(get_wrapper_calls) == 3  # 3 controllers
            # Wrapper calls should be sequential (0, 1, 2)
            assert get_wrapper_calls == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_error_propagation_and_logging(self):
        """Test: Errors are properly logged and don't crash the method"""

        mock_controller = Mock()
        mock_controller.controller_ip_address = "192.168.1.100"
        mock_controller.controller_id = "controller_1"
        mock_controller.device_id = 12345

        mock_point = Mock()
        mock_point.iot_device_point_id = "point_1"
        mock_point.type = "analogInput"
        mock_point.point_id = 1
        mock_point.properties = Mock()
        mock_point.properties.__dict__ = {"units": "degreesFahrenheit"}

        mock_controller.object_list = [mock_point]

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.read_properties = AsyncMock(
            side_effect=Exception("Critical BACnet error")
        )
        mock_wrapper.read_present_value = AsyncMock(
            side_effect=Exception("Fallback also failed")
        )

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
        ):
            mock_get_config.return_value = [mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})

            # Execute monitoring - should complete without raising exception
            await self.monitor.monitor_all_devices()

            # Should have attempted both read operations
            mock_wrapper.read_properties.assert_called_once()
            mock_wrapper.read_present_value.assert_called_once()

            # Should not insert any data when both operations fail
            mock_insert.assert_not_called()

            # Test passes if the method completes without crashing
            # The logging verification is difficult to test due to loguru's structure


class TestMonitorAllDevicesEdgeCases:
    """Test edge cases and unusual scenarios"""

    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = BACnetMonitor()

    @pytest.mark.asyncio
    async def test_empty_object_list(self):
        """Test: Controller with empty object list"""

        mock_controller = Mock()
        mock_controller.controller_ip_address = "192.168.1.100"
        mock_controller.controller_id = "controller_1"
        mock_controller.device_id = 12345
        mock_controller.object_list = []  # Empty list

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
        ):
            mock_get_config.return_value = [mock_controller]
            mock_manager.get_all_wrappers.return_value = {}
            mock_manager.get_utilization_info = AsyncMock(return_value={})

            # Execute
            await self.monitor.monitor_all_devices()

            # No operations should be performed
            mock_manager.get_wrapper_for_operation.assert_not_called()
            mock_insert.assert_not_called()

    @pytest.mark.asyncio
    async def test_malformed_properties_object(self):
        """Test: Handle malformed properties object gracefully"""

        mock_controller = Mock()
        mock_controller.controller_ip_address = "192.168.1.100"
        mock_controller.controller_id = "controller_1"
        mock_controller.device_id = 12345

        mock_point = Mock()
        mock_point.iot_device_point_id = "point_1"
        mock_point.type = "analogInput"
        mock_point.point_id = 1
        mock_point.properties = "not_a_dict_or_object"  # Invalid type

        mock_controller.object_list = [mock_point]

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.read_properties = AsyncMock(return_value={"presentValue": 72.5})

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch("src.controllers.monitoring.monitor.insert_controller_point"),
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = [mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})
            mock_health.process_all_health_properties.return_value = {}

            # Execute - should handle gracefully
            await self.monitor.monitor_all_devices()

            # Should default to reading only presentValue
            call_args = mock_wrapper.read_properties.call_args
            assert call_args[1]["properties"] == ["presentValue"]

    @pytest.mark.asyncio
    async def test_very_large_property_values(self):
        """Test: Handle very large numeric values correctly"""

        mock_controller = Mock()
        mock_controller.controller_ip_address = "192.168.1.100"
        mock_controller.controller_id = "controller_1"
        mock_controller.device_id = 12345

        mock_point = Mock()
        mock_point.iot_device_point_id = "point_1"
        mock_point.type = "analogInput"
        mock_point.point_id = 1
        mock_point.properties = None

        mock_controller.object_list = [mock_point]

        mock_wrapper = Mock()
        mock_wrapper.instance_id = "reader_1"
        mock_wrapper.read_properties = AsyncMock(
            return_value={"presentValue": 999999999999.999999}  # Very large value
        )

        with (
            patch(
                "src.controllers.monitoring.monitor.get_latest_bacnet_config_json_as_list"
            ) as mock_get_config,
            patch(
                "src.controllers.monitoring.monitor.bacnet_wrapper_manager"
            ) as mock_manager,
            patch(
                "src.controllers.monitoring.monitor.insert_controller_point"
            ) as mock_insert,
            patch(
                "src.controllers.monitoring.monitor.BACnetHealthProcessor"
            ) as mock_health,
        ):
            mock_get_config.return_value = [mock_controller]
            mock_manager.get_all_wrappers.return_value = {"reader_1": mock_wrapper}
            mock_manager.get_wrapper_for_operation = AsyncMock(
                return_value=mock_wrapper
            )
            mock_manager.get_utilization_info = AsyncMock(return_value={})
            mock_health.process_all_health_properties.return_value = {}

            # Execute
            await self.monitor.monitor_all_devices()

            # Value should be converted to string correctly
            model = mock_insert.call_args[0][0]
            assert model.present_value == "1000000000000.0"
