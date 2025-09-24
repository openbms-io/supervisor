# Balena Integration Testing Checklist

## Pre-Deployment Testing

### ✅ Local Development Environment
- [ ] **Path Configuration Test**
  ```bash
  python -c "from src.config.paths import get_config_paths; print(get_config_paths())"
  ```
  - [ ] Native environment: Uses existing paths (`./bms_bacnet.db`, `~/.bms-iot-mqtt-config.json`)
  - [ ] Container simulation: Uses `/data/*` paths when `DOCKER_CONTAINER=true`

- [ ] **Import Validation**
  ```bash
  python -c "from src.config.paths import is_container_environment; print('OK')"
  python -c "from src.network.sqlmodel_client import get_engine; print('OK')"
  python -c "from src.network.mqtt_config import load_config; print('OK')"
  ```

- [ ] **CLI Functionality**
  ```bash
  python -m src.cli --help
  python -m src.cli config --help
  ```

### ✅ Docker Build Testing
- [ ] **Build Success**
  ```bash
  ./test-docker-build.sh
  ```
  - [ ] Multi-stage build completes without errors
  - [ ] ARM dependencies compile correctly
  - [ ] Final image size reasonable (<1GB)

- [ ] **Container Functionality**
  ```bash
  docker run --rm bms-iot-app:test python --version
  docker run --rm bms-iot-app:test python -c "import BAC0; print('BAC0 OK')"
  docker run --rm bms-iot-app:test check-provisioning
  ```

- [ ] **Path Detection in Container**
  ```bash
  docker run --rm bms-iot-app:test python -c "
  from src.config.paths import get_config_paths
  config = get_config_paths()
  assert config['is_container'] == True
  assert '/data/' in config['database_url']
  print('Container paths OK')
  "
  ```

### ✅ Docker Compose Testing
- [ ] **Local Stack**
  ```bash
  docker-compose up -d
  docker-compose logs
  docker-compose down
  ```
  - [ ] Container starts successfully
  - [ ] Shows provisioning instructions
  - [ ] Volume persistence works

## Balena Platform Testing

### ✅ Balena CLI Setup
- [ ] **CLI Installation**
  ```bash
  balena version
  balena auth whoami
  ```

- [ ] **Fleet Creation**
  ```bash
  balena app create testBmsFleet --type raspberrypi3
  balena fleets
  ```

### ✅ Deployment Testing
- [ ] **Manual Deployment**
  ```bash
  balena push testBmsFleet
  ```
  - [ ] Build completes successfully on Balena builders
  - [ ] ARM compilation works correctly
  - [ ] Image deploys to devices

- [ ] **Automated Deployment**
  ```bash
  ./deploy-to-balena.sh testBmsFleet
  ```
  - [ ] Script executes without errors
  - [ ] Shows appropriate success/failure messages

### ✅ Environment Variable Testing
- [ ] **Fleet Variables**
  ```bash
  balena env add MQTT_BROKER_HOST "test.broker.com" --application testBmsFleet
  balena env add DEBUG_MODE "true" --application testBmsFleet
  balena envs --application testBmsFleet
  ```

- [ ] **Device Variables**
  ```bash
  balena env add BMS_ORG_ID "test-org" --device <device-uuid>
  balena env add BMS_SITE_ID "test-site" --device <device-uuid>
  balena env add BMS_DEVICE_ID "test-device" --device <device-uuid>
  balena envs --device <device-uuid>
  ```

## Device Testing

### ✅ Device Provisioning
- [ ] **Auto-Provisioning**
  - [ ] Device detects environment variables
  - [ ] Automatic configuration executes successfully
  - [ ] Application starts after auto-provisioning

- [ ] **Manual Provisioning**
  ```bash
  balena ssh <device-uuid>
  python -m src.cli config setup --interactive
  ```
  - [ ] Interactive setup works correctly
  - [ ] Configuration persists after restart
  - [ ] Application starts after manual provisioning

### ✅ Application Functionality
- [ ] **Container Health**
  ```bash
  balena ssh <device-uuid>
  docker ps
  docker logs <container-id>
  ```
  - [ ] Container runs successfully
  - [ ] No critical errors in logs
  - [ ] Health checks pass

