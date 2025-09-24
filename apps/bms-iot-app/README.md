# BMS IoT Application

A Python CLI application for managing IoT devices in a Building Management System with MQTT integration for monitoring data.

**Minimum Python Version**: 3.11.12
**Deployment Options**: Native, Docker, Balena Cloud (Raspberry Pi)

## 🚀 Quick Start

### Balena Cloud Deployment (Recommended for Production)
```bash
# Deploy to Balena fleet with auto-provisioning
./deploy-to-balena.sh myFleet org123 site456 device789
```
👉 **See [BALENA_DEPLOYMENT.md](BALENA_DEPLOYMENT.md) for complete deployment guide**

### Docker Deployment
```bash
# Build and test locally
./test-docker-build.sh
docker-compose up
```

### Native Development
```bash
# Install and run locally
pip install -e .
python -m src.cli config setup --interactive
python -m src.cli run-main
```

## Project Structure

```
bms-iot-app/
├── src/                # Source code directory
│   ├── __init__.py     # Package initialization
│   ├── cli.py          # CLI implementation
│   ├── monitor.py      # BACnet monitoring implementation
│   ├── mqtt_client.py  # MQTT client implementation
│   ├── mqtt_config.py  # MQTT configuration
│   └── mqtt_monitor_bridge.py # Bridge between BACnet and MQTT
├── tests/              # Test directory
├── emqxsl-ca.crt       # EMQX SSL certificate
├── pyproject.toml      # Project configuration
└── README.md           # This file
```

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Usage

The application provides several commands for BACnet monitoring and MQTT integration:

### BACnet Commands

```bash
# Run BACnet simulator
bms-iot run-bacnet-simulator

# Discover BACnet devices on the network
bms-iot discover-devices

# Get object list for a specific device
bms-iot get-object-list DEVICE_ID

# Monitor a specific device
bms-iot monitor-device DEVICE_ID --interval 5

# Monitor all devices on the network
bms-iot monitor-network --interval 5
```

### MQTT Integration

The application can publish monitoring data to an MQTT broker (like EMQX) with TLS enabled by default for security:

```bash
# Configure MQTT settings manually (TLS enabled by default)
bms-iot mqtt config --host emqx-broker.example.com --port 8883 --username user --password pass

# Disable TLS (not recommended)
bms-iot mqtt config --host mqtt-broker.example.com --port 1883 --no-tls

# Configure EMQX TLS connection (pre-configured hostname and port)
bms-iot mqtt config-emqx --username user --password pass

# Test MQTT connection
bms-iot mqtt test

# Show current MQTT configuration
bms-iot mqtt show

# Publish a test message to MQTT
bms-iot mqtt publish
bms-iot mqtt publish --topic sensors/temperature --temp 23.5 --humidity 60.2
bms-iot mqtt publish --topic events --message "System startup complete"

# Enable MQTT publishing with any monitoring command
bms-iot discover-devices --mqtt
bms-iot monitor-network --interval 5 --mqtt
```

### MQTT Configuration Options

#### General Options
- `--host`: MQTT broker hostname or IP (default: localhost)
- `--port`: MQTT broker port (default: 1883, recommended: 8883 for TLS)
- `--client-id`: MQTT client ID (default: bms-iot-client)
- `--username`: MQTT username (optional)
- `--password`: MQTT password (optional)
- `--tls/--no-tls`: Enable/disable TLS for MQTT connection (default: enabled)
- `--ca-cert`: Path to CA certificate file (optional, system CA certs used if not specified)
- `--topic-prefix`: MQTT topic prefix (default: bms/monitoring)

#### Publish Command Options
- `--topic, -t`: Topic to publish to (default: "test")
- `--message, -m`: Custom message content
- `--temp`: Temperature value
- `--humidity`: Humidity value

When no specific data is provided, the publish command will send a default test message with sample temperature and humidity values.

#### Security Note
TLS is enabled by default for all MQTT connections to ensure secure communication. It is strongly recommended to keep TLS enabled in production environments.

#### EMQX TLS Configuration
The application is pre-configured to connect to the EMQX broker at `t78ae18a.ala.us-east-1.emqxsl.com` on port `8883` using TLS. The CA certificate is included in the repository (`emqxsl-ca.crt`).

To use this configuration, simply run:
```bash
bms-iot mqtt config-emqx --username your_username --password your_password
```

### MQTT Topics

Data is published to the following topics:

- `bms/monitoring/device/{device_id}` - Device information
- `bms/monitoring/device/{device_id}/{object_type}/{object_id}` - Object data
- `bms/monitoring/test` - Test messages

## 📦 Deployment Options

### 🌐 Balena Cloud (Production)
Best for production deployment on Raspberry Pi devices with fleet management.

**Features:**
- ✅ Enterprise fleet management
- ✅ Over-the-air updates
- ✅ Remote SSH access
- ✅ Centralized logging and monitoring
- ✅ Auto-provisioning from environment variables

**Quick Deploy:**
```bash
./deploy-to-balena.sh myFleet org123 site456 device789
```

**Documentation:** [BALENA_DEPLOYMENT.md](BALENA_DEPLOYMENT.md)

### 🐳 Docker (Development & Testing)
Ideal for local development and testing.

**Features:**
- ✅ Consistent environment across platforms
- ✅ ARM/Pi compatibility testing
- ✅ Local development with volume mounting

**Quick Start:**
```bash
./test-docker-build.sh      # Build and test
docker-compose up           # Run locally
```

### 💻 Native (Development)
Direct installation for development and debugging.

**Features:**
- ✅ Direct access to Python debugging
- ✅ Fastest development iteration
- ✅ Easy dependency management

**Setup:**
```bash
pip install -e .
python -m src.cli config setup --interactive
python -m src.cli run-main
```

## 🧪 Testing

### Local Testing
```bash
# Test path configuration
python -c "from src.config.paths import get_config_paths; print(get_config_paths())"

# Test Docker build
./test-docker-build.sh

# Run pytest
pytest
```

### Integration Testing
```bash
# Complete testing checklist
# See TESTING_CHECKLIST.md for detailed validation steps
```

## Development

- Format code:
  ```bash
  black .
  isort .
  ```

## License

ISC
