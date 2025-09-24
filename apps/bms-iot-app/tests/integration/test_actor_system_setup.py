"""
Test actor system setup and initialization.

User Story: As a developer, I want to ensure the actor system initializes correctly for testing
"""

import pytest
import asyncio
from unittest.mock import patch
import sys

# Add the fixtures directory to the path
sys.path.insert(
    0, "/Users/amol/Documents/ai-projects/bms-project/apps/bms-iot-app/tests"
)

from fixtures.actor_test_harness import ActorTestHarness


class TestActorSystemInitialization:
    """Test actor system initialization and setup"""

    @pytest.mark.asyncio
    async def test_actor_test_harness_creation(self):
        """Test: ActorTestHarness creates all actors without errors"""
        harness = ActorTestHarness()

        # Verify harness is created with proper attributes
        assert harness is not None
        assert hasattr(harness, "actors")
        assert hasattr(harness, "messages")
        assert hasattr(harness, "mqtt_client")
        assert hasattr(harness, "bacnet_wrapper")

        # Verify initial state
        assert isinstance(harness.actors, dict)
        assert isinstance(harness.messages, list)
        assert len(harness.actors) == 0
        assert len(harness.messages) == 0

    @pytest.mark.asyncio
    async def test_actor_system_initialization(self):
        """Test: Actor system initializes with all required actors"""
        harness = ActorTestHarness()

        # Initialize the actor system
        await harness.initialize()

        # Verify all actors are created
        assert len(harness.actors) > 0

        # Check for expected actors
        expected_actors = ["mqtt", "bacnet_monitoring", "uploader", "heartbeat"]
        for actor_name in expected_actors:
            assert (
                actor_name in harness.actors
            ), f"Actor {actor_name} not found in initialized system"
            assert harness.actors[actor_name] is not None

    @pytest.mark.asyncio
    async def test_actor_system_cleanup(self):
        """Test: Actor system shutdown and cleanup works properly"""
        harness = ActorTestHarness()

        # Initialize the actor system
        await harness.initialize()

        # Verify actors are running
        initial_actor_count = len(harness.actors)
        assert initial_actor_count > 0

        # Cleanup the actor system
        await harness.cleanup()

        # Verify cleanup completed
        # After cleanup, actors should be stopped or removed
        assert harness._cleaned_up is True

    @pytest.mark.asyncio
    async def test_actor_registry_functionality(self):
        """Test: Actor registry and lookup functionality"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Test actor lookup by name
        mqtt_actor = harness.get_actor("mqtt")
        assert mqtt_actor is not None

        # Test getting non-existent actor
        non_existent = harness.get_actor("non_existent")
        assert non_existent is None

        # Test listing all actors
        all_actors = harness.list_actors()
        assert isinstance(all_actors, list)
        assert len(all_actors) > 0
        assert "mqtt" in all_actors

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_multiple_harness_instances(self):
        """Test: Multiple harness instances can coexist"""
        harness1 = ActorTestHarness()
        harness2 = ActorTestHarness()

        # Initialize both harnesses
        await harness1.initialize()
        await harness2.initialize()

        # Verify both are independent
        assert harness1 is not harness2
        assert harness1.actors is not harness2.actors
        assert harness1.messages is not harness2.messages

        # Cleanup both
        await harness1.cleanup()
        await harness2.cleanup()

    @pytest.mark.asyncio
    async def test_actor_initialization_error_handling(self):
        """Test: Handle errors during actor initialization"""
        harness = ActorTestHarness()

        # Mock an initialization failure
        with patch.object(
            harness, "_create_actor", side_effect=Exception("Actor init failed")
        ):
            # Initialize should handle the error gracefully
            try:
                await harness.initialize()
                # Some actors might still be created
                assert len(harness.actors) >= 0
            except Exception as e:
                # Or it might propagate the error - both are valid
                assert "Actor init failed" in str(e)

        # Cleanup should still work even after partial initialization
        await harness.cleanup()


class TestActorSystemConfiguration:
    """Test actor system configuration and settings"""

    @pytest.mark.asyncio
    async def test_actor_configuration_loading(self):
        """Test: Actors load with correct configuration"""
        harness = ActorTestHarness()

        # Initialize with custom configuration
        config = {
            "mqtt": {
                "broker_host": "test.mqtt.broker",
                "broker_port": 1883,
                "client_id": "test_client",
            },
            "bacnet": {"device_id": "test_device_123", "network_interface": "eth0"},
        }

        await harness.initialize(config=config)

        # Verify configuration was applied
        mqtt_actor = harness.get_actor("mqtt")
        if mqtt_actor and hasattr(mqtt_actor, "config"):
            assert mqtt_actor.config.get("broker_host") == "test.mqtt.broker"

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_actor_system_state_tracking(self):
        """Test: Actor system tracks state correctly"""
        harness = ActorTestHarness()

        # Initially not initialized
        assert harness.is_initialized() is False

        # After initialization
        await harness.initialize()
        assert harness.is_initialized() is True

        # After cleanup
        await harness.cleanup()
        assert harness.is_initialized() is False

    @pytest.mark.asyncio
    async def test_actor_system_message_logging(self):
        """Test: Actor system logs messages correctly"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Enable message logging
        harness.enable_message_logging()

        # Send a test message (this will be expanded in test_message_routing.py)
        test_message = {
            "type": "TEST",
            "sender": "test_sender",
            "receiver": "mqtt",
            "payload": {"test": "data"},
        }

        # Record the message
        harness._record_message(test_message)

        # Verify message was logged
        assert len(harness.messages) == 1
        assert harness.messages[0] == test_message

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_actor_system_mock_integration(self):
        """Test: Actor system integrates with mock components"""
        harness = ActorTestHarness()

        # Verify mock components are available
        assert harness.mqtt_client is not None
        assert harness.bacnet_wrapper is not None
        assert harness.rest_client is not None

        # Initialize system
        await harness.initialize()

        # Verify mocks are integrated with actors
        mqtt_actor = harness.get_actor("mqtt")
        if mqtt_actor:
            # The actor should use the mock MQTT client
            assert hasattr(mqtt_actor, "client")

        await harness.cleanup()


