"""
Pytest configuration and fixtures for BMS IoT Application tests.
"""

import os
import sys

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, AsyncMock


@pytest.fixture
def mock_bacnet_wrapper():
    """Fixture for mock BACnet wrapper"""
    wrapper = AsyncMock()
    wrapper.connect = AsyncMock()
    wrapper.read_points = AsyncMock(return_value={"temp1": 25.0, "temp2": 26.0})
    wrapper.write_point = AsyncMock(return_value=True)
    wrapper.is_connected = True
    wrapper.device_id = "test_device_123"
    return wrapper


@pytest.fixture
def mock_mqtt_client():
    """Fixture for mock MQTT client"""
    client = AsyncMock()
    client.connect = AsyncMock()
    client.publish = AsyncMock()
    client.subscribe = AsyncMock()
    client.disconnect = AsyncMock()
    client.is_connected = True
    client.published_messages = []
    client.subscriptions = []
    return client


@pytest.fixture
def mock_rest_client():
    """Fixture for mock REST client"""
    client = AsyncMock()
    client.post = AsyncMock()
    client.get = AsyncMock()
    client.uploaded_data = []

    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    client.post.return_value = mock_response

    return client


@pytest.fixture
def sample_actor_messages():
    """Sample actor messages for testing"""
    # Simple mock messages to avoid import issues during testing setup
    return {
        "config_upload": {
            "sender": "MQTT",
            "receiver": "BACNET",
            "message_type": "CONFIG_UPLOAD_REQUEST",
            "payload": {},
        },
        "point_publish": {
            "sender": "BACNET",
            "receiver": "MQTT",
            "message_type": "POINT_PUBLISH_REQUEST",
            "payload": {
                "device_id": "123",
                "points": [{"name": "temp1", "value": 25.0}],
            },
        },
        "heartbeat": {
            "sender": "HEARTBEAT",
            "receiver": "BROADCAST",
            "message_type": "HEARTBEAT_STATUS",
            "payload": {"status": "healthy"},
        },
    }


@pytest.fixture
def sample_bacnet_data():
    """Sample BACnet data for testing"""
    return {
        "device_123": {
            "temp1": 25.0,
            "temp2": 26.5,
            "humidity1": 45.2,
            "pressure1": 101.3,
        },
        "device_456": {"temp3": 22.1, "temp4": 24.8, "humidity2": 38.7},
    }


@pytest.fixture
def cleanup():
    """Fixture for resource cleanup during tests"""
    cleanup_resources = []

    def register_resource(resource):
        """Register a resource for cleanup"""
        cleanup_resources.append(resource)

    yield register_resource

    # Cleanup registered resources (synchronous cleanup for now)
    for resource in cleanup_resources:
        if hasattr(resource, "cleanup"):
            # For simplicity in tests, we'll just track that cleanup would be called
            pass
        elif hasattr(resource, "close"):
            # For simplicity in tests, we'll just track that close would be called
            pass


@pytest.fixture
def sample_mqtt_config():
    """Sample MQTT configuration for testing"""
    return {
        "broker_host": "localhost",
        "broker_port": 1883,
        "username": "test_user",
        "password": "test_pass",
        "topics": {
            "command": "iot/global/test_org/test_site/test_device/command",
            "status": "iot/global/test_org/test_site/test_device/status",
        },
    }


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Initialize database tables before running tests using SQLModel.metadata.create_all()"""

    # Add monorepo root to Python path to access packages/ directory
    # This conftest.py is in apps/bms-iot-app/tests/conftest.py
    # We need to add the monorepo root (../../../ from here) to access packages/
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        # Import all models to ensure they're registered with SQLModel
        from src.network.sqlmodel_client import initialize_database

        # For tests, use SQLModel.metadata.create_all() for simplicity
        # This creates all tables based on the current model definitions
        print("🔄 Creating test database tables with SQLModel.metadata.create_all()...")

        from sqlmodel import SQLModel
        from src.network.sqlmodel_client import get_engine

        engine = get_engine()
        print(f"Test database URL: {engine.url}")

        # Create all tables for the test database
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        print("✅ Test database tables created successfully")

        # Initialize database optimizations
        await initialize_database()
        print("✅ Global test database setup completed")

    except Exception as e:
        print(f"❌ Global test database setup failed: {e}")
        raise


# Pytest configuration for asyncio
def pytest_configure(config):
    """Configure pytest for asyncio testing"""
    config.addinivalue_line("markers", "asyncio: mark test as an async test")
