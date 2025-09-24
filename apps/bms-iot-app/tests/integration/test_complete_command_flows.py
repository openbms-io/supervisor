"""
Test complete end-to-end command flows across all actors.

User Story: As a system operator, I want to verify that complete command flows
work correctly from initiation through all actors to completion.
"""

import pytest
import asyncio
import time
import sys
import uuid

# Add the fixtures directory to the path
sys.path.insert(
    0, "/Users/amol/Documents/ai-projects/bms-project/apps/bms-iot-app/tests"
)

from fixtures.actor_test_harness import ActorTestHarness


class TestEndToEndMonitoringFlow:
    """Test complete monitoring flow from MQTT command to cloud upload"""

    @pytest.mark.asyncio
    async def test_complete_start_monitoring_flow(self):
        """Test: Complete flow from START_MONITORING command to data upload"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        command_id = str(uuid.uuid4())
        device_id = "BAC_DEVICE_001"

        # Step 1: External system sends START_MONITORING via MQTT
        start_command = {
            "id": command_id,
            "type": "START_MONITORING_REQUEST",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "timestamp": time.time(),
            "payload": {
                "device_id": device_id,
                "monitoring_config": {
                    "points": ["temperature", "humidity", "pressure"],
                    "interval_seconds": 30,
                    "upload_interval": 60,
                    "batch_size": 10,
                },
            },
        }

        await harness.send_message(start_command)
        await asyncio.sleep(0.1)

        # Step 2: BACnet acknowledges command
        bacnet_ack = {
            "type": "COMMAND_ACKNOWLEDGMENT",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "command_id": command_id,
                "status": "accepted",
                "device_id": device_id,
                "message": "Monitoring configuration applied",
            },
        }

        await harness.send_message(bacnet_ack)
        await asyncio.sleep(0.1)

        # Step 3: BACnet starts collecting data
        collected_data = {
            "type": "DATA_COLLECTED",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_id": device_id,
                "command_id": command_id,
                "collection_timestamp": time.time(),
                "points": [
                    {"name": "temperature", "value": 23.5, "unit": "celsius"},
                    {"name": "humidity", "value": 45.2, "unit": "percent"},
                    {"name": "pressure", "value": 101.3, "unit": "kPa"},
                ],
            },
        }

        await harness.send_message(collected_data)
        await asyncio.sleep(0.1)

        # Step 4: Uploader processes and uploads data
        upload_result = {
            "type": "UPLOAD_COMPLETE",
            "sender": "uploader",
            "receiver": "mqtt",
            "payload": {
                "command_id": command_id,
                "device_id": device_id,
                "upload_status": "success",
                "records_uploaded": 3,
                "upload_timestamp": time.time(),
                "cloud_location": "s3://iot-data/device_001/data.json",
            },
        }

        await harness.send_message(upload_result)
        await asyncio.sleep(0.1)

        # Step 5: MQTT publishes success notification
        success_notification = {
            "type": "MONITORING_STATUS_UPDATE",
            "sender": "mqtt",
            "receiver": "BROADCAST",
            "payload": {
                "command_id": command_id,
                "device_id": device_id,
                "status": "monitoring_active",
                "data_flow": "operational",
                "last_upload": time.time(),
            },
        }

        await harness.send_message(success_notification)
        await asyncio.sleep(0.1)

        # Verify complete flow
        messages = harness.messages

        # Check command was received by BACnet
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        start_msg = next(
            (m for m in bacnet_messages if m.get("id") == command_id), None
        )
        assert start_msg is not None
        assert start_msg["type"] == "START_MONITORING_REQUEST"

        # Check acknowledgment was sent to MQTT
        mqtt_messages = harness.get_actor_messages("mqtt")
        ack_msg = next(
            (m for m in mqtt_messages if m["type"] == "COMMAND_ACKNOWLEDGMENT"), None
        )
        assert ack_msg is not None
        assert ack_msg["payload"]["status"] == "accepted"

        # Check data was uploaded
        uploader_messages = harness.get_actor_messages("uploader")
        data_msg = next(
            (m for m in uploader_messages if m["type"] == "DATA_COLLECTED"), None
        )
        assert data_msg is not None
        assert len(data_msg["payload"]["points"]) == 3

        # Check upload confirmation
        upload_msg = next(
            (m for m in mqtt_messages if m["type"] == "UPLOAD_COMPLETE"), None
        )
        assert upload_msg is not None
        assert upload_msg["payload"]["upload_status"] == "success"

        # Check broadcast notification
        broadcast_msgs = [m for m in messages if m.get("receiver") == "BROADCAST"]
        assert len(broadcast_msgs) > 0

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_complete_stop_monitoring_flow(self):
        """Test: Complete flow for stopping monitoring"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        command_id = str(uuid.uuid4())
        device_id = "BAC_DEVICE_001"

        # Step 1: Stop monitoring command
        stop_command = {
            "id": command_id,
            "type": "STOP_MONITORING_REQUEST",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": device_id,
                "reason": "scheduled_maintenance",
                "flush_buffer": True,
            },
        }

        await harness.send_message(stop_command)
        await asyncio.sleep(0.1)

        # Step 2: BACnet flushes remaining data
        flush_data = {
            "type": "BUFFER_FLUSH",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_id": device_id,
                "command_id": command_id,
                "buffered_records": 5,
                "final_batch": True,
                "points": [
                    {"name": "temperature", "value": 24.0, "timestamp": time.time()}
                ],
            },
        }

        await harness.send_message(flush_data)
        await asyncio.sleep(0.1)

        # Step 3: Uploader confirms final upload
        final_upload = {
            "type": "FINAL_UPLOAD_COMPLETE",
            "sender": "uploader",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": device_id,
                "command_id": command_id,
                "final_records": 5,
                "buffer_cleared": True,
            },
        }

        await harness.send_message(final_upload)
        await asyncio.sleep(0.1)

        # Step 4: BACnet confirms monitoring stopped
        stop_confirmation = {
            "type": "MONITORING_STOPPED",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "device_id": device_id,
                "command_id": command_id,
                "stopped_at": time.time(),
                "final_data_uploaded": True,
            },
        }

        await harness.send_message(stop_confirmation)
        await asyncio.sleep(0.1)

        # Verify flow
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        stop_msg = next(
            (m for m in bacnet_messages if m["type"] == "STOP_MONITORING_REQUEST"), None
        )
        assert stop_msg is not None
        assert stop_msg["payload"]["flush_buffer"] is True

        uploader_messages = harness.get_actor_messages("uploader")
        flush_msg = next(
            (m for m in uploader_messages if m["type"] == "BUFFER_FLUSH"), None
        )
        assert flush_msg is not None
        assert flush_msg["payload"]["final_batch"] is True

        mqtt_messages = harness.get_actor_messages("mqtt")
        stopped_msg = next(
            (m for m in mqtt_messages if m["type"] == "MONITORING_STOPPED"), None
        )
        assert stopped_msg is not None
        assert stopped_msg["payload"]["final_data_uploaded"] is True

        await harness.cleanup()


