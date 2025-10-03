import pytest
from unittest.mock import Mock, AsyncMock

from src.network.mqtt_command_dispatcher import MqttCommandDispatcher
from src.network.mqtt_client import MQTTClient
from packages.mqtt_topics.topics_loader import CommandNameEnum
from src.models.controller_points import ControllerPointsModel
import paho.mqtt.client as mqtt


class TestMqttCommandDispatcher:
    """Unit tests for MqttCommandDispatcher class."""

    @pytest.fixture
    def mock_mqtt_client(self):
        """Create a mock MQTT client."""
        mock_client = Mock(spec=MQTTClient)
        mock_client.subscribe = Mock()
        mock_client.publish = Mock(return_value=True)
        mock_client.set_on_message = Mock()
        return mock_client

    @pytest.fixture
    def dispatcher(self, mock_mqtt_client):
        """Create MqttCommandDispatcher instance with mocked client."""
        return MqttCommandDispatcher(
            mqtt_client=mock_mqtt_client,
            organization_id="test-org",
            site_id="test-site",
            iot_device_id="test-device",
            controller_device_id="test-controller",
            iot_device_point_id="test-point",
        )

    @pytest.fixture
    def sample_controller_point(self):
        """Create a sample controller point for testing."""
        return ControllerPointsModel(
            iot_device_id="test-device",
            controller_device_id="test-controller",
            point_id="test-point",
            point_name="Test Point",
            point_type="analog-input",
            present_value=23.5,
            status_flags="fault;overridden",
            priority_array="[null, null, 50.0, null]",
            created_at_unix_milli_timestamp=1640995200000,
        )

    def test_initialization(self, mock_mqtt_client):
        """Test dispatcher initializes with correct parameters."""
        dispatcher = MqttCommandDispatcher(
            mqtt_client=mock_mqtt_client,
            organization_id="test-org",
            site_id="test-site",
            iot_device_id="test-device",
        )

        assert dispatcher.organization_id == "test-org"
        assert dispatcher.site_id == "test-site"
        assert dispatcher.iot_device_id == "test-device"
        assert dispatcher.controller_device_id is None
        assert dispatcher.iot_device_point_id is None
        assert len(dispatcher.handlers) == 0
        assert len(dispatcher.request_topics) == 5  # 5 commands
        assert len(dispatcher.response_topics) == 5

    def test_subscribe_all_subscribes_to_all_request_topics(
        self, dispatcher, mock_mqtt_client
    ):
        """Test that subscribe_all subscribes to all command request topics with QoS=1."""
        dispatcher.subscribe_all()

        # Verify all 5 command request topics are subscribed to
        assert mock_mqtt_client.subscribe.call_count == 5

        # Check that each call uses QoS=1
        for call_args in mock_mqtt_client.subscribe.call_args_list:
            args, kwargs = call_args
            assert kwargs["qos"] == 1

        # Verify specific topics are included
        subscribed_topics = [
            call_args[1]["topic"]
            for call_args in mock_mqtt_client.subscribe.call_args_list
        ]

        expected_patterns = [
            "iot/global/test-org/test-site/test-device/command/get_config/request",
            "iot/global/test-org/test-site/test-device/command/reboot/request",
            "iot/global/test-org/test-site/test-device/command/set_value_to_point/request",
            "iot/global/test-org/test-site/test-device/command/start_monitoring/request",
            "iot/global/test-org/test-site/test-device/command/stop_monitoring/request",
        ]

        for expected_topic in expected_patterns:
            assert expected_topic in subscribed_topics

    def test_register_handler_valid_command(self, dispatcher):
        """Test registering handler for valid command."""
        mock_handler = AsyncMock()

        dispatcher.register_handler(CommandNameEnum.get_config, mock_handler)

        assert dispatcher.handlers[CommandNameEnum.get_config] == mock_handler

    def test_register_handler_invalid_command(self, dispatcher):
        """Test registering handler for invalid command raises error."""
        mock_handler = AsyncMock()

        with pytest.raises(AttributeError, match="No handler slot for command"):
            dispatcher.register_handler("invalid_command", mock_handler)

    def test_handler_dispatch_based_on_topic(self, dispatcher, mock_mqtt_client):
        """Test that correct handler is dispatched based on incoming topic."""
        # Register mock handlers
        get_config_handler = AsyncMock()
        reboot_handler = AsyncMock()

        dispatcher.register_handler(CommandNameEnum.get_config, get_config_handler)
        dispatcher.register_handler(CommandNameEnum.reboot, reboot_handler)

        # Attach dispatcher to client
        dispatcher.attach_to_client()

        # Get the on_message callback that was set
        on_message_callback = mock_mqtt_client.set_on_message.call_args[0][0]

        # Create mock MQTT message for get_config command
        mock_message = Mock(spec=mqtt.MQTTMessage)
        mock_message.topic = (
            "iot/global/test-org/test-site/test-device/command/get_config/request"
        )
        mock_message.payload = b'{"test": "data"}'

        # Simulate message receipt
        on_message_callback(mock_mqtt_client, None, mock_message)

        # Verify get_config handler was called
        get_config_handler.assert_called_once()
        reboot_handler.assert_not_called()

    def test_handler_not_called_when_not_registered(self, dispatcher, mock_mqtt_client):
        """Test that no handler is called when command is not registered."""
        # Register a handler for a different command to verify it's NOT called
        reboot_handler = AsyncMock()
        dispatcher.register_handler(CommandNameEnum.reboot, reboot_handler)

        dispatcher.attach_to_client()
        on_message_callback = mock_mqtt_client.set_on_message.call_args[0][0]

        # Create message for unregistered get_config command (we only registered reboot)
        mock_message = Mock(spec=mqtt.MQTTMessage)
        mock_message.topic = (
            "iot/global/test-org/test-site/test-device/command/get_config/request"
        )
        mock_message.payload = b'{"test": "data"}'

        # Call the callback
        on_message_callback(mock_mqtt_client, None, mock_message)

        # Verify the registered handler was NOT called since it's for a different command
        reboot_handler.assert_not_called()

    def test_publish_response_with_correct_topic_retain_qos(
        self, dispatcher, mock_mqtt_client
    ):
        """Test publish_response uses correct response topic, retain, and QoS."""
        test_payload = {"status": "success", "data": "test"}

        # Test each command response
        test_cases = [
            (CommandNameEnum.get_config, "get_config"),
            (CommandNameEnum.reboot, "reboot"),
            (CommandNameEnum.set_value_to_point, "set_value_to_point"),
            (CommandNameEnum.start_monitoring, "start_monitoring"),
            (CommandNameEnum.stop_monitoring, "stop_monitoring"),
        ]

        for command, command_str in test_cases:
            mock_mqtt_client.publish.reset_mock()

            dispatcher.publish_response(command, test_payload)

            # Verify publish was called once
            mock_mqtt_client.publish.assert_called_once()

            # Get the call arguments
            call_args = mock_mqtt_client.publish.call_args
            topic = call_args[0][0]  # First positional argument
            payload = call_args[0][1]  # Second positional argument
            retain = call_args[1]["retain"]  # Keyword argument
            qos = call_args[1]["qos"]  # Keyword argument

            # Verify correct response topic
            expected_topic = f"iot/global/test-org/test-site/test-device/command/{command_str}/response"
            assert topic == expected_topic

            # Verify payload
            assert payload == test_payload

            # Verify QoS and retain from TopicConfig
            assert qos == 1  # Command responses use QoS 1
            assert retain is False  # Command responses don't retain

    def test_publish_response_invalid_command(self, dispatcher):
        """Test publish_response raises error for invalid command."""
        with pytest.raises(ValueError, match="No response topic for command"):
            dispatcher.publish_response("invalid_command", {"test": "data"})

    def test_publish_heartbeat_correct_topic_retain_qos(
        self, dispatcher, mock_mqtt_client
    ):
        """Test publish_heartbeat uses correct topic, retain=True, and QoS=1."""
        test_payload = {"status": "alive", "timestamp": "2023-01-01T00:00:00Z"}

        dispatcher.publish_heartbeat(test_payload)

        # Verify publish was called
        mock_mqtt_client.publish.assert_called_once()

        call_args = mock_mqtt_client.publish.call_args
        topic = call_args[0][0]  # First positional argument
        payload = call_args[0][1]  # Second positional argument
        retain = call_args[1]["retain"]  # Keyword argument
        qos = call_args[1]["qos"]  # Keyword argument

        # Verify heartbeat topic
        expected_topic = "iot/global/test-org/test-site/test-device/status/heartbeat"
        assert topic == expected_topic

        # Verify payload
        assert payload == test_payload

        # Verify heartbeat uses retain=True and QoS=1
        assert retain is True
        assert qos == 1

    def test_publish_point_bulk_serialization_and_publishing(
        self, dispatcher, mock_mqtt_client, sample_controller_point
    ):
        """Test publish_point_bulk correctly serializes points and publishes."""
        points = [sample_controller_point]

        result = dispatcher.publish_point_bulk(points)

        # Verify publish was called
        mock_mqtt_client.publish.assert_called_once()
        assert result is True  # Mock returns True

        call_args = mock_mqtt_client.publish.call_args
        topic = call_args[0][0]  # First positional argument
        payload = call_args[0][1]  # Second positional argument
        retain = call_args[1]["retain"]  # Keyword argument
        qos = call_args[1]["qos"]  # Keyword argument

        # Verify bulk topic
        expected_topic = "iot/global/test-org/test-site/test-device/bulk"
        assert topic == expected_topic

        # Verify bulk uses retain=False and QoS=0
        assert retain is False
        assert qos == 0

        # Verify payload structure
        assert "points" in payload
        assert len(payload["points"]) == 1

        # Verify serialization
        serialized_point = payload["points"][0]
        assert serialized_point["point_id"] == "test-point"
        assert serialized_point["present_value"] == 23.5
        assert serialized_point["status_flags"] == [
            "fault",
            "overridden",
        ]  # Converted from string
        assert serialized_point["priority_array"] == [
            None,
            None,
            50.0,
            None,
        ]  # Parsed JSON
        assert "created_at_unix_milli_timestamp" in serialized_point

    def test_update_mqtt_topics_updates_internal_state(self, dispatcher):
        """Test update_mqtt_topics updates controller and point IDs."""
        new_controller_id = "new-controller"
        new_point_id = "new-point"

        dispatcher.update_mqtt_topics(new_controller_id, new_point_id)

        assert dispatcher.controller_device_id == new_controller_id
        assert dispatcher.iot_device_point_id == new_point_id

        # Verify topics are updated
        assert new_controller_id in dispatcher.mqtt_topics.data.point.topic
        assert new_point_id in dispatcher.mqtt_topics.data.point.topic

    def test_command_map_contains_all_commands(self, dispatcher):
        """Test that command map contains all CommandNameEnum values."""
        expected_commands = [
            CommandNameEnum.get_config,
            CommandNameEnum.reboot,
            CommandNameEnum.set_value_to_point,
            CommandNameEnum.start_monitoring,
            CommandNameEnum.stop_monitoring,
        ]

        for command in expected_commands:
            assert command in dispatcher._command_map
            assert hasattr(dispatcher._command_map[command], "request")
            assert hasattr(dispatcher._command_map[command], "response")

    def test_request_and_response_topics_populated(self, dispatcher):
        """Test that request and response topic lists are properly populated."""
        assert len(dispatcher.request_topics) == 5
        assert len(dispatcher.response_topics) == 5

        # Verify all topics contain expected patterns
        for topic in dispatcher.request_topics:
            assert "/command/" in topic
            assert "/request" in topic

        for topic in dispatcher.response_topics:
            assert "/command/" in topic
            assert "/response" in topic
