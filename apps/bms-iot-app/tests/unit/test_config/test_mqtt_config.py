"""
Test MQTT configuration functionality.

User Story: As a developer, I want MQTT configuration to load and validate correctly
"""

import json
from unittest.mock import patch, mock_open
from src.network.mqtt_config import (
    MQTTConfig,
    save_config,
    load_config,
    CONFIG_FILE_PATH,
)


class TestMQTTConfig:
    """Test MQTTConfig Pydantic model"""

    def test_mqtt_config_default_values(self):
        """Test: MQTT config with default values"""
        config = MQTTConfig()

        assert config.broker_host == "localhost"
        assert config.broker_port == 1883
        assert config.client_id == "bms-iot-client"
        assert config.username is None
        assert config.password is None
        assert config.use_tls is True
        assert config.tls_ca_cert is None
        assert config.topic_prefix == "bms/monitoring"
        assert config.qos == 1
        assert config.keep_alive == 60
        assert config.reconnect_delay == 5

    def test_mqtt_config_custom_values(self):
        """Test: MQTT config with custom values"""
        config = MQTTConfig(
            broker_host="192.168.1.100",
            broker_port=8883,
            client_id="custom-client",
            username="user123",
            password="pass456",
            use_tls=False,
            tls_ca_cert="/path/to/cert.pem",
            topic_prefix="custom/topic",
            qos=2,
            keep_alive=120,
            reconnect_delay=10,
        )

        assert config.broker_host == "192.168.1.100"
        assert config.broker_port == 8883
        assert config.client_id == "custom-client"
        assert config.username == "user123"
        assert config.password == "pass456"
        assert config.use_tls is False
        assert config.tls_ca_cert == "/path/to/cert.pem"
        assert config.topic_prefix == "custom/topic"
        assert config.qos == 2
        assert config.keep_alive == 120
        assert config.reconnect_delay == 10

    def test_mqtt_config_validation(self):
        """Test: MQTT config validation"""
        # Valid QoS values
        config = MQTTConfig(qos=0)
        assert config.qos == 0

        config = MQTTConfig(qos=1)
        assert config.qos == 1

        config = MQTTConfig(qos=2)
        assert config.qos == 2

        # Valid port ranges
        config = MQTTConfig(broker_port=1)
        assert config.broker_port == 1

        config = MQTTConfig(broker_port=65535)
        assert config.broker_port == 65535

    def test_mqtt_config_model_dump(self):
        """Test: MQTT config model serialization"""
        config = MQTTConfig(
            broker_host="test.mqtt.broker", username="testuser", password="testpass"
        )

        # Test dump with all fields
        full_dict = config.model_dump()
        assert full_dict["broker_host"] == "test.mqtt.broker"
        assert full_dict["username"] == "testuser"
        assert full_dict["password"] == "testpass"

        # Test dump excluding password
        safe_dict = config.model_dump(exclude={"password"})
        assert safe_dict["broker_host"] == "test.mqtt.broker"
        assert safe_dict["username"] == "testuser"
        assert "password" not in safe_dict


