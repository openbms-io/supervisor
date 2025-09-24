"""
Test BacnetMonitoring ↔ Uploader communication patterns.

User Story: As a data analyst, I want BACnet data to be reliably uploaded to
cloud services for analysis and storage.
"""

import pytest
import asyncio
import time
import sys

# Add the fixtures directory to the path
sys.path.insert(
    0, "/Users/amol/Documents/ai-projects/bms-project/apps/bms-iot-app/tests"
)

from fixtures.actor_test_harness import ActorTestHarness


class TestBACnetToUploaderDataFlow:
    """Test BACnet monitoring to Uploader data flow"""

    @pytest.mark.asyncio
    async def test_point_data_upload_request(self):
        """Test: BACnet sends point data to Uploader for cloud storage"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # BACnet collects and sends data for upload
        upload_request = {
            "type": "DATA_UPLOAD_REQUEST",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "data_type": "telemetry",
                "points": [
                    {
                        "name": "temperature",
                        "value": 23.5,
                        "timestamp": time.time(),
                        "unit": "celsius",
                    },
                    {
                        "name": "humidity",
                        "value": 45.2,
                        "timestamp": time.time(),
                        "unit": "percent",
                    },
                    {
                        "name": "co2_level",
                        "value": 420,
                        "timestamp": time.time(),
                        "unit": "ppm",
                    },
                ],
                "metadata": {
                    "collection_method": "periodic",
                    "interval_seconds": 60,
                    "quality": "good",
                },
            },
        }

        result = await harness.send_message(upload_request)
        assert result["status"] == "sent"

        await asyncio.sleep(0.1)

        # Verify Uploader received the data
        uploader_messages = harness.get_actor_messages("uploader")
        assert len(uploader_messages) > 0

        upload_msg = uploader_messages[0]
        assert upload_msg["type"] == "DATA_UPLOAD_REQUEST"
        assert upload_msg["payload"]["device_id"] == "BAC_DEVICE_001"
        assert len(upload_msg["payload"]["points"]) == 3

        # Verify data integrity
        temp_point = next(
            p for p in upload_msg["payload"]["points"] if p["name"] == "temperature"
        )
        assert temp_point["value"] == 23.5
        assert temp_point["unit"] == "celsius"

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_bulk_data_upload(self):
        """Test: BACnet sends bulk historical data to Uploader"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Create bulk historical data
        current_time = time.time()
        bulk_upload = {
            "type": "BULK_DATA_UPLOAD",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "data_type": "historical",
                "time_range": {"start": current_time - 3600, "end": current_time},
                "data_points": [],
            },
        }

        # Generate 60 minutes of data (1 reading per minute)
        for i in range(60):
            timestamp = current_time - 3600 + (i * 60)
            data_point = {
                "timestamp": timestamp,
                "values": {
                    "temperature": 22.0 + (i * 0.05),
                    "humidity": 45.0 + (i * 0.1),
                    "pressure": 101.3 + (i * 0.01),
                },
            }
            bulk_upload["payload"]["data_points"].append(data_point)

        bulk_upload["payload"]["total_points"] = len(
            bulk_upload["payload"]["data_points"]
        )
        bulk_upload["payload"]["compression"] = "none"

        result = await harness.send_message(bulk_upload)
        assert result["status"] == "sent"

        await asyncio.sleep(0.1)

        # Verify Uploader received bulk data
        uploader_messages = harness.get_actor_messages("uploader")
        bulk_msg = next(
            (m for m in uploader_messages if m["type"] == "BULK_DATA_UPLOAD"), None
        )

        assert bulk_msg is not None
        assert bulk_msg["payload"]["total_points"] == 60
        assert len(bulk_msg["payload"]["data_points"]) == 60

        # Verify data integrity
        first_point = bulk_msg["payload"]["data_points"][0]
        assert "temperature" in first_point["values"]
        assert "humidity" in first_point["values"]

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_aggregated_data_upload(self):
        """Test: BACnet sends aggregated/computed data to Uploader"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Send aggregated statistics
        aggregated_data = {
            "type": "AGGREGATED_DATA_UPLOAD",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "aggregation_period": "15_minutes",
                "timestamp": time.time(),
                "statistics": {
                    "temperature": {
                        "min": 21.5,
                        "max": 24.8,
                        "avg": 23.1,
                        "stddev": 0.8,
                        "sample_count": 900,
                    },
                    "humidity": {
                        "min": 42.0,
                        "max": 48.5,
                        "avg": 45.2,
                        "stddev": 1.5,
                        "sample_count": 900,
                    },
                    "energy_consumption": {
                        "total_kwh": 125.4,
                        "peak_kw": 45.2,
                        "average_kw": 28.3,
                    },
                },
                "quality_metrics": {
                    "data_completeness": 0.98,
                    "sensor_availability": 0.99,
                },
            },
        }

        result = await harness.send_message(aggregated_data)
        assert result["status"] == "sent"

        await asyncio.sleep(0.1)

        # Verify aggregated data was received
        uploader_messages = harness.get_actor_messages("uploader")
        agg_msg = next(
            (m for m in uploader_messages if m["type"] == "AGGREGATED_DATA_UPLOAD"),
            None,
        )

        assert agg_msg is not None
        assert agg_msg["payload"]["aggregation_period"] == "15_minutes"
        assert "temperature" in agg_msg["payload"]["statistics"]
        assert agg_msg["payload"]["statistics"]["temperature"]["avg"] == 23.1
        assert agg_msg["payload"]["quality_metrics"]["data_completeness"] == 0.98

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_alarm_event_upload(self):
        """Test: BACnet sends alarm/event data to Uploader"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Send alarm event for upload
        alarm_event = {
            "type": "ALARM_EVENT_UPLOAD",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "event_type": "alarm",
                "alarm_details": {
                    "alarm_id": "ALM_2024_001",
                    "alarm_type": "TEMPERATURE_HIGH",
                    "severity": "critical",
                    "triggered_at": time.time(),
                    "point_name": "zone_1_temperature",
                    "trigger_value": 35.2,
                    "threshold": 30.0,
                    "state": "active",
                },
                "context": {
                    "location": "Building_A_Floor_2_Zone_1",
                    "equipment": "HVAC_Unit_01",
                    "operator_notified": True,
                },
                "requires_immediate_upload": True,
            },
        }

        result = await harness.send_message(alarm_event)
        assert result["status"] == "sent"

        await asyncio.sleep(0.1)

        # Verify alarm was uploaded
        uploader_messages = harness.get_actor_messages("uploader")
        alarm_msg = next(
            (m for m in uploader_messages if m["type"] == "ALARM_EVENT_UPLOAD"), None
        )

        assert alarm_msg is not None
        assert alarm_msg["payload"]["alarm_details"]["severity"] == "critical"
        assert alarm_msg["payload"]["alarm_details"]["trigger_value"] == 35.2
        assert alarm_msg["payload"]["requires_immediate_upload"] is True

        await harness.cleanup()


