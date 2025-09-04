"""
Basic tests for BMS IoT Supervisor FastAPI app
"""

from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "BMS IoT Supervisor is running"}


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "bms-iot-supervisor"}


def test_status_endpoint():
    """Test status endpoint"""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "bms-iot-supervisor"
    assert data["version"] == "0.1.0"
    assert data["status"] == "running"


def test_deploy_config_endpoint():
    """Test config deployment endpoint"""
    test_config = {"test": "data"}
    response = client.post("/api/config/deploy", json=test_config)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "config_id" in data
