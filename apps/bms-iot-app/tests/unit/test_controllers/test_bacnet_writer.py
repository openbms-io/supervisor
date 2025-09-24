"""
Test BACnet writer controller logic.

User Story: As a developer, I want write operations to be reliable
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from src.actors.messages.message_type import (
    SetValueToPointRequestPayload,
    SetValueToPointResponsePayload,
)
from src.controllers.bacnet_writer.writer import BACnetWriter


class TestBACnetWriter:
    """Test BACnetWriter class functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.writer = BACnetWriter()

    def test_bacnet_writer_initialization(self):
        """Test: BACnetWriter initializes correctly"""
        writer = BACnetWriter()

        # BACnetWriter should have access to wrapper manager
        assert writer.bacnet_wrapper_manager is not None
        assert hasattr(writer, "start")
        assert hasattr(writer, "write_value_to_point")

    @pytest.mark.asyncio
    async def test_start_method_compatibility(self):
        """Test: Start method exists for initialization compatibility"""
        # Should not raise any exceptions
        await self.writer.start()

        # Since it's a no-op method, just verify it completes
        assert True

    @pytest.mark.asyncio
    async def test_write_value_to_point_success(self):
        """Test: Successful write value to point operation"""
        # Create test request payload
        request_payload = SetValueToPointRequestPayload(
            iotDevicePointId="point_123",
            pointInstanceId="instance_456",
            controllerId="controller_789",
            presentValue=25.5,
            commandId="cmd_001",
            commandType="set_value_to_point",
        )

        # Mock the private methods
        mock_controller = Mock()
        mock_object = Mock()
        mock_db_record = Mock()

        with (
            patch.object(
                self.writer,
                "_find_target_point",
                return_value=(mock_controller, mock_object),
            ) as mock_find,
            patch.object(
                self.writer, "_perform_write_operation", return_value=25.5
            ) as mock_write,
            patch.object(
                self.writer, "_create_database_record", return_value=mock_db_record
            ) as mock_db,
        ):
            response, db_record = await self.writer.write_value_to_point(
                request_payload
            )

            # Verify private methods were called
            mock_find.assert_called_once_with("controller_789", "instance_456")
            mock_write.assert_called_once_with(mock_controller, mock_object, 25.5)
            mock_db.assert_called_once_with(
                request_payload, 25.5, mock_controller, mock_object
            )

            # Verify successful response
            assert isinstance(response, SetValueToPointResponsePayload)
            assert response.success is True
            assert "Successfully wrote value 25.5" in response.message
            assert response.commandId == "cmd_001"

            # Verify database record is returned
            assert db_record == mock_db_record

    @pytest.mark.asyncio
    async def test_write_value_to_point_find_target_error(self):
        """Test: Write operation handles target point not found error"""
        request_payload = SetValueToPointRequestPayload(
            iotDevicePointId="invalid_point",
            pointInstanceId="invalid_instance",
            controllerId="invalid_controller",
            presentValue=30.0,
            commandId="cmd_002",
            commandType="set_value_to_point",
        )

        with patch.object(
            self.writer, "_find_target_point", side_effect=Exception("Point not found")
        ) as mock_find:
            response, db_record = await self.writer.write_value_to_point(
                request_payload
            )

            # Verify error response
            assert isinstance(response, SetValueToPointResponsePayload)
            assert response.success is False
            assert "Point not found" in response.message
            assert response.commandId == "cmd_002"

            # Verify no database record on error
            assert db_record is None

            # Verify find method was called
            mock_find.assert_called_once_with("invalid_controller", "invalid_instance")

    @pytest.mark.asyncio
    async def test_write_value_to_point_write_operation_error(self):
        """Test: Write operation handles BACnet write failure"""
        request_payload = SetValueToPointRequestPayload(
            iotDevicePointId="point_123",
            pointInstanceId="instance_456",
            controllerId="controller_789",
            presentValue=40.0,
            commandId="cmd_003",
            commandType="set_value_to_point",
        )

        mock_controller = Mock()
        mock_object = Mock()

        with (
            patch.object(
                self.writer,
                "_find_target_point",
                return_value=(mock_controller, mock_object),
            ) as mock_find,
            patch.object(
                self.writer,
                "_perform_write_operation",
                side_effect=Exception("BACnet write failed"),
            ) as mock_write,
        ):
            response, db_record = await self.writer.write_value_to_point(
                request_payload
            )

            # Verify error handling
            assert response.success is False
            assert "BACnet write failed" in response.message
            assert response.commandId == "cmd_003"
            assert db_record is None

            # Verify methods were called in correct order
            mock_find.assert_called_once_with("controller_789", "instance_456")
            mock_write.assert_called_once_with(mock_controller, mock_object, 40.0)

    @pytest.mark.asyncio
    async def test_write_value_to_point_database_error(self):
        """Test: Write operation handles database record creation error"""
        request_payload = SetValueToPointRequestPayload(
            iotDevicePointId="point_123",
            pointInstanceId="instance_456",
            controllerId="controller_789",
            presentValue=35.0,
            commandId="cmd_004",
            commandType="set_value_to_point",
        )

        mock_controller = Mock()
        mock_object = Mock()

        with (
            patch.object(
                self.writer,
                "_find_target_point",
                return_value=(mock_controller, mock_object),
            ),
            patch.object(self.writer, "_perform_write_operation", return_value=35.0),
            patch.object(
                self.writer,
                "_create_database_record",
                side_effect=Exception("Database error"),
            ),
        ):
            response, db_record = await self.writer.write_value_to_point(
                request_payload
            )

            # Should still return error response due to database failure
            assert response.success is False
            assert "Database error" in response.message
            assert db_record is None

    @pytest.mark.asyncio
    async def test_write_value_different_data_types(self):
        """Test: Write operations with different value types"""
        test_cases = [
            (25.5, "float"),
            (30, "integer"),
            (0, "zero"),
            (-15.2, "negative"),
        ]

        mock_controller = Mock()
        mock_object = Mock()
        mock_db_record = Mock()

        for value, description in test_cases:
            request_payload = SetValueToPointRequestPayload(
                iotDevicePointId=f"point_{description}",
                pointInstanceId="instance_test",
                controllerId="controller_test",
                presentValue=value,
                commandId=f"cmd_{description}",
                commandType="set_value_to_point",
            )

            with (
                patch.object(
                    self.writer,
                    "_find_target_point",
                    return_value=(mock_controller, mock_object),
                ),
                patch.object(
                    self.writer, "_perform_write_operation", return_value=value
                ),
                patch.object(
                    self.writer, "_create_database_record", return_value=mock_db_record
                ),
            ):
                response, db_record = await self.writer.write_value_to_point(
                    request_payload
                )

                # Verify successful write for each data type
                assert response.success is True
                assert f"Successfully wrote value {value}" in response.message
                assert response.commandId == f"cmd_{description}"
                assert db_record == mock_db_record

    @pytest.mark.asyncio
    async def test_write_value_with_state_text(self):
        """Test: Write operations with state text array"""
        request_payload = SetValueToPointRequestPayload(
            iotDevicePointId="point_with_states",
            pointInstanceId="instance_states",
            controllerId="controller_states",
            presentValue=1.0,
            stateText=["Off", "On", "Auto"],
            commandId="cmd_states",
            commandType="set_value_to_point",
        )

        mock_controller = Mock()
        mock_object = Mock()
        mock_db_record = Mock()

        with (
            patch.object(
                self.writer,
                "_find_target_point",
                return_value=(mock_controller, mock_object),
            ),
            patch.object(self.writer, "_perform_write_operation", return_value=1.0),
            patch.object(
                self.writer, "_create_database_record", return_value=mock_db_record
            ),
        ):
            response, db_record = await self.writer.write_value_to_point(
                request_payload
            )

            # Verify successful handling of state text
            assert response.success is True
            assert "Successfully wrote value 1.0" in response.message
            assert db_record == mock_db_record