class TestUploaderToBACnetResponses:
    """Test Uploader responses back to BACnet monitoring"""

    @pytest.mark.asyncio
    async def test_upload_success_confirmation(self):
        """Test: Uploader confirms successful data upload to BACnet"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Step 1: BACnet sends data
        upload_request = {
            "id": "upload_001",
            "type": "DATA_UPLOAD_REQUEST",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "points": [{"name": "temp", "value": 23.5}],
            },
        }

        await harness.send_message(upload_request)
        await asyncio.sleep(0.1)

        # Step 2: Uploader confirms success
        upload_confirmation = {
            "type": "UPLOAD_CONFIRMATION",
            "sender": "uploader",
            "receiver": "bacnet_monitoring",
            "payload": {
                "original_request_id": "upload_001",
                "status": "success",
                "uploaded_at": time.time(),
                "storage_location": "cloud_bucket/2024/device_001/data.json",
                "records_uploaded": 1,
                "bytes_uploaded": 256,
                "upload_duration_ms": 125,
            },
        }

        await harness.send_message(upload_confirmation)
        await asyncio.sleep(0.1)

        # Verify confirmation flow
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        confirm_msg = next(
            (m for m in bacnet_messages if m["type"] == "UPLOAD_CONFIRMATION"), None
        )

        assert confirm_msg is not None
        assert confirm_msg["payload"]["status"] == "success"
        assert confirm_msg["payload"]["original_request_id"] == "upload_001"
        assert "storage_location" in confirm_msg["payload"]

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_upload_failure_notification(self):
        """Test: Uploader notifies BACnet of upload failures"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Uploader reports failure
        upload_failure = {
            "type": "UPLOAD_FAILURE",
            "sender": "uploader",
            "receiver": "bacnet_monitoring",
            "payload": {
                "original_request_id": "upload_002",
                "device_id": "BAC_DEVICE_001",
                "failure_reason": "network_timeout",
                "error_details": {
                    "error_code": "TIMEOUT_ERROR",
                    "error_message": "Connection to cloud service timed out after 30s",
                    "retry_count": 3,
                    "last_attempt": time.time(),
                },
                "data_buffered": True,
                "buffer_location": "/tmp/upload_buffer/upload_002.json",
                "retry_recommended": True,
                "retry_after_seconds": 300,
            },
        }

        await harness.send_message(upload_failure)
        await asyncio.sleep(0.1)

        # Verify failure notification
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        failure_msg = next(
            (m for m in bacnet_messages if m["type"] == "UPLOAD_FAILURE"), None
        )

        assert failure_msg is not None
        assert failure_msg["payload"]["failure_reason"] == "network_timeout"
        assert failure_msg["payload"]["data_buffered"] is True
        assert failure_msg["payload"]["retry_recommended"] is True

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_upload_quota_exceeded(self):
        """Test: Uploader notifies BACnet when upload quota is exceeded"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Uploader reports quota exceeded
        quota_exceeded = {
            "type": "UPLOAD_QUOTA_EXCEEDED",
            "sender": "uploader",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "quota_type": "daily_data_limit",
                "current_usage": {
                    "bytes_uploaded": 10737418240,  # 10 GB
                    "records_uploaded": 1000000,
                    "api_calls": 50000,
                },
                "quota_limits": {
                    "max_bytes": 10737418240,  # 10 GB
                    "max_records": 1000000,
                    "max_api_calls": 50000,
                },
                "reset_time": time.time() + 3600,  # Resets in 1 hour
                "action_taken": "data_buffered",
                "buffer_size": 1024000,  # 1 MB buffered
            },
        }

        await harness.send_message(quota_exceeded)
        await asyncio.sleep(0.1)

        # Verify quota notification
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        quota_msg = next(
            (m for m in bacnet_messages if m["type"] == "UPLOAD_QUOTA_EXCEEDED"), None
        )

        assert quota_msg is not None
        assert quota_msg["payload"]["quota_type"] == "daily_data_limit"
        assert quota_msg["payload"]["action_taken"] == "data_buffered"

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_upload_statistics_report(self):
        """Test: Uploader sends periodic statistics to BACnet"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Uploader sends statistics report
        stats_report = {
            "type": "UPLOAD_STATISTICS",
            "sender": "uploader",
            "receiver": "bacnet_monitoring",
            "payload": {
                "reporting_period": "1_hour",
                "timestamp": time.time(),
                "device_statistics": {
                    "BAC_DEVICE_001": {
                        "total_uploads": 3600,
                        "successful_uploads": 3590,
                        "failed_uploads": 10,
                        "bytes_uploaded": 52428800,  # 50 MB
                        "average_upload_time_ms": 150,
                        "max_upload_time_ms": 2500,
                        "error_rate": 0.0028,
                    }
                },
                "overall_statistics": {
                    "total_devices": 5,
                    "active_devices": 5,
                    "total_bytes_uploaded": 262144000,  # 250 MB
                    "cloud_storage_used": 5368709120,  # 5 GB
                    "api_health": "healthy",
                    "average_latency_ms": 125,
                },
            },
        }

        await harness.send_message(stats_report)
        await asyncio.sleep(0.1)

        # Verify statistics received
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        stats_msg = next(
            (m for m in bacnet_messages if m["type"] == "UPLOAD_STATISTICS"), None
        )

        assert stats_msg is not None
        assert "BAC_DEVICE_001" in stats_msg["payload"]["device_statistics"]
        assert (
            stats_msg["payload"]["device_statistics"]["BAC_DEVICE_001"]["total_uploads"]
            == 3600
        )
        assert stats_msg["payload"]["overall_statistics"]["api_health"] == "healthy"

        await harness.cleanup()