class TestMQTTConfigFileOperations:
    """Test MQTT config file save and load operations"""

    def test_save_config_success(self):
        """Test: Successfully save MQTT config to file"""
        config = MQTTConfig(broker_host="test.broker", username="testuser")

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("json.dump") as mock_json_dump:
                result = save_config(config)

                assert result is True
                mock_file.assert_called_once_with(CONFIG_FILE_PATH, "w")
                mock_json_dump.assert_called_once()

                # Verify the config dict passed to json.dump
                call_args = mock_json_dump.call_args
                config_dict = call_args[0][0]  # First positional argument
                assert config_dict["broker_host"] == "test.broker"
                assert config_dict["username"] == "testuser"

    def test_save_config_excludes_none_password(self):
        """Test: Save config excludes password when it's None"""
        config = MQTTConfig(broker_host="test.broker", password=None)

        with patch("builtins.open", mock_open()):
            with patch("json.dump") as mock_json_dump:
                result = save_config(config)

                assert result is True
                call_args = mock_json_dump.call_args
                config_dict = call_args[0][0]
                assert "password" not in config_dict

    def test_save_config_includes_password_when_set(self):
        """Test: Save config includes password when it's set"""
        config = MQTTConfig(broker_host="test.broker", password="secret123")

        with patch("builtins.open", mock_open()):
            with patch("json.dump") as mock_json_dump:
                result = save_config(config)

                assert result is True
                call_args = mock_json_dump.call_args
                config_dict = call_args[0][0]
                assert config_dict["password"] == "secret123"

    def test_save_config_failure(self):
        """Test: Save config handles file write errors"""
        config = MQTTConfig()

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            result = save_config(config)

            assert result is False

    def test_load_config_file_not_exists(self):
        """Test: Load config returns default when file doesn't exist"""
        with patch("os.path.exists", return_value=False):
            config = load_config()

            assert isinstance(config, MQTTConfig)
            assert config.broker_host == "localhost"  # Default value
            assert config.broker_port == 1883  # Default value

    def test_load_config_success(self):
        """Test: Successfully load MQTT config from file"""
        test_config_data = {
            "broker_host": "saved.broker",
            "broker_port": 8883,
            "client_id": "saved-client",
            "username": "saveduser",
            "use_tls": False,
            "topic_prefix": "saved/topic",
        }

        with patch("os.path.exists", return_value=True):
            with patch(
                "builtins.open", mock_open(read_data=json.dumps(test_config_data))
            ):
                config = load_config()

                assert config.broker_host == "saved.broker"
                assert config.broker_port == 8883
                assert config.client_id == "saved-client"
                assert config.username == "saveduser"
                assert config.use_tls is False
                assert config.topic_prefix == "saved/topic"

    def test_load_config_invalid_json(self):
        """Test: Load config handles invalid JSON"""
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="invalid json")):
                config = load_config()

                # Should return default config when JSON is invalid
                assert isinstance(config, MQTTConfig)
                assert config.broker_host == "localhost"  # Default value

    def test_load_config_file_read_error(self):
        """Test: Load config handles file read errors"""
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", side_effect=IOError("File read error")):
                config = load_config()

                # Should return default config when file can't be read
                assert isinstance(config, MQTTConfig)
                assert config.broker_host == "localhost"  # Default value

    def test_load_config_partial_data(self):
        """Test: Load config handles partial configuration data"""
        partial_config_data = {
            "broker_host": "partial.broker",
            "broker_port": 9999,
            # Missing other fields
        }

        with patch("os.path.exists", return_value=True):
            with patch(
                "builtins.open", mock_open(read_data=json.dumps(partial_config_data))
            ):
                config = load_config()

                # Should use provided values and defaults for missing ones
                assert config.broker_host == "partial.broker"
                assert config.broker_port == 9999
                assert config.client_id == "bms-iot-client"  # Default
                assert config.use_tls is True  # Default


class TestMQTTConfigEdgeCases:
    """Test edge cases for MQTT configuration"""

    def test_config_file_path_expansion(self):
        """Test: Config file path uses proper home directory expansion"""
        # The CONFIG_FILE_PATH should be expanded
        assert CONFIG_FILE_PATH.startswith("/")  # Should be absolute path
        assert "~" not in CONFIG_FILE_PATH  # Should be expanded

    def test_mqtt_config_with_empty_strings(self):
        """Test: MQTT config handles empty strings appropriately"""
        config = MQTTConfig(
            broker_host="",
            client_id="",
            topic_prefix="",  # Empty string
        )

        assert config.broker_host == ""
        assert config.client_id == ""
        assert config.topic_prefix == ""

    def test_mqtt_config_with_special_characters(self):
        """Test: MQTT config handles special characters"""
        config = MQTTConfig(
            broker_host="mqtt-broker.example.com",
            client_id="client-with-dashes_and_underscores",
            username="user@domain.com",
            topic_prefix="topic/with/slashes",
            tls_ca_cert="/path/with spaces/cert.pem",
        )

        assert config.broker_host == "mqtt-broker.example.com"
        assert config.client_id == "client-with-dashes_and_underscores"
        assert config.username == "user@domain.com"
        assert config.topic_prefix == "topic/with/slashes"
        assert config.tls_ca_cert == "/path/with spaces/cert.pem"

    def test_save_load_roundtrip(self):
        """Test: Save and load config maintains data integrity"""
        original_config = MQTTConfig(
            broker_host="roundtrip.test",
            broker_port=12345,
            client_id="roundtrip-client",
            username="roundtripuser",
            password="roundtrippass",
            use_tls=False,
            topic_prefix="roundtrip/test",
            qos=2,
        )

        # Mock file operations for roundtrip test
        saved_data = None

        def mock_write(data):
            nonlocal saved_data
            saved_data = data

        def mock_read():
            return saved_data

        with patch("builtins.open", mock_open()):
            with patch(
                "json.dump",
                side_effect=lambda data, f, **kwargs: mock_write(json.dumps(data)),
            ):
                # Save config
                result = save_config(original_config)
                assert result is True

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_read())):
                # Load config
                loaded_config = load_config()

                # Compare key fields (password excluded in save if None, but we set it)
                assert loaded_config.broker_host == original_config.broker_host
                assert loaded_config.broker_port == original_config.broker_port
                assert loaded_config.client_id == original_config.client_id
                assert loaded_config.username == original_config.username
                assert loaded_config.use_tls == original_config.use_tls
                assert loaded_config.topic_prefix == original_config.topic_prefix
                assert loaded_config.qos == original_config.qos