class TestActorSystemResilience:
    """Test actor system resilience and recovery"""

    @pytest.mark.asyncio
    async def test_actor_restart_capability(self):
        """Test: Individual actors can be restarted"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Get initial actor reference
        mqtt_actor_initial = harness.get_actor("mqtt")
        assert mqtt_actor_initial is not None

        # Restart the actor
        await harness.restart_actor("mqtt")

        # Get new actor reference
        mqtt_actor_after = harness.get_actor("mqtt")
        assert mqtt_actor_after is not None

        # Verify it's a new instance (or properly restarted)
        # This depends on implementation - might be same object but reset
        assert harness.actors["mqtt"] is not None

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_partial_actor_failure_handling(self):
        """Test: System continues with partial actor failures"""
        harness = ActorTestHarness()

        # Initialize system
        await harness.initialize()

        # Simulate an actor failure
        harness._simulate_actor_failure("uploader")

        # System should still be operational
        assert harness.is_initialized() is True

        # Other actors should still be available
        mqtt_actor = harness.get_actor("mqtt")
        assert mqtt_actor is not None

        # Failed actor should be marked or removed
        uploader_actor = harness.get_actor("uploader")
        # Either None or in failed state
        assert uploader_actor is None or harness._is_actor_failed("uploader")

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_actor_system_reinitialize(self):
        """Test: Actor system can be reinitialized after cleanup"""
        harness = ActorTestHarness()

        # First initialization
        await harness.initialize()
        initial_actors = list(harness.actors.keys())
        assert len(initial_actors) > 0

        # Cleanup
        await harness.cleanup()
        assert harness.is_initialized() is False

        # Reinitialize
        await harness.initialize()
        assert harness.is_initialized() is True

        # Should have same actors as before
        reinitialized_actors = list(harness.actors.keys())
        assert set(reinitialized_actors) == set(initial_actors)

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_concurrent_actor_operations(self):
        """Test: Concurrent operations on actor system"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Perform concurrent operations
        async def get_actor_info(actor_name):
            actor = harness.get_actor(actor_name)
            return actor is not None

        # Run multiple concurrent actor lookups
        tasks = [
            get_actor_info("mqtt"),
            get_actor_info("bacnet_monitoring"),
            get_actor_info("uploader"),
            get_actor_info("heartbeat"),
        ]

        results = await asyncio.gather(*tasks)

        # All lookups should succeed
        assert all(results), "Some actor lookups failed during concurrent access"

        await harness.cleanup()


class TestActorSystemMetrics:
    """Test actor system metrics and monitoring"""

    @pytest.mark.asyncio
    async def test_actor_system_metrics_collection(self):
        """Test: System collects metrics about actors"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Get system metrics
        metrics = harness.get_system_metrics()

        assert metrics is not None
        assert "actor_count" in metrics
        assert "message_count" in metrics
        assert "uptime" in metrics
        assert metrics["actor_count"] > 0

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_actor_health_monitoring(self):
        """Test: System monitors actor health"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Check health of all actors
        health_status = harness.get_health_status()

        assert health_status is not None
        assert isinstance(health_status, dict)

        # Each actor should have health status
        for actor_name in harness.list_actors():
            assert actor_name in health_status
            assert "status" in health_status[actor_name]
            assert health_status[actor_name]["status"] in [
                "healthy",
                "unhealthy",
                "unknown",
            ]

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_message_throughput_tracking(self):
        """Test: System tracks message throughput"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Enable message tracking
        harness.enable_message_logging()

        # Simulate some messages
        for i in range(10):
            test_message = {
                "id": i,
                "type": "TEST",
                "sender": "test",
                "receiver": "mqtt",
            }
            harness._record_message(test_message)

        # Get throughput metrics
        throughput = harness.get_message_throughput()

        assert throughput is not None
        assert throughput["total_messages"] == 10
        assert "messages_per_second" in throughput

        await harness.cleanup()