class TestDataBufferingAndRetry:
    """Test data buffering and retry mechanisms"""

    @pytest.mark.asyncio
    async def test_data_buffering_during_outage(self):
        """Test: Data buffering when uploader is unavailable"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # BACnet notifies about buffering
        buffer_notification = {
            "type": "DATA_BUFFERING_STARTED",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "reason": "uploader_unavailable",
                "buffer_strategy": "memory_then_disk",
                "buffer_location": "/tmp/bacnet_buffer/",
                "max_buffer_size": 104857600,  # 100 MB
                "current_buffer_size": 0,
                "timestamp": time.time(),
            },
        }

        await harness.send_message(buffer_notification)

        # Buffer some data
        buffered_data = []
        for i in range(5):
            data = {
                "type": "BUFFERED_DATA",
                "sender": "bacnet_monitoring",
                "receiver": "uploader",
                "payload": {
                    "device_id": "BAC_DEVICE_001",
                    "sequence_number": i,
                    "buffered_at": time.time() + i,
                    "data": {"temp": 23.0 + i * 0.1},
                },
            }
            buffered_data.append(data)
            await harness.send_message(data)

        await asyncio.sleep(0.1)

        # Uploader becomes available and requests buffered data
        buffer_request = {
            "type": "REQUEST_BUFFERED_DATA",
            "sender": "uploader",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "max_records": 100,
                "from_sequence": 0,
            },
        }

        await harness.send_message(buffer_request)
        await asyncio.sleep(0.1)

        # Verify buffering flow
        uploader_messages = harness.get_actor_messages("uploader")
        buffer_start = next(
            (m for m in uploader_messages if m["type"] == "DATA_BUFFERING_STARTED"),
            None,
        )
        assert buffer_start is not None

        buffered_msgs = [m for m in uploader_messages if m["type"] == "BUFFERED_DATA"]
        assert len(buffered_msgs) == 5

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self):
        """Test: Retry uploads with exponential backoff"""
        harness = ActorTestHarness()
        await harness.initialize()

        # Configure retry with exponential backoff
        retry_config = {
            "max_retries": 5,
            "initial_delay": 1,
            "backoff_multiplier": 2,
            "max_delay": 60,
        }

        # Initial upload attempt
        upload_request = {
            "id": "retry_test",
            "type": "DATA_UPLOAD_REQUEST",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "retry_config": retry_config,
            "payload": {"device_id": "BAC_DEVICE_001", "data": {"temp": 23.5}},
        }

        # Simulate retries with backoff
        expected_delays = [1, 2, 4, 8, 16]  # Exponential backoff

        for attempt, delay in enumerate(expected_delays):
            # Send retry attempt
            retry_msg = upload_request.copy()
            retry_msg["retry_attempt"] = attempt + 1
            retry_msg["retry_delay"] = delay

            await harness.send_message(retry_msg)
            await asyncio.sleep(0.05)  # Small delay for processing

        # Verify retry attempts
        uploader_messages = harness.get_actor_messages("uploader")
        retry_messages = [m for m in uploader_messages if m.get("id") == "retry_test"]

        assert len(retry_messages) >= 5

        # Check exponential delays
        for i, msg in enumerate(retry_messages[:5]):
            if "retry_delay" in msg:
                assert msg["retry_delay"] == expected_delays[i]

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_batch_upload_optimization(self):
        """Test: Batch multiple small uploads for efficiency"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # BACnet sends request to batch uploads
        batch_request = {
            "type": "BATCH_UPLOAD_REQUEST",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "batch_id": "batch_001",
                "device_id": "BAC_DEVICE_001",
                "batch_strategy": "time_window",
                "batch_window_seconds": 60,
                "data_items": [],
            },
        }

        # Add 20 small data items to batch
        current_time = time.time()
        for i in range(20):
            item = {
                "item_id": f"item_{i}",
                "timestamp": current_time + i,
                "data": {"temp": 23.0 + i * 0.1, "humidity": 45.0 + i * 0.2},
            }
            batch_request["payload"]["data_items"].append(item)

        batch_request["payload"]["total_items"] = 20
        batch_request["payload"]["batch_size_bytes"] = 2048

        result = await harness.send_message(batch_request)
        assert result["status"] == "sent"

        await asyncio.sleep(0.1)

        # Uploader confirms batch upload
        batch_confirmation = {
            "type": "BATCH_UPLOAD_CONFIRMATION",
            "sender": "uploader",
            "receiver": "bacnet_monitoring",
            "payload": {
                "batch_id": "batch_001",
                "status": "success",
                "items_uploaded": 20,
                "compression_ratio": 0.65,
                "upload_time_ms": 250,
                "storage_saved_percent": 35,
            },
        }

        await harness.send_message(batch_confirmation)
        await asyncio.sleep(0.1)

        # Verify batch optimization
        uploader_messages = harness.get_actor_messages("uploader")
        batch_msg = next(
            (m for m in uploader_messages if m["type"] == "BATCH_UPLOAD_REQUEST"), None
        )

        assert batch_msg is not None
        assert batch_msg["payload"]["total_items"] == 20
        assert batch_msg["payload"]["batch_strategy"] == "time_window"

        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        confirm_msg = next(
            (m for m in bacnet_messages if m["type"] == "BATCH_UPLOAD_CONFIRMATION"),
            None,
        )

        assert confirm_msg is not None
        assert confirm_msg["payload"]["items_uploaded"] == 20
        assert confirm_msg["payload"]["storage_saved_percent"] == 35

        await harness.cleanup()