class TestConfigurationUpdateFlow:
    """Test complete configuration update flows"""

    @pytest.mark.asyncio
    async def test_device_configuration_update_flow(self):
        """Test: Complete device configuration update flow"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        config_id = str(uuid.uuid4())
        device_id = "BAC_DEVICE_001"

        # Step 1: Configuration update request via MQTT
        config_update = {
            "id": config_id,
            "type": "CONFIG_UPDATE_REQUEST",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": device_id,
                "config_version": "2.0.1",
                "configuration": {
                    "sampling_rate": 15,
                    "points": [
                        {"name": "temperature", "enabled": True, "threshold": 30},
                        {"name": "humidity", "enabled": True, "threshold": 70},
                        {"name": "co2", "enabled": False},
                    ],
                    "alarm_settings": {
                        "temperature_high": 35,
                        "temperature_low": 10,
                        "humidity_high": 80,
                    },
                },
            },
        }

        await harness.send_message(config_update)
        await asyncio.sleep(0.1)

        # Step 2: BACnet validates configuration
        validation_result = {
            "type": "CONFIG_VALIDATION",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "config_id": config_id,
                "device_id": device_id,
                "validation_status": "valid",
                "warnings": ["co2 sensor will be disabled"],
                "estimated_impact": "minimal",
            },
        }

        await harness.send_message(validation_result)
        await asyncio.sleep(0.1)

        # Step 3: BACnet applies configuration
        config_applied = {
            "type": "CONFIG_APPLIED",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "config_id": config_id,
                "device_id": device_id,
                "applied_at": time.time(),
                "changes_made": [
                    "sampling_rate: 30 -> 15",
                    "co2 monitoring: enabled -> disabled",
                ],
            },
        }

        await harness.send_message(config_applied)
        await asyncio.sleep(0.1)

        # Step 4: Upload configuration to cloud for audit
        config_audit = {
            "type": "CONFIG_AUDIT_UPLOAD",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "config_id": config_id,
                "device_id": device_id,
                "config_version": "2.0.1",
                "audit_data": {
                    "previous_version": "2.0.0",
                    "changed_by": "system",
                    "change_timestamp": time.time(),
                    "configuration": config_update["payload"]["configuration"],
                },
            },
        }

        await harness.send_message(config_audit)
        await asyncio.sleep(0.1)

        # Step 5: Uploader confirms audit trail
        audit_confirmation = {
            "type": "AUDIT_UPLOAD_COMPLETE",
            "sender": "uploader",
            "receiver": "mqtt",
            "payload": {
                "config_id": config_id,
                "device_id": device_id,
                "audit_stored": True,
                "audit_id": "AUD_" + config_id,
            },
        }

        await harness.send_message(audit_confirmation)
        await asyncio.sleep(0.1)

        # Verify configuration flow
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        config_msg = next(
            (m for m in bacnet_messages if m.get("id") == config_id), None
        )
        assert config_msg is not None
        assert config_msg["payload"]["config_version"] == "2.0.1"

        mqtt_messages = harness.get_actor_messages("mqtt")
        validation_msg = next(
            (m for m in mqtt_messages if m["type"] == "CONFIG_VALIDATION"), None
        )
        assert validation_msg is not None
        assert validation_msg["payload"]["validation_status"] == "valid"

        applied_msg = next(
            (m for m in mqtt_messages if m["type"] == "CONFIG_APPLIED"), None
        )
        assert applied_msg is not None
        assert len(applied_msg["payload"]["changes_made"]) == 2

        uploader_messages = harness.get_actor_messages("uploader")
        audit_msg = next(
            (m for m in uploader_messages if m["type"] == "CONFIG_AUDIT_UPLOAD"), None
        )
        assert audit_msg is not None
        assert audit_msg["payload"]["config_version"] == "2.0.1"

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_bulk_configuration_update_flow(self):
        """Test: Bulk configuration update for multiple devices"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        bulk_config_id = str(uuid.uuid4())
        device_ids = ["BAC_DEVICE_001", "BAC_DEVICE_002", "BAC_DEVICE_003"]

        # Step 1: Bulk configuration request
        bulk_config = {
            "id": bulk_config_id,
            "type": "BULK_CONFIG_UPDATE",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_ids": device_ids,
                "apply_mode": "sequential",
                "rollback_on_failure": True,
                "configuration": {
                    "global_settings": {"sampling_rate": 20, "upload_interval": 120}
                },
            },
        }

        await harness.send_message(bulk_config)
        await asyncio.sleep(0.1)

        # Step 2: BACnet processes each device
        for idx, device_id in enumerate(device_ids):
            device_result = {
                "type": "DEVICE_CONFIG_RESULT",
                "sender": "bacnet_monitoring",
                "receiver": "mqtt",
                "payload": {
                    "bulk_config_id": bulk_config_id,
                    "device_id": device_id,
                    "device_index": idx + 1,
                    "total_devices": len(device_ids),
                    "status": "success",
                    "applied_at": time.time() + idx,
                },
            }
            await harness.send_message(device_result)
            await asyncio.sleep(0.05)

        # Step 3: BACnet sends bulk completion
        bulk_complete = {
            "type": "BULK_CONFIG_COMPLETE",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "bulk_config_id": bulk_config_id,
                "total_devices": len(device_ids),
                "successful": len(device_ids),
                "failed": 0,
                "completion_time": time.time(),
            },
        }

        await harness.send_message(bulk_complete)
        await asyncio.sleep(0.1)

        # Verify bulk update flow
        mqtt_messages = harness.get_actor_messages("mqtt")

        # Check individual device results
        device_results = [
            m for m in mqtt_messages if m["type"] == "DEVICE_CONFIG_RESULT"
        ]
        assert len(device_results) == 3
        for result in device_results:
            assert result["payload"]["status"] == "success"

        # Check bulk completion
        bulk_msg = next(
            (m for m in mqtt_messages if m["type"] == "BULK_CONFIG_COMPLETE"), None
        )
        assert bulk_msg is not None
        assert bulk_msg["payload"]["successful"] == 3
        assert bulk_msg["payload"]["failed"] == 0

        await harness.cleanup()


