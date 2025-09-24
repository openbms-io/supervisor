"""
Test controller points data model.

User Story: As a developer, I want controller points model to work correctly
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from src.models.controller_points import (
    ControllerPointsModel,
    insert_controller_point,
    bulk_insert_controller_points,
    get_controller_points_by_controller_id,
    delete_uploaded_points,
    mark_points_as_uploaded,
    get_points_to_upload,
)
from src.models.bacnet_types import BacnetObjectTypeEnum


class TestControllerPointsModel:
    """Test ControllerPointsModel data structure"""

    def test_controller_point_creation(self):
        """Test: Controller point model creation with required fields"""
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type=BacnetObjectTypeEnum.ANALOG_INPUT,
            point_id=1,
            iot_device_point_id="point_123",
            controller_id="ctrl_456",
            controller_device_id="device_789",
        )

        assert point.controller_ip_address == "192.168.1.100"
        assert point.bacnet_object_type == BacnetObjectTypeEnum.ANALOG_INPUT
        assert point.point_id == 1
        assert point.iot_device_point_id == "point_123"
        assert point.controller_id == "ctrl_456"
        assert point.controller_device_id == "device_789"
        assert point.controller_port == 47808  # DEFAULT_CONTROLLER_PORT
        assert point.is_uploaded is False

    def test_controller_point_with_optional_fields(self):
        """Test: Controller point with optional health monitoring fields"""
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type=BacnetObjectTypeEnum.BINARY_OUTPUT,
            point_id=2,
            iot_device_point_id="point_234",
            controller_id="ctrl_567",
            controller_device_id="device_890",
            units="degrees_celsius",
            present_value="25.5",
            status_flags="fault;overridden",
            event_state="normal",
            out_of_service=False,
            reliability="noFaultDetected",
            error_info='{"error": "none"}',
        )

        assert point.units == "degrees_celsius"
        assert point.present_value == "25.5"
        assert point.status_flags == "fault;overridden"
        assert point.event_state == "normal"
        assert point.out_of_service is False
        assert point.reliability == "noFaultDetected"
        assert point.error_info == '{"error": "none"}'

    def test_controller_point_default_values(self):
        """Test: Default values are set correctly"""
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type=BacnetObjectTypeEnum.ANALOG_VALUE,
            point_id=3,
            iot_device_point_id="point_345",
            controller_id="ctrl_678",
            controller_device_id="device_901",
        )

        assert point.controller_port == 47808  # DEFAULT_CONTROLLER_PORT
        assert point.units is None
        assert point.is_uploaded is False
        assert point.status_flags is None
        assert point.event_state is None
        assert point.out_of_service is None
        assert point.reliability is None
        assert point.error_info is None
        assert isinstance(point.created_at, datetime)
        assert isinstance(point.updated_at, datetime)


class TestControllerPointsDatabaseOperations:
    """Test database operations for controller points"""

    @pytest.mark.asyncio
    async def test_insert_controller_point_success(self):
        """Test: Successful point insertion"""
        with patch("src.models.controller_points.get_session") as mock_get_session:
            mock_session = AsyncMock()

            # Create async context manager mock
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            point = ControllerPointsModel(
                controller_ip_address="192.168.1.100",
                bacnet_object_type=BacnetObjectTypeEnum.ANALOG_INPUT,
                point_id=1,
                iot_device_point_id="point_123",
                controller_id="ctrl_456",
                controller_device_id="device_789",
            )
            point.id = 1  # Simulate database assignment

            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()

            result = await insert_controller_point(point)

            mock_session.add.assert_called_once_with(point)
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once_with(point)
            assert result == point

    @pytest.mark.asyncio
    async def test_get_controller_points_by_controller_id(self):
        """Test: Fetch points by controller ID"""
        with patch("src.models.controller_points.get_session") as mock_get_session:
            mock_session = AsyncMock()

            # Create async context manager mock
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            # Create mock points
            mock_point1 = Mock(spec=ControllerPointsModel)
            mock_point1.controller_id = "ctrl_123"
            mock_point2 = Mock(spec=ControllerPointsModel)
            mock_point2.controller_id = "ctrl_123"

            # Mock query result
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = [
                mock_point1,
                mock_point2,
            ]
            mock_session.execute = AsyncMock(return_value=mock_result)

            result = await get_controller_points_by_controller_id("ctrl_123")

            assert len(result) == 2
            assert result[0] == mock_point1
            assert result[1] == mock_point2
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_uploaded_points(self):
        """Test: Delete points that have been uploaded"""
        with patch("src.models.controller_points.get_session") as mock_get_session:
            mock_session = AsyncMock()

            # Create async context manager mock
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            # Create mock uploaded points
            mock_point1 = Mock(spec=ControllerPointsModel)
            mock_point1.is_uploaded = True
            mock_point2 = Mock(spec=ControllerPointsModel)
            mock_point2.is_uploaded = True

            # Mock query result
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = [
                mock_point1,
                mock_point2,
            ]
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session.delete = AsyncMock()
            mock_session.commit = AsyncMock()

            result = await delete_uploaded_points()

            assert result == 2
            assert mock_session.delete.call_count == 2
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_points_as_uploaded(self):
        """Test: Mark points as uploaded"""
        with patch("src.models.controller_points.get_session") as mock_get_session:
            mock_session = AsyncMock()

            # Create async context manager mock
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            # Create mock points with IDs
            mock_point1 = Mock(spec=ControllerPointsModel)
            mock_point1.id = 1
            mock_point2 = Mock(spec=ControllerPointsModel)
            mock_point2.id = 2

            mock_session.execute = AsyncMock()
            mock_session.commit = AsyncMock()

            await mark_points_as_uploaded([mock_point1, mock_point2])

            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_points_as_uploaded_empty_list(self):
        """Test: Mark points as uploaded with empty list"""
        with patch("src.models.controller_points.get_session") as mock_get_session:
            mock_session = AsyncMock()

            # Create async context manager mock
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            await mark_points_as_uploaded([])

            # Should not call session methods for empty list
            mock_session.execute.assert_not_called()
            mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_points_to_upload(self):
        """Test: Fetch points that need to be uploaded"""
        with patch("src.models.controller_points.get_session") as mock_get_session:
            mock_session = AsyncMock()

            # Create async context manager mock
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            # Create mock points not yet uploaded
            mock_point1 = Mock(spec=ControllerPointsModel)
            mock_point1.is_uploaded = False
            mock_point2 = Mock(spec=ControllerPointsModel)
            mock_point2.is_uploaded = False

            # Mock query result
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = [
                mock_point1,
                mock_point2,
            ]
            mock_session.execute = AsyncMock(return_value=mock_result)

            result = await get_points_to_upload()

            assert len(result) == 2
            assert result[0] == mock_point1
            assert result[1] == mock_point2
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_operations_with_session_failure(self):
        """Test: Database operations handle session failures gracefully"""
        with patch("src.models.controller_points.get_session") as mock_get_session:
            # Mock context manager that raises exception on enter
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(
                side_effect=RuntimeError("Failed to get database session")
            )
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            # Test insert_controller_point raises exception on session failure
            point = ControllerPointsModel(
                controller_ip_address="192.168.1.100",
                bacnet_object_type=BacnetObjectTypeEnum.ANALOG_INPUT,
                point_id=1,
                iot_device_point_id="point_123",
                controller_id="ctrl_456",
                controller_device_id="device_789",
            )

            with pytest.raises(RuntimeError, match="Failed to get database session"):
                await insert_controller_point(point)

            # Test get_controller_points_by_controller_id raises exception
            with pytest.raises(RuntimeError, match="Failed to get database session"):
                await get_controller_points_by_controller_id("ctrl_123")

            # Test delete_uploaded_points raises exception
            with pytest.raises(RuntimeError, match="Failed to get database session"):
                await delete_uploaded_points()

            # Test get_points_to_upload raises exception
            with pytest.raises(RuntimeError, match="Failed to get database session"):
                await get_points_to_upload()


class TestControllerPointsEdgeCases:
    """Test edge cases and error handling"""

    def test_controller_point_with_none_values(self):
        """Test: Controller point handles None values correctly"""
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type=BacnetObjectTypeEnum.MULTI_STATE_INPUT,
            point_id=4,
            iot_device_point_id="point_456",
            controller_id="ctrl_789",
            controller_device_id="device_012",
            present_value=None,
            units=None,
        )

        assert point.present_value is None
        assert point.units is None

    def test_controller_point_bacnet_object_type_validation(self):
        """Test: BACnet object type enum validation"""
        point = ControllerPointsModel(
            controller_ip_address="192.168.1.100",
            bacnet_object_type=BacnetObjectTypeEnum.BINARY_VALUE,
            point_id=5,
            iot_device_point_id="point_567",
            controller_id="ctrl_890",
            controller_device_id="device_123",
        )

        assert point.bacnet_object_type == BacnetObjectTypeEnum.BINARY_VALUE
        assert point.bacnet_object_type.value == "binaryValue"

    @pytest.mark.asyncio
    async def test_mark_points_as_uploaded_with_none_ids(self):
        """Test: Mark points as uploaded when some points have None IDs"""
        with patch("src.models.controller_points.get_session") as mock_get_session:
            mock_session = AsyncMock()

            # Create async context manager mock
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            # Create mock points, some with None IDs
            mock_point1 = Mock(spec=ControllerPointsModel)
            mock_point1.id = 1
            mock_point2 = Mock(spec=ControllerPointsModel)
            mock_point2.id = None
            mock_point3 = Mock(spec=ControllerPointsModel)
            mock_point3.id = 3

            mock_session.execute = AsyncMock()
            mock_session.commit = AsyncMock()

            await mark_points_as_uploaded([mock_point1, mock_point2, mock_point3])

            # Should only update points with non-None IDs
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()


class TestBulkInsertControllerPoints:
    """Test bulk insertion functionality for controller points"""

    @pytest.mark.asyncio
    async def test_bulk_insert_empty_list(self):
        """Test: Bulk insert with empty list handles gracefully"""
        await bulk_insert_controller_points([])
        # Should complete without error

    @pytest.mark.asyncio
    async def test_bulk_insert_success(self):
        """Test: Successful bulk insertion of multiple points"""
        with patch("src.models.controller_points.get_session") as mock_get_session:
            mock_session = AsyncMock()

            # Create async context manager mock
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            # Create test points
            points = [
                ControllerPointsModel(
                    controller_ip_address="192.168.1.100",
                    bacnet_object_type=BacnetObjectTypeEnum.ANALOG_INPUT,
                    point_id=1,
                    iot_device_point_id="point_123",
                    controller_id="ctrl_456",
                    controller_device_id="device_789",
                ),
                ControllerPointsModel(
                    controller_ip_address="192.168.1.100",
                    bacnet_object_type=BacnetObjectTypeEnum.ANALOG_OUTPUT,
                    point_id=2,
                    iot_device_point_id="point_234",
                    controller_id="ctrl_456",
                    controller_device_id="device_789",
                ),
            ]

            # Mock successful session operations (simplified: no fetch-after-insert)
            mock_session.add_all = Mock()
            mock_session.commit = AsyncMock()

            # Set up points with IDs after commit (simulate database ID assignment)
            points[0].id = 1
            points[1].id = 2

            await bulk_insert_controller_points(points)

            # Verify session operations (simplified version)
            mock_session.add_all.assert_called_once_with(points)
            mock_session.commit.assert_called_once()
            # Verify points were modified in place (database would assign IDs)
            assert all(point.id is not None for point in points)

    @pytest.mark.asyncio
    async def test_bulk_insert_database_error(self):
        """Test: Bulk insert handles database errors gracefully"""
        with patch("src.models.controller_points.get_session") as mock_get_session:
            mock_session = AsyncMock()

            # Create async context manager mock
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            # Create test points
            points = [
                ControllerPointsModel(
                    controller_ip_address="192.168.1.100",
                    bacnet_object_type=BacnetObjectTypeEnum.ANALOG_INPUT,
                    point_id=1,
                    iot_device_point_id="point_123",
                    controller_id="ctrl_456",
                    controller_device_id="device_789",
                )
            ]

            # Mock database error
            mock_session.add_all = Mock()
            mock_session.commit = AsyncMock(side_effect=Exception("Database error"))
            mock_session.rollback = AsyncMock()

            # Should raise the exception
            with pytest.raises(Exception, match="Database error"):
                await bulk_insert_controller_points(points)

            # Verify session operations were attempted
            mock_session.add_all.assert_called_once_with(points)
            mock_session.commit.assert_called_once()
            # Note: rollback is handled automatically by async context manager

    @pytest.mark.asyncio
    async def test_bulk_insert_session_failure(self):
        """Test: Bulk insert raises exception when session fails"""
        with patch("src.models.controller_points.get_session") as mock_get_session:
            # Mock context manager that raises exception on enter
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(
                side_effect=RuntimeError("Failed to get database session")
            )
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            points = [
                ControllerPointsModel(
                    controller_ip_address="192.168.1.100",
                    bacnet_object_type=BacnetObjectTypeEnum.ANALOG_INPUT,
                    point_id=1,
                    iot_device_point_id="point_123",
                    controller_id="ctrl_456",
                    controller_device_id="device_789",
                )
            ]

            with pytest.raises(RuntimeError, match="Failed to get database session"):
                await bulk_insert_controller_points(points)

    @pytest.mark.asyncio
    async def test_bulk_insert_large_batch(self):
        """Test: Bulk insert handles large batches efficiently"""
        with patch("src.models.controller_points.get_session") as mock_get_session:
            mock_session = AsyncMock()

            # Create async context manager mock
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            # Create 100 test points
            points = []
            for i in range(100):
                points.append(
                    ControllerPointsModel(
                        controller_ip_address="192.168.1.100",
                        bacnet_object_type=BacnetObjectTypeEnum.ANALOG_INPUT,
                        point_id=i,
                        iot_device_point_id=f"point_{i}",
                        controller_id="ctrl_456",
                        controller_device_id="device_789",
                    )
                )

            # Mock successful session operations (simplified: no fetch-after-insert)
            mock_session.add_all = Mock()
            mock_session.commit = AsyncMock()

            # Set up points with IDs after commit (simulate database ID assignment)
            for i, point in enumerate(points):
                point.id = i + 1

            await bulk_insert_controller_points(points)

            # Verify single add_all call with all points (simplified version)
            mock_session.add_all.assert_called_once_with(points)
            mock_session.commit.assert_called_once()
            # Verify points were modified in place (database would assign IDs)
            assert all(point.id is not None for point in points)

    @pytest.mark.asyncio
    async def test_bulk_insert_with_health_properties(self):
        """Test: Bulk insert preserves health monitoring properties"""
        with patch("src.models.controller_points.get_session") as mock_get_session:
            mock_session = AsyncMock()

            # Create async context manager mock
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_get_session.return_value = mock_context_manager

            # Create point with health properties
            point = ControllerPointsModel(
                controller_ip_address="192.168.1.100",
                bacnet_object_type=BacnetObjectTypeEnum.BINARY_OUTPUT,
                point_id=1,
                iot_device_point_id="point_123",
                controller_id="ctrl_456",
                controller_device_id="device_789",
                present_value="1",
                units="degrees_celsius",
                status_flags="fault;overridden",
                event_state="normal",
                out_of_service=False,
                reliability="noFaultDetected",
                error_info='{"error": "none"}',
            )

            # Mock successful session operations
            mock_session.add_all = Mock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()

            await bulk_insert_controller_points([point])

            # Verify all properties are preserved in the original point
            assert point.present_value == "1"
            assert point.units == "degrees_celsius"
            assert point.status_flags == "fault;overridden"
            assert point.event_state == "normal"
            assert point.out_of_service is False
            assert point.reliability == "noFaultDetected"
            assert point.error_info == '{"error": "none"}'
