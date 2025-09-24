"""
Test infrastructure validation for pytest setup.

User Story: As a developer, I want to verify pytest is working correctly
"""

import pytest
import asyncio
from unittest.mock import Mock


def test_simple_assertion():
    """Test: Simple assertion test to validate pytest execution"""
    assert True


@pytest.mark.asyncio
async def test_asyncio_functionality():
    """Test: Async test to validate pytest-asyncio plugin"""
    await asyncio.sleep(0.001)
    assert True


def test_mock_functionality():
    """Test: Mock test to validate unittest.mock integration"""
    mock_obj = Mock()
    mock_obj.test_method.return_value = "test_value"

    result = mock_obj.test_method()

    assert result == "test_value"
    mock_obj.test_method.assert_called_once()


def test_pytest_markers():
    """Test: Validate pytest markers work correctly"""
    assert hasattr(pytest.mark, "asyncio")
