# Balena Deployment Guide for BMS IoT App

This guide covers deploying the BMS IoT Application to Raspberry Pi devices using Balena Cloud.

## Prerequisites

1. **Balena Account**: Sign up at [balena.io](https://balena.io)
2. **Balena CLI**: Install from [balena.io/docs/reference/cli/](https://balena.io/docs/reference/cli/)
3. **Raspberry Pi**: Supported models: Pi 3, Pi 4, Pi 400, or Compute Module 3

## Quick Start

### 1. Create Balena Application

```bash
# Login to Balena
balena login

# Create application
balena app create myBmsFleet --type raspberrypi3

# Clone and navigate to the project
cd apps/bms-iot-app
```

### 2. Deploy Application

```bash
# Push application to Balena
balena push myBmsFleet

# Or deploy to specific device
balena push <device-uuid>
```

### 3. Provision Device

After deployment, the device will wait for provisioning:

```bash
# SSH into the device
balena ssh <device-uuid>

# Run provisioning command
python -m src.cli config setup --interactive
```

Provide the following information:
- **Organization ID**: Your organization identifier
- **Site ID**: Site where this device is deployed
- **Device ID**: Unique identifier for this device
- **MQTT Configuration**: Broker details and credentials
- **API Credentials**: Client ID and secret key

### 4. Monitor Device

The container will automatically start after provisioning. Monitor via:
- Balena Dashboard: Device logs and status
- SSH access: `balena ssh <device-uuid>`
- Health checks: Automatic container health monitoring

## Configuration Management

### Fleet-Wide Variables

Set variables for all devices in the fleet:

```bash
# Set MQTT broker for all devices
balena env add MQTT_BROKER_HOST "your-broker.com" --application myBmsFleet

# Set API base URL
balena env add BMS_API_BASE_URL "https://api.yourdomain.com" --application myBmsFleet
```

### Device-Specific Variables

Set variables for individual devices:

```bash
# Set organization ID for specific device
balena env add BMS_ORG_ID "org123" --device <device-uuid>

# Set site ID for specific device
balena env add BMS_SITE_ID "site456" --device <device-uuid>

# Set device ID
balena env add BMS_DEVICE_ID "device789" --device <device-uuid>
```

### Available Configuration Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BMS_ORG_ID` | Organization ID | - | ✅ |
| `BMS_SITE_ID` | Site ID | - | ✅ |
| `BMS_DEVICE_ID` | Device ID | - | ✅ |
| `MQTT_BROKER_HOST` | MQTT broker hostname | t78ae18a.ala.us-east-1.emqxsl.com | ❌ |
| `MQTT_BROKER_PORT` | MQTT broker port | 8883 | ❌ |
| `MQTT_USE_TLS` | Enable TLS | true | ❌ |
| `BMS_API_BASE_URL` | API base URL | - | ❌ |
| `MONITORING_INTERVAL` | Monitoring interval (seconds) | 30 | ❌ |
| `DEBUG_MODE` | Enable debug logging | false | ❌ |

## Device Management

### Check Device Status

```bash
# List all devices
balena devices

# Get device information
balena device <device-uuid>

# View device logs
balena logs <device-uuid>
```

### Re-provision Device

To change device configuration:

```bash
# Option 1: SSH and re-run provisioning
balena ssh <device-uuid>
python -m src.cli config setup --interactive

# Option 2: Delete database and restart
rm /data/bms_bacnet.db
# Container will restart and wait for provisioning
```

### Update Application

```bash
# Deploy new version
balena push myBmsFleet

# Or target specific device
balena push <device-uuid>
```

## Troubleshooting

### Device Not Starting

1. **Check provisioning status**:
   ```bash
   balena ssh <device-uuid>
   python -m src.cli check-provisioning
   ```

2. **View container logs**:
   ```bash
   balena logs <device-uuid>
   ```

3. **Check environment variables**:
   ```bash
   balena envs --device <device-uuid>
   ```

### BACnet Communication Issues

1. **Verify network connectivity**:
   ```bash
   balena ssh <device-uuid>
   ping <bacnet-device-ip>
   ```

2. **Check BACnet port**:
   ```bash
   # BACnet uses UDP port 47808
   netstat -un | grep 47808
   ```

### MQTT Connection Issues

1. **Test MQTT connectivity**:
   ```bash
   balena ssh <device-uuid>
   # Check MQTT config
   cat /data/mqtt-config.json
   ```

2. **Verify certificates**:
   ```bash
   ls -la /data/emqxsl-ca.crt
   ```

### Performance Issues

1. **Check system resources**:
   ```bash
   balena ssh <device-uuid>
   htop
   free -h
   ```

2. **Adjust memory limits** in `balena.yml`:
   ```yaml
   services:
     bms-iot:
       mem_limit: 1024m  # Increase if needed
   ```

## Advanced Configuration

### Custom MQTT Broker

```bash
# Set custom broker
balena env add MQTT_BROKER_HOST "mqtt.yourcompany.com" --application myBmsFleet
balena env add MQTT_BROKER_PORT "8883" --application myBmsFleet
balena env add MQTT_USE_TLS "true" --application myBmsFleet
```

### Development Mode

Enable SSH access and debugging:

```bash
# Enable development mode
balena device <device-uuid> --enable-dev-mode

# SSH access
balena ssh <device-uuid>

# Enable debug logging
balena env add DEBUG_MODE "true" --device <device-uuid>
```

### Fleet Management

```bash
# Create device groups
balena tag set location "Building-A" --device <device-uuid>
balena tag set floor "3" --device <device-uuid>

# Filter devices by tags
balena devices --filter "location=Building-A"
```

## Support

For issues related to:
- **Balena platform**: [Balena Support](https://balena.io/support)
- **BMS IoT App**: Check application logs and configuration
- **BACnet connectivity**: Verify network and device configurations
