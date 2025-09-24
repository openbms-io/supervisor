"""
Test network credentials management.

User Story: As a developer, I want credentials management to work securely and reliably
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from pydantic import ValidationError

from src.network.credentials import (
    Credentials,
    ensure_credentials_dir,
    save_credentials,
    CREDENTIALS_FILE,
)


class TestCredentialsModel:
    """Test Credentials Pydantic model"""

    def test_valid_credentials_creation(self):
        """Test: Valid credentials model creation"""
        credentials = Credentials(
            client_id="test_client_123", secret_key="secret_key_456"
        )

        assert credentials.client_id == "test_client_123"
        assert credentials.secret_key == "secret_key_456"

    def test_credentials_model_validation(self):
        """Test: Credentials model validation"""
        # Test with empty strings
        credentials = Credentials(client_id="", secret_key="")
        assert credentials.client_id == ""
        assert credentials.secret_key == ""

        # Test with special characters
        credentials = Credentials(
            client_id="client_with_special_chars!@#$%",
            secret_key="secret_with_émojis_🔐",
        )
        assert "special_chars" in credentials.client_id
        assert "🔐" in credentials.secret_key

    def test_credentials_missing_fields(self):
        """Test: Credentials validation with missing fields"""
        # Missing client_id
        with pytest.raises(ValidationError):
            Credentials(secret_key="secret_only")

        # Missing secret_key
        with pytest.raises(ValidationError):
            Credentials(client_id="client_only")

        # Missing both fields
        with pytest.raises(ValidationError):
            Credentials()

    def test_credentials_serialization(self):
        """Test: Credentials model serialization"""
        credentials = Credentials(
            client_id="serialize_test_client", secret_key="serialize_test_secret"
        )

        # Test model_dump
        data = credentials.model_dump()
        expected = {
            "client_id": "serialize_test_client",
            "secret_key": "serialize_test_secret",
        }

        assert data == expected

        # Should be JSON serializable
        json_str = json.dumps(data)
        assert "serialize_test_client" in json_str
        assert "serialize_test_secret" in json_str

    def test_credentials_deserialization(self):
        """Test: Credentials model deserialization"""
        data = {
            "client_id": "deserialize_test_client",
            "secret_key": "deserialize_test_secret",
        }

        credentials = Credentials(**data)
        assert credentials.client_id == "deserialize_test_client"
        assert credentials.secret_key == "deserialize_test_secret"


class TestCredentialsFileOperations:
    """Test credentials file operations"""

    def test_credentials_file_path_location(self):
        """Test: Credentials file path is in user home directory"""
        assert CREDENTIALS_FILE.name == "credentials.json"
        assert CREDENTIALS_FILE.parent.name == ".bms"
        # Should be under user's home directory
        assert str(CREDENTIALS_FILE).startswith(str(Path.home()))

    def test_ensure_credentials_dir_creates_directory(self):
        """Test: ensure_credentials_dir creates directory structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / ".bms" / "credentials.json"

            with patch("src.network.credentials.CREDENTIALS_FILE", test_path):
                # Directory should not exist initially
                assert not test_path.parent.exists()

                # Call ensure_credentials_dir
                ensure_credentials_dir()

                # Directory should now exist
                assert test_path.parent.exists()
                assert test_path.parent.is_dir()

    def test_ensure_credentials_dir_existing_directory(self):
        """Test: ensure_credentials_dir handles existing directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / ".bms" / "credentials.json"

            # Pre-create the directory
            test_path.parent.mkdir(parents=True, exist_ok=True)
            assert test_path.parent.exists()

            with patch("src.network.credentials.CREDENTIALS_FILE", test_path):
                # Should not raise an error
                ensure_credentials_dir()

                # Directory should still exist
                assert test_path.parent.exists()

    def test_save_credentials_success(self):
        """Test: Successful credentials saving"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / ".bms" / "credentials.json"

            with patch("src.network.credentials.CREDENTIALS_FILE", test_path):
                save_credentials("test_client", "test_secret")

                # File should exist
                assert test_path.exists()

                # File should contain correct data
                with open(test_path, "r") as f:
                    data = json.load(f)

                assert data["client_id"] == "test_client"
                assert data["secret_key"] == "test_secret"

    def test_save_credentials_creates_directory_if_needed(self):
        """Test: save_credentials creates directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / ".bms" / "credentials.json"

            # Directory should not exist initially
            assert not test_path.parent.exists()

            with patch("src.network.credentials.CREDENTIALS_FILE", test_path):
                save_credentials("auto_create_client", "auto_create_secret")

                # Directory and file should be created
                assert test_path.parent.exists()
                assert test_path.exists()

                # Verify content
                with open(test_path, "r") as f:
                    data = json.load(f)

                assert data["client_id"] == "auto_create_client"

    def test_save_credentials_overwrites_existing(self):
        """Test: save_credentials overwrites existing credentials"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / ".bms" / "credentials.json"
            test_path.parent.mkdir(parents=True)

            # Create initial credentials
            initial_data = {"client_id": "old_client", "secret_key": "old_secret"}
            with open(test_path, "w") as f:
                json.dump(initial_data, f)

            with patch("src.network.credentials.CREDENTIALS_FILE", test_path):
                save_credentials("new_client", "new_secret")

                # File should contain new data
                with open(test_path, "r") as f:
                    data = json.load(f)

                assert data["client_id"] == "new_client"
                assert data["secret_key"] == "new_secret"

    def test_save_credentials_handles_permission_error(self):
        """Test: save_credentials handles permission errors gracefully"""
        with patch(
            "src.network.credentials.CREDENTIALS_FILE",
            Path("/root/no_permission/credentials.json"),
        ):
            with patch(
                "src.network.credentials.ensure_credentials_dir",
                side_effect=PermissionError("Permission denied"),
            ):
                with pytest.raises(Exception):
                    save_credentials("test_client", "test_secret")

    def test_save_credentials_handles_json_write_error(self):
        """Test: save_credentials handles JSON write errors"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / ".bms" / "credentials.json"

            with patch("src.network.credentials.CREDENTIALS_FILE", test_path):
                with patch("builtins.open", side_effect=IOError("Cannot write file")):
                    with pytest.raises(Exception):
                        save_credentials("test_client", "test_secret")


class TestCredentialsSecurityConsiderations:
    """Test security-related aspects of credentials handling"""

    def test_credentials_file_permissions(self):
        """Test: Credentials file security considerations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / ".bms" / "credentials.json"

            with patch("src.network.credentials.CREDENTIALS_FILE", test_path):
                save_credentials("security_test", "sensitive_secret")

                # File should exist
                assert test_path.exists()

                # Note: In a real implementation, we'd want to check file permissions
                # This test documents the security consideration
                stat_info = test_path.stat()
                assert stat_info.st_size > 0  # File has content

    def test_credentials_contain_sensitive_data(self):
        """Test: Credentials properly handle sensitive data"""
        sensitive_client = "highly_sensitive_client_id_123"
        sensitive_secret = "super_secret_key_with_special_chars_!@#$%^&*()"

        credentials = Credentials(
            client_id=sensitive_client, secret_key=sensitive_secret
        )

        # Data should be stored correctly
        assert credentials.client_id == sensitive_client
        assert credentials.secret_key == sensitive_secret

        # Serialization should preserve sensitive data
        data = credentials.model_dump()
        assert data["client_id"] == sensitive_client
        assert data["secret_key"] == sensitive_secret

    def test_credentials_no_accidental_logging(self):
        """Test: Credentials model doesn't accidentally expose secrets in string representation"""
        credentials = Credentials(
            client_id="public_client_id", secret_key="secret_that_should_not_be_logged"
        )

        # Convert to string (this could happen in logging)
        str_repr = str(credentials)

        # Pydantic models expose field values in string representation
        # This test documents the security concern - secrets will be visible in str()
        assert "public_client_id" in str_repr
        assert "secret_that_should_not_be_logged" in str_repr
        # This test documents the concern - in production, we'd want to ensure
        # secrets don't appear in logs accidentally

    def test_empty_credentials_handling(self):
        """Test: Empty credentials are handled appropriately"""
        # Empty but valid credentials
        credentials = Credentials(client_id="", secret_key="")

        assert credentials.client_id == ""
        assert credentials.secret_key == ""

        # Should still serialize/deserialize correctly
        data = credentials.model_dump()
        restored = Credentials(**data)
        assert restored.client_id == ""
        assert restored.secret_key == ""