class TestAlarmAndEventFlow:
    """Test complete alarm and event handling flows"""

    @pytest.mark.asyncio
    async def test_critical_alarm_flow(self):
        """Test: Critical alarm detection and escalation flow"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        alarm_id = "ALM_" + str(uuid.uuid4())
        device_id = "BAC_DEVICE_001"

        # Step 1: BACnet detects critical condition
        alarm_detection = {
            "id": alarm_id,
            "type": "CRITICAL_ALARM_DETECTED",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "priority": "critical",
            "payload": {
                "device_id": device_id,
                "alarm_type": "TEMPERATURE_CRITICAL",
                "severity": "critical",
                "value": 45.8,
                "threshold": 40.0,
                "point_name": "zone_temperature",
                "detected_at": time.time(),
            },
        }

        await harness.send_message(alarm_detection)
        await asyncio.sleep(0.1)

        # Step 2: MQTT broadcasts alarm to all systems
        alarm_broadcast = {
            "type": "CRITICAL_ALARM_BROADCAST",
            "sender": "mqtt",
            "receiver": "BROADCAST",
            "priority": "critical",
            "payload": {
                "alarm_id": alarm_id,
                "device_id": device_id,
                "immediate_action_required": True,
                "notification_sent_to": ["operations", "maintenance", "management"],
            },
        }

        await harness.send_message(alarm_broadcast)
        await asyncio.sleep(0.1)

        # Step 3: Upload alarm to cloud immediately
        alarm_upload = {
            "type": "CRITICAL_ALARM_UPLOAD",
            "sender": "mqtt",
            "receiver": "uploader",
            "priority": "critical",
            "payload": {
                "alarm_id": alarm_id,
                "device_id": device_id,
                "upload_priority": "immediate",
                "alarm_data": alarm_detection["payload"],
            },
        }

        await harness.send_message(alarm_upload)
        await asyncio.sleep(0.1)

        # Step 4: Uploader confirms critical upload
        upload_confirm = {
            "type": "CRITICAL_UPLOAD_COMPLETE",
            "sender": "uploader",
            "receiver": "mqtt",
            "payload": {
                "alarm_id": alarm_id,
                "uploaded_at": time.time(),
                "escalation_triggered": True,
                "incident_id": "INC_" + alarm_id,
            },
        }

        await harness.send_message(upload_confirm)
        await asyncio.sleep(0.1)

        # Step 5: BACnet takes corrective action
        corrective_action = {
            "type": "CORRECTIVE_ACTION_TAKEN",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "alarm_id": alarm_id,
                "device_id": device_id,
                "action": "emergency_shutdown",
                "action_result": "success",
                "new_value": 25.0,
                "safe_mode_activated": True,
            },
        }

        await harness.send_message(corrective_action)
        await asyncio.sleep(0.1)

        # Verify critical alarm flow
        mqtt_messages = harness.get_actor_messages("mqtt")
        alarm_msg = next((m for m in mqtt_messages if m.get("id") == alarm_id), None)
        assert alarm_msg is not None
        assert alarm_msg["payload"]["severity"] == "critical"

        # Check broadcast
        all_messages = harness.messages
        broadcast_msgs = [
            m for m in all_messages if m.get("type") == "CRITICAL_ALARM_BROADCAST"
        ]
        assert len(broadcast_msgs) > 0
        assert broadcast_msgs[0]["payload"]["immediate_action_required"] is True

        # Check upload
        uploader_messages = harness.get_actor_messages("uploader")
        critical_upload = next(
            (m for m in uploader_messages if m["type"] == "CRITICAL_ALARM_UPLOAD"), None
        )
        assert critical_upload is not None
        assert critical_upload["payload"]["upload_priority"] == "immediate"

        # Check corrective action
        action_msg = next(
            (m for m in mqtt_messages if m["type"] == "CORRECTIVE_ACTION_TAKEN"), None
        )
        assert action_msg is not None
        assert action_msg["payload"]["action"] == "emergency_shutdown"
        assert action_msg["payload"]["safe_mode_activated"] is True

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_alarm_acknowledgment_flow(self):
        """Test: Alarm acknowledgment and resolution flow"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        alarm_id = "ALM_" + str(uuid.uuid4())
        device_id = "BAC_DEVICE_001"

        # Step 1: Alarm occurs
        alarm_event = {
            "id": alarm_id,
            "type": "ALARM_RAISED",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "device_id": device_id,
                "alarm_type": "PRESSURE_HIGH",
                "value": 120,
                "threshold": 110,
            },
        }

        await harness.send_message(alarm_event)
        await asyncio.sleep(0.1)

        # Step 2: Operator acknowledges via MQTT
        alarm_ack = {
            "type": "ALARM_ACKNOWLEDGMENT",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {
                "alarm_id": alarm_id,
                "acknowledged_by": "operator_123",
                "acknowledgment_time": time.time(),
                "action_plan": "manual_pressure_release",
            },
        }

        await harness.send_message(alarm_ack)
        await asyncio.sleep(0.1)

        # Step 3: BACnet monitors resolution
        monitoring_update = {
            "type": "ALARM_MONITORING",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "alarm_id": alarm_id,
                "current_value": 105,
                "trending": "decreasing",
                "estimated_resolution": 300,  # seconds
            },
        }

        await harness.send_message(monitoring_update)
        await asyncio.sleep(0.1)

        # Step 4: Alarm resolved
        alarm_resolved = {
            "type": "ALARM_RESOLVED",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "alarm_id": alarm_id,
                "resolved_at": time.time(),
                "final_value": 95,
                "duration_seconds": 600,
                "auto_cleared": False,
            },
        }

        await harness.send_message(alarm_resolved)
        await asyncio.sleep(0.1)

        # Step 5: Upload resolution for records
        resolution_upload = {
            "type": "ALARM_RESOLUTION_UPLOAD",
            "sender": "mqtt",
            "receiver": "uploader",
            "payload": {
                "alarm_id": alarm_id,
                "resolution_data": {
                    "duration": 600,
                    "acknowledged": True,
                    "resolved_by": "manual_intervention",
                    "root_cause": "valve_malfunction",
                },
            },
        }

        await harness.send_message(resolution_upload)
        await asyncio.sleep(0.1)

        # Verify acknowledgment flow
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        ack_msg = next(
            (m for m in bacnet_messages if m["type"] == "ALARM_ACKNOWLEDGMENT"), None
        )
        assert ack_msg is not None
        assert ack_msg["payload"]["acknowledged_by"] == "operator_123"

        mqtt_messages = harness.get_actor_messages("mqtt")
        resolved_msg = next(
            (m for m in mqtt_messages if m["type"] == "ALARM_RESOLVED"), None
        )
        assert resolved_msg is not None
        assert resolved_msg["payload"]["auto_cleared"] is False

        uploader_messages = harness.get_actor_messages("uploader")
        resolution_msg = next(
            (m for m in uploader_messages if m["type"] == "ALARM_RESOLUTION_UPLOAD"),
            None,
        )
        assert resolution_msg is not None
        assert (
            resolution_msg["payload"]["resolution_data"]["resolved_by"]
            == "manual_intervention"
        )

        await harness.cleanup()