class TestBACnetWriterIntegration:
    """Test BACnetWriter integration with dependencies"""

    def setup_method(self):
        """Set up test fixtures"""
        self.writer = BACnetWriter()

    @pytest.mark.asyncio
    async def test_write_operation_with_wrapper_manager(self):
        """Test: Write operation integrates with BACnet wrapper manager"""
        request_payload = SetValueToPointRequestPayload(
            iotDevicePointId="integration_point",
            pointInstanceId="integration_instance",
            controllerId="integration_controller",
            presentValue=45.0,
            commandId="integration_cmd",
            commandType="set_value_to_point",
        )

        # Mock the wrapper manager
        with patch("src.controllers.bacnet_writer.writer.bacnet_wrapper_manager"):
            # Mock all private methods to focus on integration
            with (
                patch.object(
                    self.writer, "_find_target_point", return_value=(Mock(), Mock())
                ),
                patch.object(
                    self.writer, "_perform_write_operation", return_value=45.0
                ),
                patch.object(
                    self.writer, "_create_database_record", return_value=Mock()
                ),
            ):
                response, db_record = await self.writer.write_value_to_point(
                    request_payload
                )

                # Verify integration works
                assert response.success is True
                assert db_record is not None

    @pytest.mark.asyncio
    async def test_concurrent_write_operations(self):
        """Test: Multiple concurrent write operations"""
        # Create multiple write requests
        requests = []
        for i in range(3):
            request = SetValueToPointRequestPayload(
                iotDevicePointId=f"concurrent_point_{i}",
                pointInstanceId=f"concurrent_instance_{i}",
                controllerId=f"concurrent_controller_{i}",
                presentValue=float(i * 10),
                commandId=f"concurrent_cmd_{i}",
                commandType="set_value_to_point",
            )
            requests.append(request)

        # Mock successful operations for all requests
        with (
            patch.object(
                self.writer, "_find_target_point", return_value=(Mock(), Mock())
            ),
            patch.object(
                self.writer, "_perform_write_operation", side_effect=[0.0, 10.0, 20.0]
            ),
            patch.object(self.writer, "_create_database_record", return_value=Mock()),
        ):
            # Execute concurrent writes
            tasks = [self.writer.write_value_to_point(req) for req in requests]
            results = await asyncio.gather(*tasks)

            # Verify all operations completed successfully
            assert len(results) == 3
            for i, (response, db_record) in enumerate(results):
                assert response.success is True
                assert f"concurrent_cmd_{i}" == response.commandId
                assert db_record is not None

    @pytest.mark.asyncio
    async def test_write_operation_error_isolation(self):
        """Test: One failing write operation doesn't affect others"""
        # Create mixed success/failure requests
        success_request = SetValueToPointRequestPayload(
            iotDevicePointId="success_point",
            pointInstanceId="success_instance",
            controllerId="success_controller",
            presentValue=50.0,
            commandId="success_cmd",
            commandType="set_value_to_point",
        )

        failure_request = SetValueToPointRequestPayload(
            iotDevicePointId="failure_point",
            pointInstanceId="failure_instance",
            controllerId="failure_controller",
            presentValue=60.0,
            commandId="failure_cmd",
            commandType="set_value_to_point",
        )

        # Mock mixed results
        def mock_find_side_effect(controller_id, instance_id):
            if "failure" in controller_id:
                raise Exception("Point not found")
            return Mock(), Mock()

        with (
            patch.object(
                self.writer, "_find_target_point", side_effect=mock_find_side_effect
            ),
            patch.object(self.writer, "_perform_write_operation", return_value=50.0),
            patch.object(self.writer, "_create_database_record", return_value=Mock()),
        ):
            # Execute both operations
            success_result = await self.writer.write_value_to_point(success_request)
            failure_result = await self.writer.write_value_to_point(failure_request)

            # Verify success operation worked
            success_response, success_db = success_result
            assert success_response.success is True
            assert success_db is not None

            # Verify failure operation handled gracefully
            failure_response, failure_db = failure_result
            assert failure_response.success is False
            assert failure_db is None
            assert "Point not found" in failure_response.message