class TestDataTransformationAndCompression:
    """Test data transformation and compression between actors"""

    @pytest.mark.asyncio
    async def test_data_compression_before_upload(self):
        """Test: BACnet compresses data before sending to Uploader"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Large dataset for compression
        large_dataset = {
            "type": "COMPRESSED_DATA_UPLOAD",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "compression": {
                    "algorithm": "gzip",
                    "original_size": 1048576,  # 1 MB
                    "compressed_size": 256000,  # 250 KB
                    "compression_ratio": 0.244,
                },
                "data_format": "json_compressed",
                "data": "base64_encoded_compressed_data_here",  # Simulated compressed data
                "checksum": "sha256:abcdef123456",
                "timestamp": time.time(),
            },
        }

        result = await harness.send_message(large_dataset)
        assert result["status"] == "sent"

        await asyncio.sleep(0.1)

        # Verify compressed data received
        uploader_messages = harness.get_actor_messages("uploader")
        compressed_msg = next(
            (m for m in uploader_messages if m["type"] == "COMPRESSED_DATA_UPLOAD"),
            None,
        )

        assert compressed_msg is not None
        assert compressed_msg["payload"]["compression"]["algorithm"] == "gzip"
        assert compressed_msg["payload"]["compression"]["compression_ratio"] == 0.244

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_data_format_transformation(self):
        """Test: Data format transformation between BACnet and Uploader"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # BACnet sends data in one format
        bacnet_format_data = {
            "type": "DATA_TRANSFORM_REQUEST",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "source_format": "bacnet_raw",
                "target_format": "cloud_json",
                "data": {
                    "analogInput:1": {
                        "presentValue": 23.5,
                        "statusFlags": [0, 0, 0, 0],
                    },
                    "analogInput:2": {
                        "presentValue": 45.2,
                        "statusFlags": [0, 0, 0, 0],
                    },
                    "binaryInput:1": {
                        "presentValue": "active",
                        "statusFlags": [0, 0, 0, 0],
                    },
                },
                "transformation_rules": {
                    "flatten_structure": True,
                    "convert_units": True,
                    "add_metadata": True,
                },
            },
        }

        await harness.send_message(bacnet_format_data)
        await asyncio.sleep(0.1)

        # Uploader confirms transformation
        transform_result = {
            "type": "DATA_TRANSFORM_COMPLETE",
            "sender": "uploader",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "transformation_status": "success",
                "transformed_data": {
                    "temperature": 23.5,
                    "humidity": 45.2,
                    "occupancy": True,
                    "metadata": {
                        "source": "bacnet",
                        "transformed_at": time.time(),
                        "quality": "good",
                    },
                },
                "records_transformed": 3,
            },
        }

        await harness.send_message(transform_result)
        await asyncio.sleep(0.1)

        # Verify transformation flow
        uploader_messages = harness.get_actor_messages("uploader")
        transform_req = next(
            (m for m in uploader_messages if m["type"] == "DATA_TRANSFORM_REQUEST"),
            None,
        )

        assert transform_req is not None
        assert transform_req["payload"]["source_format"] == "bacnet_raw"
        assert transform_req["payload"]["target_format"] == "cloud_json"

        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        transform_complete = next(
            (m for m in bacnet_messages if m["type"] == "DATA_TRANSFORM_COMPLETE"), None
        )

        assert transform_complete is not None
        assert transform_complete["payload"]["transformation_status"] == "success"
        assert transform_complete["payload"]["records_transformed"] == 3

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_data_validation_before_upload(self):
        """Test: Data validation between BACnet and Uploader"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # BACnet sends data for validation
        data_for_validation = {
            "type": "VALIDATE_DATA_REQUEST",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "validation_schema": "telemetry_v2",
                "data": [
                    {
                        "point": "temperature",
                        "value": 23.5,
                        "timestamp": time.time(),
                        "quality": "good",
                    },
                    {
                        "point": "humidity",
                        "value": 145.0,  # Invalid - out of range
                        "timestamp": time.time(),
                        "quality": "good",
                    },
                    {
                        "point": "pressure",
                        "value": None,  # Invalid - null value
                        "timestamp": time.time(),
                        "quality": "bad",
                    },
                ],
            },
        }

        await harness.send_message(data_for_validation)
        await asyncio.sleep(0.1)

        # Uploader responds with validation results
        validation_result = {
            "type": "VALIDATION_RESULT",
            "sender": "uploader",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "validation_status": "partial_failure",
                "total_records": 3,
                "valid_records": 1,
                "invalid_records": 2,
                "validation_errors": [
                    {
                        "record_index": 1,
                        "field": "humidity.value",
                        "error": "value_out_of_range",
                        "message": "Humidity value 145.0 exceeds maximum 100.0",
                    },
                    {
                        "record_index": 2,
                        "field": "pressure.value",
                        "error": "null_value_not_allowed",
                        "message": "Pressure value cannot be null when quality is bad",
                    },
                ],
                "action": "upload_valid_only",
            },
        }

        await harness.send_message(validation_result)
        await asyncio.sleep(0.1)

        # Verify validation flow
        uploader_messages = harness.get_actor_messages("uploader")
        validation_req = next(
            (m for m in uploader_messages if m["type"] == "VALIDATE_DATA_REQUEST"), None
        )

        assert validation_req is not None
        assert len(validation_req["payload"]["data"]) == 3

        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        validation_res = next(
            (m for m in bacnet_messages if m["type"] == "VALIDATION_RESULT"), None
        )

        assert validation_res is not None
        assert validation_res["payload"]["validation_status"] == "partial_failure"
        assert validation_res["payload"]["invalid_records"] == 2
        assert len(validation_res["payload"]["validation_errors"]) == 2

        await harness.cleanup()


class TestCloudServiceIntegration:
    """Test cloud service integration patterns"""

    @pytest.mark.asyncio
    async def test_multi_cloud_upload_routing(self):
        """Test: Route uploads to different cloud services"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # BACnet requests multi-cloud upload
        multi_cloud_request = {
            "type": "MULTI_CLOUD_UPLOAD",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "routing_strategy": "data_type_based",
                "destinations": [
                    {
                        "cloud_provider": "aws_s3",
                        "data_types": ["telemetry", "metrics"],
                        "bucket": "iot-telemetry-prod",
                    },
                    {
                        "cloud_provider": "azure_blob",
                        "data_types": ["alarms", "events"],
                        "container": "iot-events",
                    },
                    {
                        "cloud_provider": "timescale_db",
                        "data_types": ["time_series"],
                        "database": "iot_metrics",
                    },
                ],
                "data_packets": [
                    {"type": "telemetry", "data": {"temp": 23.5}},
                    {"type": "alarms", "data": {"alarm": "high_temp"}},
                    {"type": "time_series", "data": {"values": [1, 2, 3]}},
                ],
            },
        }

        await harness.send_message(multi_cloud_request)
        await asyncio.sleep(0.1)

        # Uploader confirms multi-cloud upload
        multi_cloud_result = {
            "type": "MULTI_CLOUD_UPLOAD_RESULT",
            "sender": "uploader",
            "receiver": "bacnet_monitoring",
            "payload": {
                "device_id": "BAC_DEVICE_001",
                "upload_results": [
                    {
                        "cloud_provider": "aws_s3",
                        "status": "success",
                        "records_uploaded": 1,
                        "location": "s3://iot-telemetry-prod/2024/device_001/",
                    },
                    {
                        "cloud_provider": "azure_blob",
                        "status": "success",
                        "records_uploaded": 1,
                        "location": "https://storage.blob.core.windows.net/iot-events/",
                    },
                    {
                        "cloud_provider": "timescale_db",
                        "status": "success",
                        "records_uploaded": 1,
                        "rows_inserted": 3,
                    },
                ],
                "total_success": 3,
                "total_failure": 0,
            },
        }

        await harness.send_message(multi_cloud_result)
        await asyncio.sleep(0.1)

        # Verify multi-cloud routing
        uploader_messages = harness.get_actor_messages("uploader")
        multi_req = next(
            (m for m in uploader_messages if m["type"] == "MULTI_CLOUD_UPLOAD"), None
        )

        assert multi_req is not None
        assert len(multi_req["payload"]["destinations"]) == 3
        assert multi_req["payload"]["routing_strategy"] == "data_type_based"

        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        multi_res = next(
            (m for m in bacnet_messages if m["type"] == "MULTI_CLOUD_UPLOAD_RESULT"),
            None,
        )

        assert multi_res is not None
        assert multi_res["payload"]["total_success"] == 3
        assert all(
            r["status"] == "success" for r in multi_res["payload"]["upload_results"]
        )

        await harness.cleanup()