class TestDataCollectionAndAnalyticsFlow:
    """Test complete data collection and analytics flows"""

    @pytest.mark.asyncio
    async def test_scheduled_data_collection_flow(self):
        """Test: Scheduled data collection and aggregation flow"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        schedule_id = str(uuid.uuid4())
        device_id = "BAC_DEVICE_001"

        # Step 1: Schedule data collection
        schedule_request = {
            "id": schedule_id,
            "type": "SCHEDULE_DATA_COLLECTION",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": device_id,
                "schedule_type": "recurring",
                "interval_minutes": 15,
                "duration_hours": 24,
                "points": ["temperature", "humidity", "energy"],
                "aggregation": "average",
            },
        }

        await harness.send_message(schedule_request)
        await asyncio.sleep(0.1)

        # Step 2: BACnet confirms schedule
        schedule_confirm = {
            "type": "SCHEDULE_CONFIRMED",
            "sender": "bacnet_monitoring",
            "receiver": "mqtt",
            "payload": {
                "schedule_id": schedule_id,
                "next_collection": time.time() + 900,
                "total_collections": 96,
            },
        }

        await harness.send_message(schedule_confirm)
        await asyncio.sleep(0.1)

        # Step 3: Simulate first collection
        collection_data = {
            "type": "SCHEDULED_DATA_COLLECTED",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "schedule_id": schedule_id,
                "collection_number": 1,
                "timestamp": time.time(),
                "aggregated_data": {
                    "temperature": {"avg": 23.5, "min": 22.0, "max": 25.0},
                    "humidity": {"avg": 45.0, "min": 42.0, "max": 48.0},
                    "energy": {"total_kwh": 15.5, "peak_kw": 5.2},
                },
            },
        }

        await harness.send_message(collection_data)
        await asyncio.sleep(0.1)

        # Step 4: Uploader processes and stores
        analytics_result = {
            "type": "ANALYTICS_PROCESSED",
            "sender": "uploader",
            "receiver": "mqtt",
            "payload": {
                "schedule_id": schedule_id,
                "analytics": {
                    "trend": "stable",
                    "anomalies": [],
                    "efficiency_score": 0.92,
                    "recommendations": ["maintain_current_settings"],
                },
            },
        }

        await harness.send_message(analytics_result)
        await asyncio.sleep(0.1)

        # Verify scheduled collection flow
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        schedule_msg = next(
            (m for m in bacnet_messages if m.get("id") == schedule_id), None
        )
        assert schedule_msg is not None
        assert schedule_msg["payload"]["interval_minutes"] == 15

        uploader_messages = harness.get_actor_messages("uploader")
        collection_msg = next(
            (m for m in uploader_messages if m["type"] == "SCHEDULED_DATA_COLLECTED"),
            None,
        )
        assert collection_msg is not None
        assert "temperature" in collection_msg["payload"]["aggregated_data"]

        mqtt_messages = harness.get_actor_messages("mqtt")
        analytics_msg = next(
            (m for m in mqtt_messages if m["type"] == "ANALYTICS_PROCESSED"), None
        )
        assert analytics_msg is not None
        assert analytics_msg["payload"]["analytics"]["efficiency_score"] == 0.92

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_real_time_analytics_flow(self):
        """Test: Real-time analytics and alerting flow"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        session_id = str(uuid.uuid4())
        device_id = "BAC_DEVICE_001"

        # Step 1: Enable real-time analytics
        enable_analytics = {
            "id": session_id,
            "type": "ENABLE_REALTIME_ANALYTICS",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": device_id,
                "analytics_type": "anomaly_detection",
                "sensitivity": "high",
                "points": ["temperature", "vibration"],
                "window_size": 60,  # seconds
            },
        }

        await harness.send_message(enable_analytics)
        await asyncio.sleep(0.1)

        # Step 2: Stream data points
        for i in range(3):
            data_point = {
                "type": "REALTIME_DATA",
                "sender": "bacnet_monitoring",
                "receiver": "uploader",
                "payload": {
                    "session_id": session_id,
                    "device_id": device_id,
                    "timestamp": time.time() + i * 10,
                    "values": {
                        "temperature": 23.5 + i * 0.5,
                        "vibration": 0.1 + i * 0.05,
                    },
                },
            }
            await harness.send_message(data_point)
            await asyncio.sleep(0.05)

        # Step 3: Anomaly detected
        anomaly_alert = {
            "type": "ANOMALY_DETECTED",
            "sender": "uploader",
            "receiver": "mqtt",
            "payload": {
                "session_id": session_id,
                "device_id": device_id,
                "anomaly_type": "sudden_increase",
                "affected_point": "vibration",
                "confidence": 0.85,
                "recommendation": "investigate_mechanical_issue",
            },
        }

        await harness.send_message(anomaly_alert)
        await asyncio.sleep(0.1)

        # Step 4: MQTT triggers investigation
        investigation_request = {
            "type": "INVESTIGATE_ANOMALY",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {
                "session_id": session_id,
                "device_id": device_id,
                "deep_scan": True,
                "additional_points": ["motor_current", "bearing_temperature"],
            },
        }

        await harness.send_message(investigation_request)
        await asyncio.sleep(0.1)

        # Verify real-time analytics flow
        uploader_messages = harness.get_actor_messages("uploader")
        realtime_data = [m for m in uploader_messages if m["type"] == "REALTIME_DATA"]
        assert len(realtime_data) == 3

        mqtt_messages = harness.get_actor_messages("mqtt")
        anomaly_msg = next(
            (m for m in mqtt_messages if m["type"] == "ANOMALY_DETECTED"), None
        )
        assert anomaly_msg is not None
        assert anomaly_msg["payload"]["confidence"] == 0.85

        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        investigate_msg = next(
            (m for m in bacnet_messages if m["type"] == "INVESTIGATE_ANOMALY"), None
        )
        assert investigate_msg is not None
        assert investigate_msg["payload"]["deep_scan"] is True

        await harness.cleanup()