class TestBACnetWriterEdgeCases:
    """Test BACnetWriter edge cases and error conditions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.writer = BACnetWriter()

    @pytest.mark.asyncio
    async def test_write_with_empty_command_id(self):
        """Test: Write operation with empty command ID"""
        request_payload = SetValueToPointRequestPayload(
            iotDevicePointId="empty_cmd_point",
            pointInstanceId="empty_cmd_instance",
            controllerId="empty_cmd_controller",
            presentValue=25.0,
            commandId="",  # Empty command ID
            commandType="set_value_to_point",
        )

        with (
            patch.object(
                self.writer, "_find_target_point", return_value=(Mock(), Mock())
            ),
            patch.object(self.writer, "_perform_write_operation", return_value=25.0),
            patch.object(self.writer, "_create_database_record", return_value=Mock()),
        ):
            response, db_record = await self.writer.write_value_to_point(
                request_payload
            )

            # Should handle empty command ID gracefully
            assert response.success is True
            assert response.commandId == ""
            assert db_record is not None

    @pytest.mark.asyncio
    async def test_write_with_very_large_value(self):
        """Test: Write operation with very large numeric value"""
        large_value = 999999999.99

        request_payload = SetValueToPointRequestPayload(
            iotDevicePointId="large_value_point",
            pointInstanceId="large_value_instance",
            controllerId="large_value_controller",
            presentValue=large_value,
            commandId="large_value_cmd",
            commandType="set_value_to_point",
        )

        with (
            patch.object(
                self.writer, "_find_target_point", return_value=(Mock(), Mock())
            ),
            patch.object(
                self.writer, "_perform_write_operation", return_value=large_value
            ),
            patch.object(self.writer, "_create_database_record", return_value=Mock()),
        ):
            response, db_record = await self.writer.write_value_to_point(
                request_payload
            )

            # Should handle large values
            assert response.success is True
            assert f"Successfully wrote value {large_value}" in response.message

    @pytest.mark.asyncio
    async def test_write_with_negative_value(self):
        """Test: Write operation with negative value"""
        negative_value = -273.15

        request_payload = SetValueToPointRequestPayload(
            iotDevicePointId="negative_value_point",
            pointInstanceId="negative_value_instance",
            controllerId="negative_value_controller",
            presentValue=negative_value,
            commandId="negative_value_cmd",
            commandType="set_value_to_point",
        )

        with (
            patch.object(
                self.writer, "_find_target_point", return_value=(Mock(), Mock())
            ),
            patch.object(
                self.writer, "_perform_write_operation", return_value=negative_value
            ),
            patch.object(self.writer, "_create_database_record", return_value=Mock()),
        ):
            response, db_record = await self.writer.write_value_to_point(
                request_payload
            )

            # Should handle negative values
            assert response.success is True
            assert f"Successfully wrote value {negative_value}" in response.message

    @pytest.mark.asyncio
    async def test_write_with_special_characters_in_ids(self):
        """Test: Write operation with special characters in IDs"""
        request_payload = SetValueToPointRequestPayload(
            iotDevicePointId="point/with:special@chars",
            pointInstanceId="instance-with_special.chars",
            controllerId="controller#with$special%chars",
            presentValue=42.0,
            commandId="cmd*with&special^chars",
            commandType="set_value_to_point",
        )

        with (
            patch.object(
                self.writer, "_find_target_point", return_value=(Mock(), Mock())
            ),
            patch.object(self.writer, "_perform_write_operation", return_value=42.0),
            patch.object(self.writer, "_create_database_record", return_value=Mock()),
        ):
            response, db_record = await self.writer.write_value_to_point(
                request_payload
            )

            # Should handle special characters in IDs
            assert response.success is True
            assert response.commandId == "cmd*with&special^chars"

    @pytest.mark.asyncio
    async def test_write_operation_timeout_simulation(self):
        """Test: Write operation handles timeout scenarios"""
        request_payload = SetValueToPointRequestPayload(
            iotDevicePointId="timeout_point",
            pointInstanceId="timeout_instance",
            controllerId="timeout_controller",
            presentValue=30.0,
            commandId="timeout_cmd",
            commandType="set_value_to_point",
        )

        # Mock timeout in write operation
        with (
            patch.object(
                self.writer, "_find_target_point", return_value=(Mock(), Mock())
            ),
            patch.object(
                self.writer,
                "_perform_write_operation",
                side_effect=asyncio.TimeoutError("BACnet write timeout"),
            ),
        ):
            response, db_record = await self.writer.write_value_to_point(
                request_payload
            )

            # Should handle timeout gracefully
            assert response.success is False
            assert "BACnet write timeout" in response.message
            assert db_record is None

    @pytest.mark.asyncio
    async def test_write_with_none_state_text(self):
        """Test: Write operation with None state text (default behavior)"""
        request_payload = SetValueToPointRequestPayload(
            iotDevicePointId="none_state_point",
            pointInstanceId="none_state_instance",
            controllerId="none_state_controller",
            presentValue=15.0,
            stateText=None,  # None state text
            commandId="none_state_cmd",
            commandType="set_value_to_point",
        )

        with (
            patch.object(
                self.writer, "_find_target_point", return_value=(Mock(), Mock())
            ),
            patch.object(self.writer, "_perform_write_operation", return_value=15.0),
            patch.object(self.writer, "_create_database_record", return_value=Mock()),
        ):
            response, db_record = await self.writer.write_value_to_point(
                request_payload
            )

            # Should handle None state text
            assert response.success is True
            assert db_record is not None
