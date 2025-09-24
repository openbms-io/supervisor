"""
Test uploader actor error handling and recovery patterns.

User Story: As a data engineer, I want upload failures to preserve data integrity
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


class TestUploaderConnectionFailureHandling:
    """Test uploader connection failure scenarios and data preservation"""

    @pytest.mark.asyncio
    async def test_rest_api_failure_data_persistence_retry_queue(self):
        """Test: REST API failure → data persistence → retry queue management"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate REST API failure during upload
        api_failure = {
            "type": "UPLOADER_API_FAILURE",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "endpoint": "https://api.bms.com/v1/metrics/bulk",
                "http_method": "POST",
                "error_type": "ConnectionError",
                "error_message": "Connection timeout after 30s",
                "payload_size": 2048000,  # 2MB
                "batch_id": "batch_001",
                "device_count": 25,
                "failure_timestamp": time.time(),
            },
        }

        await harness.send_message(api_failure)
        await asyncio.sleep(0.1)

        # Simulate data persistence to local storage
        data_persistence = {
            "type": "UPLOADER_DATA_PERSISTED",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "batch_id": "batch_001",
                "storage_location": "/tmp/bms_cache/pending_uploads/batch_001.json",
                "data_size": 2048000,
                "compression_applied": True,
                "compressed_size": 512000,  # 25% of original
                "persistence_timestamp": time.time(),
                "expiry_timestamp": time.time() + 86400,  # 24 hours
            },
        }

        await harness.send_message(data_persistence)
        await asyncio.sleep(0.1)

        # Simulate retry queue management
        retry_queue_update = {
            "type": "UPLOADER_RETRY_QUEUE_UPDATE",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "batch_id": "batch_001",
                "queue_position": 1,
                "total_queue_size": 5,
                "priority_level": "high",
                "next_retry_timestamp": time.time() + 300,  # Retry in 5 minutes
                "retry_count": 0,
                "max_retries": 5,
                "backoff_strategy": "exponential",
            },
        }

        await harness.send_message(retry_queue_update)
        await asyncio.sleep(0.1)

        # Simulate queue processing status
        queue_status = {
            "type": "UPLOADER_QUEUE_STATUS",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "total_batches_queued": 5,
                "total_data_size": 10240000,  # 10MB
                "oldest_batch_age": 1800,  # 30 minutes
                "queue_utilization": 50.0,  # 50%
                "estimated_processing_time": 900,  # 15 minutes
            },
        }

        await harness.send_message(queue_status)
        await asyncio.sleep(0.1)

        # Verify API failure notification
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        failure_msg = next(
            (m for m in heartbeat_messages if m["type"] == "UPLOADER_API_FAILURE"), None
        )
        assert failure_msg is not None
        assert failure_msg["payload"]["batch_id"] == "batch_001"
        assert failure_msg["payload"]["device_count"] == 25

        # Verify data persistence
        persistence_msg = next(
            (m for m in heartbeat_messages if m["type"] == "UPLOADER_DATA_PERSISTED"),
            None,
        )
        assert persistence_msg is not None
        assert persistence_msg["payload"]["compression_applied"] is True
        assert persistence_msg["payload"]["compressed_size"] == 512000

        # Verify retry queue management
        queue_update_msg = next(
            (
                m
                for m in heartbeat_messages
                if m["type"] == "UPLOADER_RETRY_QUEUE_UPDATE"
            ),
            None,
        )
        assert queue_update_msg is not None
        assert queue_update_msg["payload"]["priority_level"] == "high"
        assert queue_update_msg["payload"]["backoff_strategy"] == "exponential"

        # Verify queue status
        status_msg = next(
            (m for m in heartbeat_messages if m["type"] == "UPLOADER_QUEUE_STATUS"),
            None,
        )
        assert status_msg is not None
        assert status_msg["payload"]["total_batches_queued"] == 5
        assert status_msg["payload"]["queue_utilization"] == 50.0

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_network_timeout_during_upload_data_preservation(self):
        """Test: Network timeout during upload → timeout handling → data preservation"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate network timeout during large upload
        network_timeout = {
            "type": "UPLOADER_NETWORK_TIMEOUT",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "batch_id": "batch_002",
                "upload_progress": 65.5,  # 65.5% uploaded when timeout occurred
                "bytes_uploaded": 1342177,  # ~1.3MB
                "total_bytes": 2048000,  # 2MB total
                "timeout_duration": 60.0,  # 60 second timeout
                "connection_state": "interrupted",
                "retry_recommended": True,
            },
        }

        await harness.send_message(network_timeout)
        await asyncio.sleep(0.1)

        # Simulate timeout handling strategy
        timeout_handling = {
            "type": "UPLOADER_TIMEOUT_HANDLING",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "batch_id": "batch_002",
                "handling_strategy": "resume_upload",
                "resume_from_byte": 1342177,
                "remaining_bytes": 705823,
                "chunked_upload_enabled": True,
                "chunk_size": 256000,  # 256KB chunks
                "estimated_chunks": 3,
            },
        }

        await harness.send_message(timeout_handling)
        await asyncio.sleep(0.1)

        # Simulate data preservation during retry
        data_preservation = {
            "type": "UPLOADER_DATA_PRESERVATION",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "batch_id": "batch_002",
                "preservation_method": "incremental_backup",
                "backup_location": "/tmp/bms_cache/partial_uploads/batch_002_resume.json",
                "resume_token": "resume_token_xyz789",
                "partial_upload_metadata": {
                    "bytes_uploaded": 1342177,
                    "upload_session_id": "session_abc123",
                    "server_etag": "etag_456def",
                },
            },
        }

        await harness.send_message(data_preservation)
        await asyncio.sleep(0.1)

        # Simulate successful resumption
        upload_resumed = {
            "type": "UPLOADER_UPLOAD_RESUMED",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "batch_id": "batch_002",
                "resumption_successful": True,
                "resumed_from_byte": 1342177,
                "chunks_uploaded": 3,
                "total_upload_time": 45.2,
                "final_status": "completed",
                "data_integrity_verified": True,
            },
        }

        await harness.send_message(upload_resumed)
        await asyncio.sleep(0.1)

        # Verify timeout detection
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        timeout_msg = next(
            (m for m in heartbeat_messages if m["type"] == "UPLOADER_NETWORK_TIMEOUT"),
            None,
        )
        assert timeout_msg is not None
        assert timeout_msg["payload"]["upload_progress"] == 65.5
        assert timeout_msg["payload"]["retry_recommended"] is True

        # Verify timeout handling strategy
        handling_msg = next(
            (m for m in heartbeat_messages if m["type"] == "UPLOADER_TIMEOUT_HANDLING"),
            None,
        )
        assert handling_msg is not None
        assert handling_msg["payload"]["handling_strategy"] == "resume_upload"
        assert handling_msg["payload"]["chunked_upload_enabled"] is True

        # Verify data preservation
        preservation_msg = next(
            (
                m
                for m in heartbeat_messages
                if m["type"] == "UPLOADER_DATA_PRESERVATION"
            ),
            None,
        )
        assert preservation_msg is not None
        assert (
            preservation_msg["payload"]["preservation_method"] == "incremental_backup"
        )

        # Verify successful resumption
        resumed_msg = next(
            (m for m in heartbeat_messages if m["type"] == "UPLOADER_UPLOAD_RESUMED"),
            None,
        )
        assert resumed_msg is not None
        assert resumed_msg["payload"]["resumption_successful"] is True
        assert resumed_msg["payload"]["data_integrity_verified"] is True

        await harness.cleanup()


class TestUploaderHTTPErrorHandling:
    """Test HTTP error handling and retry logic"""

    @pytest.mark.asyncio
    async def test_http_5xx_errors_exponential_backoff_retry(self):
        """Test: HTTP 5xx errors → exponential backoff → retry logic"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate HTTP 5xx error
        http_5xx_error = {
            "type": "UPLOADER_HTTP_5XX_ERROR",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "batch_id": "batch_003",
                "http_status_code": 503,
                "error_message": "Service Temporarily Unavailable",
                "response_headers": {"Retry-After": "120", "Server": "nginx/1.18.0"},
                "error_category": "server_overload",
                "retry_eligible": True,
            },
        }

        await harness.send_message(http_5xx_error)
        await asyncio.sleep(0.1)

        # Simulate exponential backoff strategy
        backoff_strategy = {
            "type": "UPLOADER_BACKOFF_STRATEGY",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "batch_id": "batch_003",
                "strategy_type": "exponential_backoff",
                "initial_delay": 30,  # 30 seconds
                "max_delay": 1800,  # 30 minutes
                "backoff_multiplier": 2.0,
                "jitter_enabled": True,
                "jitter_percentage": 10,
                "current_retry_count": 0,
                "max_retries": 5,
            },
        }

        await harness.send_message(backoff_strategy)
        await asyncio.sleep(0.1)

        # Simulate retry attempts with increasing delays
        retry_delays = [30, 60, 120, 240, 480]  # Exponential backoff

        for retry_count, delay in enumerate(retry_delays, 1):
            retry_attempt = {
                "type": "UPLOADER_RETRY_ATTEMPT",
                "sender": "uploader",
                "receiver": "heartbeat",
                "payload": {
                    "batch_id": "batch_003",
                    "retry_count": retry_count,
                    "scheduled_delay": delay,
                    "actual_delay": delay + (delay * 0.1),  # With jitter
                    "retry_timestamp": time.time() + delay,
                    "retry_reason": "http_5xx_temporary_failure",
                },
            }
            await harness.send_message(retry_attempt)
            await asyncio.sleep(0.02)  # Small delay between messages

        # Simulate successful retry on 3rd attempt
        successful_retry = {
            "type": "UPLOADER_RETRY_SUCCESS",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "batch_id": "batch_003",
                "successful_retry_count": 3,
                "total_retry_duration": 210,  # 3.5 minutes total
                "http_status_code": 200,
                "upload_completion_time": 15.8,
                "server_recovery_detected": True,
                "data_integrity_verified": True,
            },
        }

        await harness.send_message(successful_retry)
        await asyncio.sleep(0.1)

        # Verify HTTP 5xx error detection
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        error_msg = next(
            (m for m in heartbeat_messages if m["type"] == "UPLOADER_HTTP_5XX_ERROR"),
            None,
        )
        assert error_msg is not None
        assert error_msg["payload"]["http_status_code"] == 503
        assert error_msg["payload"]["retry_eligible"] is True

        # Verify backoff strategy
        backoff_msg = next(
            (m for m in heartbeat_messages if m["type"] == "UPLOADER_BACKOFF_STRATEGY"),
            None,
        )
        assert backoff_msg is not None
        assert backoff_msg["payload"]["strategy_type"] == "exponential_backoff"
        assert backoff_msg["payload"]["jitter_enabled"] is True

        # Verify retry attempts
        retry_msgs = [
            m for m in heartbeat_messages if m["type"] == "UPLOADER_RETRY_ATTEMPT"
        ]
        assert len(retry_msgs) == 5

        # Verify exponential backoff delays
        for i, msg in enumerate(retry_msgs):
            expected_delay = retry_delays[i]
            assert msg["payload"]["scheduled_delay"] == expected_delay

        # Verify successful retry
        success_msg = next(
            (m for m in heartbeat_messages if m["type"] == "UPLOADER_RETRY_SUCCESS"),
            None,
        )
        assert success_msg is not None
        assert success_msg["payload"]["successful_retry_count"] == 3
        assert success_msg["payload"]["server_recovery_detected"] is True

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_http_4xx_errors_permanent_failure_data_quarantine(self):
        """Test: HTTP 4xx errors → permanent failure handling → data quarantine"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate HTTP 4xx error (permanent failure)
        http_4xx_error = {
            "type": "UPLOADER_HTTP_4XX_ERROR",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "batch_id": "batch_004",
                "http_status_code": 422,
                "error_message": "Unprocessable Entity: Invalid data format",
                "validation_errors": [
                    'Field "timestamp" format invalid',
                    'Field "device_id" exceeds maximum length',
                    'Field "value" contains non-numeric data',
                ],
                "error_category": "data_validation",
                "retry_eligible": False,
            },
        }

        await harness.send_message(http_4xx_error)
        await asyncio.sleep(0.1)

        # Simulate permanent failure handling
        permanent_failure = {
            "type": "UPLOADER_PERMANENT_FAILURE",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "batch_id": "batch_004",
                "failure_type": "data_validation_error",
                "resolution_action": "quarantine_data",
                "data_preservation": True,
                "manual_review_required": True,
                "automatic_retry_disabled": True,
            },
        }

        await harness.send_message(permanent_failure)
        await asyncio.sleep(0.1)

        # Simulate data quarantine process
        data_quarantine = {
            "type": "UPLOADER_DATA_QUARANTINED",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "batch_id": "batch_004",
                "quarantine_location": "/tmp/bms_cache/quarantine/batch_004_invalid.json",
                "quarantine_timestamp": time.time(),
                "quarantine_reason": "http_422_validation_failure",
                "data_preserved": True,
                "validation_errors_logged": True,
                "notification_sent": True,
                "review_required_by": time.time() + 86400,  # 24 hours
            },
        }

        await harness.send_message(data_quarantine)
        await asyncio.sleep(0.1)

        # Simulate notification to administrators
        admin_notification = {
            "type": "UPLOADER_ADMIN_NOTIFICATION",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "notification_type": "data_quarantine_alert",
                "batch_id": "batch_004",
                "severity": "medium",
                "message": "Data batch quarantined due to validation errors",
                "action_required": "Review and fix data format issues",
                "quarantine_location": "/tmp/bms_cache/quarantine/batch_004_invalid.json",
                "contact_info": "admin@bms-system.com",
            },
        }

        await harness.send_message(admin_notification)
        await asyncio.sleep(0.1)

        # Verify HTTP 4xx error detection
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        error_msg = next(
            (m for m in heartbeat_messages if m["type"] == "UPLOADER_HTTP_4XX_ERROR"),
            None,
        )
        assert error_msg is not None
        assert error_msg["payload"]["http_status_code"] == 422
        assert error_msg["payload"]["retry_eligible"] is False
        assert len(error_msg["payload"]["validation_errors"]) == 3

        # Verify permanent failure handling
        failure_msg = next(
            (
                m
                for m in heartbeat_messages
                if m["type"] == "UPLOADER_PERMANENT_FAILURE"
            ),
            None,
        )
        assert failure_msg is not None
        assert failure_msg["payload"]["resolution_action"] == "quarantine_data"
        assert failure_msg["payload"]["manual_review_required"] is True

        # Verify data quarantine
        quarantine_msg = next(
            (m for m in heartbeat_messages if m["type"] == "UPLOADER_DATA_QUARANTINED"),
            None,
        )
        assert quarantine_msg is not None
        assert quarantine_msg["payload"]["data_preserved"] is True
        assert quarantine_msg["payload"]["validation_errors_logged"] is True

        # Verify admin notification
        notification_msg = next(
            (
                m
                for m in heartbeat_messages
                if m["type"] == "UPLOADER_ADMIN_NOTIFICATION"
            ),
            None,
        )
        assert notification_msg is not None
        assert notification_msg["payload"]["severity"] == "medium"
        assert (
            notification_msg["payload"]["action_required"]
            == "Review and fix data format issues"
        )

        await harness.cleanup()


class TestUploaderQueueManagement:
    """Test upload queue overflow and backpressure handling"""

    @pytest.mark.asyncio
    async def test_upload_queue_overflow_backpressure_throttling(self):
        """Test: Upload queue overflow → backpressure → data collection throttling"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate upload queue reaching critical capacity
        queue_overflow = {
            "type": "UPLOADER_QUEUE_OVERFLOW",
            "sender": "uploader",
            "receiver": "BROADCAST",
            "payload": {
                "queue_type": "pending_uploads",
                "current_size": 95,
                "max_capacity": 100,
                "overflow_threshold": 90,
                "queue_utilization": 95.0,
                "oldest_batch_age": 3600,  # 1 hour
                "estimated_processing_backlog": 7200,  # 2 hours
                "backpressure_required": True,
            },
        }

        await harness.send_message(queue_overflow)
        await asyncio.sleep(0.1)

        # Simulate backpressure signal to data collectors
        backpressure_signal = {
            "type": "UPLOADER_BACKPRESSURE_SIGNAL",
            "sender": "uploader",
            "receiver": "bacnet_monitoring",
            "payload": {
                "backpressure_level": "high",
                "throttling_required": True,
                "reduce_collection_rate_by": 70,  # Reduce by 70%
                "skip_non_critical_devices": True,
                "increase_batch_interval": True,
                "new_batch_interval": 300,  # 5 minutes instead of 1 minute
                "priority_devices_only": True,
            },
        }

        await harness.send_message(backpressure_signal)
        await asyncio.sleep(0.1)

        # Simulate data collection throttling response
        throttling_response = {
            "type": "BACNET_THROTTLING_ACTIVATED",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "throttling_level": "high",
                "original_device_count": 50,
                "throttled_device_count": 15,  # Only 15 critical devices
                "collection_rate_reduction": 70,
                "estimated_data_reduction": 85,  # 85% less data
                "throttling_duration": "until_backpressure_released",
            },
        }

        await harness.send_message(throttling_response)
        await asyncio.sleep(0.1)

        # Simulate queue recovery after throttling
        queue_recovery = {
            "type": "UPLOADER_QUEUE_RECOVERY",
            "sender": "uploader",
            "receiver": "BROADCAST",
            "payload": {
                "queue_type": "pending_uploads",
                "current_size": 45,
                "recovery_time": 1800,  # 30 minutes to recover
                "backlog_cleared": 50,
                "backpressure_released": True,
                "normal_operations_resumed": False,  # Still cautious
                "gradual_ramp_up": True,
            },
        }

        await harness.send_message(queue_recovery)
        await asyncio.sleep(0.1)

        # Simulate gradual ramp-up of collection
        gradual_ramp_up = {
            "type": "UPLOADER_GRADUAL_RAMP_UP",
            "sender": "uploader",
            "receiver": "bacnet_monitoring",
            "payload": {
                "ramp_up_phase": 1,
                "target_device_count": 25,  # 50% of original
                "ramp_up_duration": 600,  # 10 minutes
                "monitor_queue_closely": True,
                "abort_ramp_up_threshold": 80,  # If queue hits 80%, abort
                "next_phase_delay": 600,
            },
        }

        await harness.send_message(gradual_ramp_up)
        await asyncio.sleep(0.1)

        # Verify queue overflow detection
        all_messages = harness.messages
        overflow_msgs = [
            m for m in all_messages if m.get("type") == "UPLOADER_QUEUE_OVERFLOW"
        ]
        assert len(overflow_msgs) > 0
        assert overflow_msgs[0]["payload"]["queue_utilization"] == 95.0
        assert overflow_msgs[0]["payload"]["backpressure_required"] is True

        # Verify backpressure signal
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        backpressure_msg = next(
            (m for m in bacnet_messages if m["type"] == "UPLOADER_BACKPRESSURE_SIGNAL"),
            None,
        )
        assert backpressure_msg is not None
        assert backpressure_msg["payload"]["reduce_collection_rate_by"] == 70
        assert backpressure_msg["payload"]["priority_devices_only"] is True

        # Verify throttling response
        uploader_messages = harness.get_actor_messages("uploader")
        throttling_msg = next(
            (
                m
                for m in uploader_messages
                if m["type"] == "BACNET_THROTTLING_ACTIVATED"
            ),
            None,
        )
        assert throttling_msg is not None
        assert throttling_msg["payload"]["throttled_device_count"] == 15
        assert throttling_msg["payload"]["collection_rate_reduction"] == 70

        # Verify queue recovery
        recovery_msgs = [
            m for m in all_messages if m.get("type") == "UPLOADER_QUEUE_RECOVERY"
        ]
        assert len(recovery_msgs) > 0
        assert recovery_msgs[0]["payload"]["backpressure_released"] is True
        assert recovery_msgs[0]["payload"]["gradual_ramp_up"] is True

        # Verify gradual ramp-up
        ramp_up_msg = next(
            (m for m in bacnet_messages if m["type"] == "UPLOADER_GRADUAL_RAMP_UP"),
            None,
        )
        assert ramp_up_msg is not None
        assert ramp_up_msg["payload"]["target_device_count"] == 25
        assert ramp_up_msg["payload"]["monitor_queue_closely"] is True

        await harness.cleanup()