class TestHeartbeatAndHealthCheckFlow:
    """Test complete heartbeat and health monitoring flows"""

    @pytest.mark.asyncio
    async def test_system_health_check_flow(self):
        """Test: Complete system health check flow across all actors"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        health_check_id = str(uuid.uuid4())

        # Step 1: Initiate health check
        health_check = {
            "id": health_check_id,
            "type": "SYSTEM_HEALTH_CHECK",
            "sender": "heartbeat",
            "receiver": "BROADCAST",
            "payload": {"check_type": "comprehensive", "include_diagnostics": True},
        }

        await harness.send_message(health_check)
        await asyncio.sleep(0.1)

        # Step 2: Each actor responds with health status
        actors = ["mqtt", "bacnet_monitoring", "uploader"]
        for actor in actors:
            health_response = {
                "type": "HEALTH_STATUS_RESPONSE",
                "sender": actor,
                "receiver": "heartbeat",
                "payload": {
                    "health_check_id": health_check_id,
                    "actor": actor,
                    "status": "healthy",
                    "metrics": {
                        "uptime": 3600,
                        "messages_processed": 1000,
                        "error_rate": 0.001,
                        "queue_depth": 5,
                    },
                },
            }
            await harness.send_message(health_response)
            await asyncio.sleep(0.05)

        # Step 3: Heartbeat aggregates results
        health_summary = {
            "type": "HEALTH_CHECK_SUMMARY",
            "sender": "heartbeat",
            "receiver": "mqtt",
            "payload": {
                "health_check_id": health_check_id,
                "overall_status": "healthy",
                "actors_checked": 3,
                "healthy_actors": 3,
                "system_metrics": {
                    "total_uptime": 3600,
                    "total_messages": 3000,
                    "average_error_rate": 0.001,
                },
            },
        }

        await harness.send_message(health_summary)
        await asyncio.sleep(0.1)

        # Step 4: Upload health report
        health_upload = {
            "type": "HEALTH_REPORT_UPLOAD",
            "sender": "mqtt",
            "receiver": "uploader",
            "payload": {
                "health_check_id": health_check_id,
                "report": health_summary["payload"],
                "timestamp": time.time(),
            },
        }

        await harness.send_message(health_upload)
        await asyncio.sleep(0.1)

        # Verify health check flow
        all_messages = harness.messages

        # Check broadcast was received
        broadcast_msgs = [
            m for m in all_messages if m.get("type") == "SYSTEM_HEALTH_CHECK"
        ]
        assert len(broadcast_msgs) > 0

        # Check responses from all actors
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        health_responses = [
            m for m in heartbeat_messages if m["type"] == "HEALTH_STATUS_RESPONSE"
        ]
        assert len(health_responses) == 3

        # Check summary
        mqtt_messages = harness.get_actor_messages("mqtt")
        summary_msg = next(
            (m for m in mqtt_messages if m["type"] == "HEALTH_CHECK_SUMMARY"), None
        )
        assert summary_msg is not None
        assert summary_msg["payload"]["overall_status"] == "healthy"

        # Check upload
        uploader_messages = harness.get_actor_messages("uploader")
        upload_msg = next(
            (m for m in uploader_messages if m["type"] == "HEALTH_REPORT_UPLOAD"), None
        )
        assert upload_msg is not None

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_actor_failure_recovery_flow(self):
        """Test: Actor failure detection and recovery flow"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Step 1: Simulate actor failure detection
        failure_detection = {
            "type": "ACTOR_FAILURE_DETECTED",
            "sender": "heartbeat",
            "receiver": "mqtt",
            "payload": {
                "failed_actor": "uploader",
                "last_response": time.time() - 60,
                "failure_type": "timeout",
                "missed_heartbeats": 3,
            },
        }

        await harness.send_message(failure_detection)
        await asyncio.sleep(0.1)

        # Step 2: MQTT initiates recovery
        recovery_request = {
            "type": "INITIATE_RECOVERY",
            "sender": "mqtt",
            "receiver": "heartbeat",
            "payload": {
                "target_actor": "uploader",
                "recovery_strategy": "restart",
                "preserve_state": True,
            },
        }

        await harness.send_message(recovery_request)
        await asyncio.sleep(0.1)

        # Step 3: Restart actor
        await harness.restart_actor("uploader")

        # Step 4: Verify actor recovery
        recovery_complete = {
            "type": "RECOVERY_COMPLETE",
            "sender": "heartbeat",
            "receiver": "mqtt",
            "payload": {
                "recovered_actor": "uploader",
                "recovery_time": 5.2,
                "state_restored": True,
                "status": "healthy",
            },
        }

        await harness.send_message(recovery_complete)
        await asyncio.sleep(0.1)

        # Step 5: Resume normal operations
        resume_operations = {
            "type": "RESUME_OPERATIONS",
            "sender": "mqtt",
            "receiver": "BROADCAST",
            "payload": {
                "recovered_actor": "uploader",
                "operations_resumed": True,
                "pending_messages_processed": 12,
            },
        }

        await harness.send_message(resume_operations)
        await asyncio.sleep(0.1)

        # Verify recovery flow
        mqtt_messages = harness.get_actor_messages("mqtt")
        failure_msg = next(
            (m for m in mqtt_messages if m["type"] == "ACTOR_FAILURE_DETECTED"), None
        )
        assert failure_msg is not None
        assert failure_msg["payload"]["failed_actor"] == "uploader"

        recovery_msg = next(
            (m for m in mqtt_messages if m["type"] == "RECOVERY_COMPLETE"), None
        )
        assert recovery_msg is not None
        assert recovery_msg["payload"]["status"] == "healthy"

        # Check broadcast resume
        all_messages = harness.messages
        resume_msgs = [m for m in all_messages if m.get("type") == "RESUME_OPERATIONS"]
        assert len(resume_msgs) > 0
        assert resume_msgs[0]["payload"]["operations_resumed"] is True

        await harness.cleanup()
