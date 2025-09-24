"""
BACnet-related test fixtures.
"""

import pytest
from unittest.mock import Mock, AsyncMock


@pytest.fixture
def mock_bac0_device():
    """Mock BAC0 device"""
    device = Mock()
    device.device_id = 12345
    device.address = "192.168.1.100"
    device.device_name = "Test_Device"
    device.vendor_name = "Test_Vendor"
    device.description = "Test BACnet Device"
    device.objects = {
        "analogInput:1": {"name": "Temperature_1", "present_value": 25.0},
        "analogInput:2": {"name": "Temperature_2", "present_value": 26.5},
        "analogInput:3": {"name": "Humidity_1", "present_value": 45.2},
    }
    return device


@pytest.fixture
def mock_bacnet_wrapper():
    """Mock BACnet wrapper"""
    wrapper = AsyncMock()
    wrapper.connect = AsyncMock()
    wrapper.disconnect = AsyncMock()
    wrapper.discover_devices = AsyncMock(
        return_value=["192.168.1.100", "192.168.1.101"]
    )
    wrapper.read_point = AsyncMock(return_value=25.0)
    wrapper.read_points = AsyncMock(return_value={"temp1": 25.0, "temp2": 26.0})
    wrapper.write_point = AsyncMock(return_value=True)
    wrapper.is_connected = True
    wrapper.device_list = []
    return wrapper


@pytest.fixture
def mock_bacnet_wrapper_manager():
    """Mock BACnet wrapper manager"""
    manager = AsyncMock()
    manager.create_wrapper = AsyncMock()
    manager.get_wrapper = AsyncMock()
    manager.remove_wrapper = AsyncMock()
    manager.get_all_wrappers = AsyncMock(return_value=[])
    manager.wrappers = {}
    return manager


@pytest.fixture
def mock_bacnet_load_balancer():
    """Mock BACnet load balancer"""
    balancer = Mock()
    balancer.select_reader = Mock(return_value="reader_1")
    balancer.add_reader = Mock()
    balancer.remove_reader = Mock()
    balancer.get_reader_stats = Mock(return_value={})
    balancer.readers = ["reader_1", "reader_2"]
    return balancer


@pytest.fixture
def sample_bacnet_points():
    """Sample BACnet points for testing"""
    return [
        {
            "device_id": 12345,
            "object_type": "analogInput",
            "object_instance": 1,
            "property": "presentValue",
            "name": "Temperature_1",
            "units": "degreesCelsius",
            "value": 25.0,
        },
        {
            "device_id": 12345,
            "object_type": "analogInput",
            "object_instance": 2,
            "property": "presentValue",
            "name": "Humidity_1",
            "units": "percent",
            "value": 45.2,
        },
    ]


@pytest.fixture
def sample_bacnet_config():
    """Sample BACnet configuration"""
    return {
        "ip_address": "192.168.1.100",
        "subnet_mask": "255.255.255.0",
        "port": 47808,
        "device_id": 2111,
        "device_name": "BMS_Gateway",
        "max_apdu_length": 1476,
        "segmentation_supported": "segmentedBoth",
        "vendor_id": 999,
    }