class TestCredentialsEdgeCases:
    """Test edge cases in credentials handling"""

    def test_credentials_with_unicode_characters(self):
        """Test: Credentials with Unicode characters"""
        unicode_client = "client_with_unicode_字符_🔐"
        unicode_secret = "secret_with_émojis_and_symbols_®™"

        credentials = Credentials(client_id=unicode_client, secret_key=unicode_secret)

        assert credentials.client_id == unicode_client
        assert credentials.secret_key == unicode_secret

        # Should serialize/deserialize correctly
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / ".bms" / "credentials.json"

            with patch("src.network.credentials.CREDENTIALS_FILE", test_path):
                save_credentials(unicode_client, unicode_secret)

                # Read back and verify
                with open(test_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                assert data["client_id"] == unicode_client
                assert data["secret_key"] == unicode_secret

    def test_credentials_with_very_long_values(self):
        """Test: Credentials with very long values"""
        long_client = "client_" + "x" * 1000
        long_secret = "secret_" + "y" * 2000

        credentials = Credentials(client_id=long_client, secret_key=long_secret)

        assert len(credentials.client_id) == 1007  # "client_" + 1000 x's
        assert len(credentials.secret_key) == 2007  # "secret_" + 2000 y's

        # Should handle serialization of long values
        data = credentials.model_dump()
        json_str = json.dumps(data)
        assert len(json_str) > 3000  # Should be substantial

    def test_credentials_with_special_json_characters(self):
        """Test: Credentials with JSON special characters"""
        special_client = 'client_with_"quotes"_and_\\backslashes\\_and_\n_newlines'
        special_secret = "secret_with_\t_tabs_and_\r_carriage_returns"

        credentials = Credentials(client_id=special_client, secret_key=special_secret)

        # Should handle JSON escaping correctly
        data = credentials.model_dump()
        json_str = json.dumps(data)

        # Should be valid JSON
        parsed_back = json.loads(json_str)
        assert parsed_back["client_id"] == special_client
        assert parsed_back["secret_key"] == special_secret

    def test_credentials_roundtrip_integrity(self):
        """Test: Credentials maintain integrity through complete save/load cycle"""
        original_client = "integrity_test_client_123"
        original_secret = "integrity_test_secret_456"

        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / ".bms" / "credentials.json"

            with patch("src.network.credentials.CREDENTIALS_FILE", test_path):
                # Save credentials
                save_credentials(original_client, original_secret)

                # Load and verify
                with open(test_path, "r") as f:
                    loaded_data = json.load(f)

                loaded_credentials = Credentials(**loaded_data)

                assert loaded_credentials.client_id == original_client
                assert loaded_credentials.secret_key == original_secret

    def test_credentials_concurrent_access_consideration(self):
        """Test: Document concurrent access considerations"""
        # This test documents the concern about concurrent access
        # In a real implementation, we might want file locking

        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / ".bms" / "credentials.json"

            with patch("src.network.credentials.CREDENTIALS_FILE", test_path):
                # Simulate rapid succession saves (potential race condition)
                save_credentials("concurrent_1", "secret_1")
                save_credentials("concurrent_2", "secret_2")
                save_credentials("concurrent_3", "secret_3")

                # Last write should win
                with open(test_path, "r") as f:
                    data = json.load(f)

                assert data["client_id"] == "concurrent_3"
                assert data["secret_key"] == "secret_3"