- [ ] **Database Persistence**
  ```bash
  ls -la /data/
  sqlite3 /data/bms_bacnet.db ".tables"
  ```
  - [ ] Database file exists and is accessible
  - [ ] Required tables are present
  - [ ] Data persists across container restarts

- [ ] **Configuration Files**
  ```bash
  cat /data/mqtt-config.json
  ls -la /data/emqxsl-ca.crt
  ```
  - [ ] MQTT configuration is correct
  - [ ] Certificate file is present and valid

### ✅ Network Connectivity
- [ ] **BACnet Communication**
  ```bash
  netstat -un | grep 47808
  # Test BACnet device discovery if devices available
  ```
  - [ ] BACnet port is listening
  - [ ] Device discovery works (if BACnet devices available)

- [ ] **MQTT Connectivity**
  - [ ] MQTT client connects successfully
  - [ ] Can publish test messages
  - [ ] TLS encryption works

### ✅ Monitoring & Management
- [ ] **Balena Dashboard**
  - [ ] Device appears online
  - [ ] Logs are accessible
  - [ ] Environment variables are applied

- [ ] **SSH Access**
  ```bash
  balena ssh <device-uuid>
  ```
  - [ ] Can access device remotely
  - [ ] Can run diagnostic commands
  - [ ] Can restart services if needed

- [ ] **System Resources**
  ```bash
  free -h
  df -h
  htop
  ```
  - [ ] Memory usage is reasonable
  - [ ] Disk space is sufficient
  - [ ] CPU usage is normal

## Performance Testing

### ✅ Resource Usage
- [ ] **Memory Consumption**
  - [ ] Container uses <500MB RAM under normal load
  - [ ] No significant memory leaks over 24 hours

- [ ] **CPU Usage**
  - [ ] Average CPU usage <50% during monitoring
  - [ ] No CPU spikes during normal operation

- [ ] **Network Usage**
  - [ ] MQTT traffic is reasonable
  - [ ] BACnet polling doesn't saturate network

### ✅ Reliability Testing
- [ ] **Container Restart**
  ```bash
  docker restart <container-id>
  ```
  - [ ] Application restarts cleanly
  - [ ] Configuration persists
  - [ ] Monitoring resumes automatically

- [ ] **Device Reboot**
  ```bash
  sudo reboot
  ```
  - [ ] Container starts automatically after reboot
  - [ ] All services resume correctly
  - [ ] Data integrity maintained

- [ ] **Network Interruption**
  - [ ] Application handles MQTT disconnections gracefully
  - [ ] Automatic reconnection works
  - [ ] Data buffering/queuing functions properly

## Final Validation

### ✅ End-to-End Testing
- [ ] **Complete Workflow**
  1. [ ] Deploy to Balena device
  2. [ ] Device auto-provisions or manual provision
  3. [ ] BACnet monitoring starts
  4. [ ] MQTT data publishing works
  5. [ ] Cloud API integration functions
  6. [ ] Device status reporting works

### ✅ Documentation Verification
- [ ] **Deployment Guide**
  - [ ] All commands in `BALENA_DEPLOYMENT.md` work correctly
  - [ ] Troubleshooting steps are accurate
  - [ ] Configuration examples are valid

- [ ] **Integration Summary**
  - [ ] All features listed in `INTEGRATION_COMPLETE.md` work
  - [ ] File structure is accurate
  - [ ] Testing procedures are complete

---

## Test Results Summary

| Test Category | Status | Notes |
|---------------|--------|-------|
| Local Development | ⏳ | |
| Docker Build | ⏳ | |
| Balena Deployment | ⏳ | |
| Device Provisioning | ⏳ | |
| Application Functionality | ⏳ | |
| Network Connectivity | ⏳ | |
| Performance | ⏳ | |
| Reliability | ⏳ | |

**Overall Status**: ⏳ Ready for Testing

**Test Environment**:
- Balena Fleet: `_____________________`
- Device UUID: `_____________________`
- Test Date: `_____________________`
- Tester: `_____________________`
