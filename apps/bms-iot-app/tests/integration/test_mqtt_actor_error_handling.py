"""
Test MQTT actor error handling and recovery patterns.

User Story: As a system operator, I want MQTT connection failures to be handled gracefully
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


class TestMQTTConnectionFailureHandling:
    """Test MQTT connection failure scenarios and recovery"""

    @pytest.mark.asyncio
    async def test_mqtt_broker_connection_failure_retry_fallback(self):
        """Test: MQTT broker connection failure → retry logic → fallback mode"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate connection failure
        connection_failure = {
            "type": "MQTT_CONNECTION_FAILURE",
            "sender": "mqtt",
            "receiver": "BROADCAST",
            "payload": {
                "broker_host": "mqtt.primary.com",
                "error": "ConnectionRefusedError",
                "retry_count": 1,
                "max_retries": 3,
                "fallback_available": True,
            },
        }

        await harness.send_message(connection_failure)
        await asyncio.sleep(0.1)

        # Simulate retry attempts
        for retry_count in range(2, 4):  # Retry 2 and 3
            retry_attempt = {
                "type": "MQTT_RETRY_ATTEMPT",
                "sender": "mqtt",
                "receiver": "heartbeat",
                "payload": {
                    "broker_host": "mqtt.primary.com",
                    "retry_count": retry_count,
                    "backoff_delay": 2**retry_count,  # Exponential backoff
                    "attempt_timestamp": time.time(),
                },
            }
            await harness.send_message(retry_attempt)
            await asyncio.sleep(0.05)

        # Simulate fallback activation
        fallback_activation = {
            "type": "MQTT_FALLBACK_ACTIVATED",
            "sender": "mqtt",
            "receiver": "BROADCAST",
            "payload": {
                "fallback_broker": "mqtt.backup.com",
                "primary_broker_failed": "mqtt.primary.com",
                "fallback_timestamp": time.time(),
                "expected_recovery_time": 300,
            },
        }

        await harness.send_message(fallback_activation)
        await asyncio.sleep(0.1)

        # Verify failure notification broadcast
        all_messages = harness.messages
        failure_msgs = [
            m for m in all_messages if m.get("type") == "MQTT_CONNECTION_FAILURE"
        ]
        assert len(failure_msgs) > 0

        # Verify retry attempts
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        retry_msgs = [
            m for m in heartbeat_messages if m["type"] == "MQTT_RETRY_ATTEMPT"
        ]
        assert len(retry_msgs) == 2  # Retry 2 and 3

        # Verify fallback activation broadcast
        fallback_msgs = [
            m for m in all_messages if m.get("type") == "MQTT_FALLBACK_ACTIVATED"
        ]
        assert len(fallback_msgs) > 0
        assert fallback_msgs[0]["payload"]["fallback_broker"] == "mqtt.backup.com"

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_mqtt_publish_failure_queuing_retry(self):
        """Test: MQTT publish failure → message queuing → retry on reconnection"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate publish failure
        publish_failure = {
            "type": "MQTT_PUBLISH_FAILURE",
            "sender": "mqtt",
            "receiver": "uploader",
            "payload": {
                "topic": "iot/data/device_001",
                "message_id": "msg_123",
                "error": "ConnectionLostError",
                "queued_for_retry": True,
                "queue_size": 1,
            },
        }

        await harness.send_message(publish_failure)
        await asyncio.sleep(0.1)

        # Add more failed messages to queue
        for i in range(2, 6):
            queue_update = {
                "type": "MQTT_MESSAGE_QUEUED",
                "sender": "mqtt",
                "receiver": "uploader",
                "payload": {
                    "message_id": f"msg_12{i}",
                    "topic": "iot/data/device_001",
                    "queue_position": i,
                    "queue_size": i,
                },
            }
            await harness.send_message(queue_update)

        await asyncio.sleep(0.1)

        # Simulate connection recovery
        connection_restored = {
            "type": "MQTT_CONNECTION_RESTORED",
            "sender": "mqtt",
            "receiver": "BROADCAST",
            "payload": {
                "broker_host": "mqtt.primary.com",
                "outage_duration": 30.5,
                "queued_messages": 5,
                "processing_queue": True,
            },
        }

        await harness.send_message(connection_restored)
        await asyncio.sleep(0.1)

        # Simulate queue processing
        queue_processed = {
            "type": "MQTT_QUEUE_PROCESSED",
            "sender": "mqtt",
            "receiver": "uploader",
            "payload": {
                "messages_processed": 5,
                "successful_publishes": 5,
                "failed_publishes": 0,
                "queue_cleared": True,
                "processing_time": 2.3,
            },
        }

        await harness.send_message(queue_processed)
        await asyncio.sleep(0.1)

        # Verify publish failure and queuing
        uploader_messages = harness.get_actor_messages("uploader")
        failure_msg = next(
            (m for m in uploader_messages if m["type"] == "MQTT_PUBLISH_FAILURE"), None
        )
        assert failure_msg is not None
        assert failure_msg["payload"]["queued_for_retry"] is True

        # Verify queue updates
        queue_msgs = [
            m for m in uploader_messages if m["type"] == "MQTT_MESSAGE_QUEUED"
        ]
        assert len(queue_msgs) == 4  # Messages 2-5

        # Verify connection restoration broadcast
        all_messages = harness.messages
        restore_msgs = [
            m for m in all_messages if m.get("type") == "MQTT_CONNECTION_RESTORED"
        ]
        assert len(restore_msgs) > 0
        assert restore_msgs[0]["payload"]["queued_messages"] == 5

        # Verify queue processing
        processed_msg = next(
            (m for m in uploader_messages if m["type"] == "MQTT_QUEUE_PROCESSED"), None
        )
        assert processed_msg is not None
        assert processed_msg["payload"]["queue_cleared"] is True

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_mqtt_subscription_loss_resubscription(self):
        """Test: MQTT subscription loss → resubscription → message recovery"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate subscription loss
        subscription_lost = {
            "type": "MQTT_SUBSCRIPTION_LOST",
            "sender": "mqtt",
            "receiver": "heartbeat",
            "payload": {
                "lost_topics": [
                    "iot/command/device_001/+",
                    "iot/config/device_001/+",
                    "iot/status/+/+",
                ],
                "loss_detected": time.time(),
                "auto_resubscribe": True,
            },
        }

        await harness.send_message(subscription_lost)
        await asyncio.sleep(0.1)

        # Simulate resubscription attempts
        resubscription_started = {
            "type": "MQTT_RESUBSCRIPTION_STARTED",
            "sender": "mqtt",
            "receiver": "heartbeat",
            "payload": {
                "topics_to_resubscribe": 3,
                "resubscription_strategy": "sequential",
                "started_at": time.time(),
            },
        }

        await harness.send_message(resubscription_started)
        await asyncio.sleep(0.1)

        # Simulate individual topic resubscriptions
        topics = [
            "iot/command/device_001/+",
            "iot/config/device_001/+",
            "iot/status/+/+",
        ]

        for i, topic in enumerate(topics):
            resubscribe_success = {
                "type": "MQTT_TOPIC_RESUBSCRIBED",
                "sender": "mqtt",
                "receiver": "heartbeat",
                "payload": {
                    "topic": topic,
                    "qos": 1,
                    "resubscription_order": i + 1,
                    "success": True,
                },
            }
            await harness.send_message(resubscribe_success)

        await asyncio.sleep(0.1)

        # Simulate message recovery (retained messages)
        message_recovery = {
            "type": "MQTT_MESSAGE_RECOVERY",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {
                "recovered_messages": 3,
                "topics_recovered": topics,
                "recovery_method": "retained_messages",
                "oldest_message_age": 120,  # 2 minutes old
            },
        }

        await harness.send_message(message_recovery)
        await asyncio.sleep(0.1)

        # Verify subscription loss detection
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        loss_msg = next(
            (m for m in heartbeat_messages if m["type"] == "MQTT_SUBSCRIPTION_LOST"),
            None,
        )
        assert loss_msg is not None
        assert len(loss_msg["payload"]["lost_topics"]) == 3

        # Verify resubscription process
        resubscribe_msgs = [
            m for m in heartbeat_messages if m["type"] == "MQTT_TOPIC_RESUBSCRIBED"
        ]
        assert len(resubscribe_msgs) == 3

        # Verify all topics were resubscribed
        resubscribed_topics = [msg["payload"]["topic"] for msg in resubscribe_msgs]
        assert set(resubscribed_topics) == set(topics)

        # Verify message recovery
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        recovery_msg = next(
            (m for m in bacnet_messages if m["type"] == "MQTT_MESSAGE_RECOVERY"), None
        )
        assert recovery_msg is not None
        assert recovery_msg["payload"]["recovered_messages"] == 3

        await harness.cleanup()


class TestMQTTMessageValidationErrors:
    """Test MQTT message validation and error handling"""

    @pytest.mark.asyncio
    async def test_invalid_mqtt_message_format_handling(self):
        """Test: Invalid MQTT message format → validation error → error response"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate invalid message received
        invalid_message_received = {
            "type": "MQTT_INVALID_MESSAGE_RECEIVED",
            "sender": "mqtt",
            "receiver": "heartbeat",
            "payload": {
                "topic": "iot/command/device_001/invalid",
                "raw_payload": "invalid{json}content",
                "validation_errors": [
                    "Invalid JSON format",
                    "Missing required field: command_type",
                    "Invalid timestamp format",
                ],
                "message_rejected": True,
                "sender_notified": True,
            },
        }

        await harness.send_message(invalid_message_received)
        await asyncio.sleep(0.1)

        # Send validation error response
        validation_error_response = {
            "type": "MQTT_VALIDATION_ERROR_RESPONSE",
            "sender": "mqtt",
            "receiver": "BROADCAST",
            "payload": {
                "error_topic": "iot/error/device_001/validation",
                "original_topic": "iot/command/device_001/invalid",
                "error_code": "VALIDATION_FAILED",
                "error_details": {
                    "validation_errors": [
                        "Invalid JSON format",
                        "Missing required field: command_type",
                        "Invalid timestamp format",
                    ],
                    "received_at": time.time(),
                    "corrective_action": "Fix message format and resend",
                },
            },
        }

        await harness.send_message(validation_error_response)
        await asyncio.sleep(0.1)

        # Verify invalid message handling
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        invalid_msg = next(
            (
                m
                for m in heartbeat_messages
                if m["type"] == "MQTT_INVALID_MESSAGE_RECEIVED"
            ),
            None,
        )
        assert invalid_msg is not None
        assert invalid_msg["payload"]["message_rejected"] is True
        assert len(invalid_msg["payload"]["validation_errors"]) == 3

        # Verify error response broadcast
        all_messages = harness.messages
        error_response_msgs = [
            m for m in all_messages if m.get("type") == "MQTT_VALIDATION_ERROR_RESPONSE"
        ]
        assert len(error_response_msgs) > 0
        assert error_response_msgs[0]["payload"]["error_code"] == "VALIDATION_FAILED"

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_mqtt_timeout_during_publish_handling(self):
        """Test: MQTT timeout during publish → timeout handling → status notification"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate publish timeout
        publish_timeout = {
            "type": "MQTT_PUBLISH_TIMEOUT",
            "sender": "mqtt",
            "receiver": "uploader",
            "payload": {
                "topic": "iot/data/device_001/bulk",
                "message_id": "bulk_upload_001",
                "timeout_duration": 30.0,
                "payload_size": 1024000,  # 1MB
                "retry_recommended": True,
                "timeout_reason": "broker_overload",
            },
        }

        await harness.send_message(publish_timeout)
        await asyncio.sleep(0.1)

        # Send timeout handling strategy
        timeout_strategy = {
            "type": "MQTT_TIMEOUT_STRATEGY",
            "sender": "mqtt",
            "receiver": "uploader",
            "payload": {
                "strategy": "split_and_retry",
                "original_message_id": "bulk_upload_001",
                "split_into_parts": 4,
                "part_size": 256000,  # 256KB each
                "retry_delay": 10.0,
            },
        }

        await harness.send_message(timeout_strategy)
        await asyncio.sleep(0.1)

        # Simulate retry with smaller chunks
        for part in range(1, 5):
            chunk_publish = {
                "type": "MQTT_CHUNK_PUBLISH",
                "sender": "mqtt",
                "receiver": "uploader",
                "payload": {
                    "original_message_id": "bulk_upload_001",
                    "chunk_id": f"chunk_{part}",
                    "chunk_size": 256000,
                    "chunk_sequence": part,
                    "total_chunks": 4,
                    "publish_success": True,
                },
            }
            await harness.send_message(chunk_publish)

        await asyncio.sleep(0.1)

        # Send chunked upload completion
        chunked_complete = {
            "type": "MQTT_CHUNKED_UPLOAD_COMPLETE",
            "sender": "mqtt",
            "receiver": "uploader",
            "payload": {
                "original_message_id": "bulk_upload_001",
                "total_chunks": 4,
                "successful_chunks": 4,
                "failed_chunks": 0,
                "total_size": 1024000,
                "upload_time": 15.2,
            },
        }

        await harness.send_message(chunked_complete)
        await asyncio.sleep(0.1)

        # Verify timeout handling
        uploader_messages = harness.get_actor_messages("uploader")
        timeout_msg = next(
            (m for m in uploader_messages if m["type"] == "MQTT_PUBLISH_TIMEOUT"), None
        )
        assert timeout_msg is not None
        assert timeout_msg["payload"]["timeout_duration"] == 30.0
        assert timeout_msg["payload"]["retry_recommended"] is True

        # Verify timeout strategy
        strategy_msg = next(
            (m for m in uploader_messages if m["type"] == "MQTT_TIMEOUT_STRATEGY"), None
        )
        assert strategy_msg is not None
        assert strategy_msg["payload"]["strategy"] == "split_and_retry"
        assert strategy_msg["payload"]["split_into_parts"] == 4

        # Verify chunk publishing
        chunk_msgs = [m for m in uploader_messages if m["type"] == "MQTT_CHUNK_PUBLISH"]
        assert len(chunk_msgs) == 4

        # Verify completion
        complete_msg = next(
            (
                m
                for m in uploader_messages
                if m["type"] == "MQTT_CHUNKED_UPLOAD_COMPLETE"
            ),
            None,
        )
        assert complete_msg is not None
        assert complete_msg["payload"]["successful_chunks"] == 4

        await harness.cleanup()


class TestMQTTQueueManagement:
    """Test MQTT queue management and overflow handling"""

    @pytest.mark.asyncio
    async def test_mqtt_queue_overflow_handling(self):
        """Test: MQTT queue overflow → queue management → backpressure"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate queue reaching capacity
        queue_warning = {
            "type": "MQTT_QUEUE_WARNING",
            "sender": "mqtt",
            "receiver": "BROADCAST",
            "payload": {
                "queue_type": "outbound_messages",
                "current_size": 800,
                "max_capacity": 1000,
                "utilization_percent": 80,
                "warning_threshold": 80,
            },
        }

        await harness.send_message(queue_warning)
        await asyncio.sleep(0.1)

        # Simulate queue overflow
        queue_overflow = {
            "type": "MQTT_QUEUE_OVERFLOW",
            "sender": "mqtt",
            "receiver": "BROADCAST",
            "payload": {
                "queue_type": "outbound_messages",
                "overflow_size": 50,
                "dropped_messages": 25,
                "queued_messages": 25,
                "overflow_policy": "drop_oldest",
                "backpressure_activated": True,
            },
        }

        await harness.send_message(queue_overflow)
        await asyncio.sleep(0.1)

        # Send backpressure signal to producers
        backpressure_signal = {
            "type": "MQTT_BACKPRESSURE_SIGNAL",
            "sender": "mqtt",
            "receiver": "bacnet_monitoring",
            "payload": {
                "backpressure_level": "high",
                "reduce_rate_by": 50,  # Reduce by 50%
                "estimated_duration": 60,
                "alternative_actions": [
                    "batch_messages",
                    "compress_payloads",
                    "prioritize_critical",
                ],
            },
        }

        await harness.send_message(backpressure_signal)
        await asyncio.sleep(0.1)

        # Simulate queue recovery
        queue_recovery = {
            "type": "MQTT_QUEUE_RECOVERY",
            "sender": "mqtt",
            "receiver": "BROADCAST",
            "payload": {
                "queue_type": "outbound_messages",
                "current_size": 300,
                "recovery_time": 45.0,
                "backpressure_released": True,
                "normal_operations_resumed": True,
            },
        }

        await harness.send_message(queue_recovery)
        await asyncio.sleep(0.1)

        # Verify queue warning broadcast
        all_messages = harness.messages
        warning_msgs = [
            m for m in all_messages if m.get("type") == "MQTT_QUEUE_WARNING"
        ]
        assert len(warning_msgs) > 0
        assert warning_msgs[0]["payload"]["utilization_percent"] == 80

        # Verify overflow handling
        overflow_msgs = [
            m for m in all_messages if m.get("type") == "MQTT_QUEUE_OVERFLOW"
        ]
        assert len(overflow_msgs) > 0
        assert overflow_msgs[0]["payload"]["backpressure_activated"] is True
        assert overflow_msgs[0]["payload"]["dropped_messages"] == 25

        # Verify backpressure signal
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        backpressure_msg = next(
            (m for m in bacnet_messages if m["type"] == "MQTT_BACKPRESSURE_SIGNAL"),
            None,
        )
        assert backpressure_msg is not None
        assert backpressure_msg["payload"]["reduce_rate_by"] == 50

        # Verify recovery
        recovery_msgs = [
            m for m in all_messages if m.get("type") == "MQTT_QUEUE_RECOVERY"
        ]
        assert len(recovery_msgs) > 0
        assert recovery_msgs[0]["payload"]["backpressure_released"] is True

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_mqtt_priority_queue_management(self):
        """Test: MQTT priority queue handling for critical messages"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate priority queue status
        priority_queue_status = {
            "type": "MQTT_PRIORITY_QUEUE_STATUS",
            "sender": "mqtt",
            "receiver": "heartbeat",
            "payload": {
                "critical_queue_size": 5,
                "high_queue_size": 15,
                "normal_queue_size": 100,
                "low_queue_size": 200,
                "processing_order": ["critical", "high", "normal", "low"],
            },
        }

        await harness.send_message(priority_queue_status)
        await asyncio.sleep(0.1)

        # Simulate critical message processing
        critical_message_processed = {
            "type": "MQTT_CRITICAL_MESSAGE_PROCESSED",
            "sender": "mqtt",
            "receiver": "heartbeat",
            "payload": {
                "message_type": "EMERGENCY_STOP",
                "processing_time": 0.05,
                "queue_bypass": True,
                "priority_level": "critical",
                "publish_success": True,
            },
        }

        await harness.send_message(critical_message_processed)
        await asyncio.sleep(0.1)

        # Simulate priority queue rebalancing
        queue_rebalancing = {
            "type": "MQTT_QUEUE_REBALANCING",
            "sender": "mqtt",
            "receiver": "heartbeat",
            "payload": {
                "rebalancing_reason": "critical_message_surge",
                "old_allocation": {"critical": 10, "high": 20, "normal": 30, "low": 40},
                "new_allocation": {"critical": 20, "high": 25, "normal": 25, "low": 30},
                "rebalancing_duration": 5.0,
            },
        }

        await harness.send_message(queue_rebalancing)
        await asyncio.sleep(0.1)

        # Verify priority queue status
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        status_msg = next(
            (
                m
                for m in heartbeat_messages
                if m["type"] == "MQTT_PRIORITY_QUEUE_STATUS"
            ),
            None,
        )
        assert status_msg is not None
        assert status_msg["payload"]["processing_order"][0] == "critical"

        # Verify critical message processing
        critical_msg = next(
            (
                m
                for m in heartbeat_messages
                if m["type"] == "MQTT_CRITICAL_MESSAGE_PROCESSED"
            ),
            None,
        )
        assert critical_msg is not None
        assert critical_msg["payload"]["queue_bypass"] is True
        assert critical_msg["payload"]["processing_time"] == 0.05

        # Verify queue rebalancing
        rebalance_msg = next(
            (m for m in heartbeat_messages if m["type"] == "MQTT_QUEUE_REBALANCING"),
            None,
        )
        assert rebalance_msg is not None
        assert rebalance_msg["payload"]["new_allocation"]["critical"] == 20

        await harness.cleanup()


class TestMQTTHealthMonitoring:
    """Test MQTT actor health monitoring and diagnostics"""

    @pytest.mark.asyncio
    async def test_mqtt_connection_health_monitoring(self):
        """Test: MQTT connection health monitoring and reporting"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate connection health metrics
        connection_health = {
            "type": "MQTT_CONNECTION_HEALTH",
            "sender": "mqtt",
            "receiver": "heartbeat",
            "payload": {
                "broker_host": "mqtt.primary.com",
                "connection_uptime": 3600,  # 1 hour
                "messages_sent": 1500,
                "messages_received": 800,
                "failed_publishes": 5,
                "failed_subscribes": 0,
                "average_latency": 50.2,  # ms
                "connection_quality": "excellent",
            },
        }

        await harness.send_message(connection_health)
        await asyncio.sleep(0.1)

        # Simulate degraded connection health
        degraded_health = {
            "type": "MQTT_CONNECTION_DEGRADED",
            "sender": "mqtt",
            "receiver": "BROADCAST",
            "payload": {
                "broker_host": "mqtt.primary.com",
                "degradation_factors": [
                    "high_latency",
                    "intermittent_drops",
                    "publish_failures",
                ],
                "current_latency": 250.5,  # ms
                "failure_rate": 5.2,  # percent
                "recommended_action": "investigate_network",
            },
        }

        await harness.send_message(degraded_health)
        await asyncio.sleep(0.1)

        # Simulate health improvement
        health_improved = {
            "type": "MQTT_CONNECTION_IMPROVED",
            "sender": "mqtt",
            "receiver": "BROADCAST",
            "payload": {
                "broker_host": "mqtt.primary.com",
                "improvement_factors": [
                    "latency_reduced",
                    "connection_stable",
                    "no_publish_failures",
                ],
                "current_latency": 45.0,  # ms
                "failure_rate": 0.1,  # percent
                "stability_duration": 600,  # 10 minutes stable
            },
        }

        await harness.send_message(health_improved)
        await asyncio.sleep(0.1)

        # Verify health monitoring
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        health_msg = next(
            (m for m in heartbeat_messages if m["type"] == "MQTT_CONNECTION_HEALTH"),
            None,
        )
        assert health_msg is not None
        assert health_msg["payload"]["connection_quality"] == "excellent"
        assert health_msg["payload"]["messages_sent"] == 1500

        # Verify degradation notification
        all_messages = harness.messages
        degraded_msgs = [
            m for m in all_messages if m.get("type") == "MQTT_CONNECTION_DEGRADED"
        ]
        assert len(degraded_msgs) > 0
        assert "high_latency" in degraded_msgs[0]["payload"]["degradation_factors"]

        # Verify improvement notification
        improved_msgs = [
            m for m in all_messages if m.get("type") == "MQTT_CONNECTION_IMPROVED"
        ]
        assert len(improved_msgs) > 0
        assert improved_msgs[0]["payload"]["current_latency"] == 45.0

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_mqtt_diagnostic_reporting(self):
        """Test: MQTT diagnostic data collection and reporting"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Request diagnostic report
        diagnostic_request = {
            "type": "MQTT_DIAGNOSTIC_REQUEST",
            "sender": "heartbeat",
            "receiver": "mqtt",
            "payload": {
                "diagnostic_level": "comprehensive",
                "include_statistics": True,
                "include_error_log": True,
                "time_window": 3600,  # Last hour
            },
        }

        await harness.send_message(diagnostic_request)
        await asyncio.sleep(0.1)

        # Generate diagnostic report
        diagnostic_report = {
            "type": "MQTT_DIAGNOSTIC_REPORT",
            "sender": "mqtt",
            "receiver": "heartbeat",
            "payload": {
                "report_timestamp": time.time(),
                "broker_info": {
                    "primary_broker": "mqtt.primary.com:1883",
                    "fallback_broker": "mqtt.backup.com:1883",
                    "current_broker": "mqtt.primary.com:1883",
                },
                "connection_statistics": {
                    "total_connections": 1,
                    "connection_uptime": 3600,
                    "reconnection_count": 2,
                    "last_reconnection": time.time() - 1800,
                },
                "message_statistics": {
                    "total_published": 2500,
                    "total_received": 1200,
                    "failed_publishes": 8,
                    "queued_messages": 0,
                },
                "error_summary": {
                    "connection_errors": 2,
                    "publish_errors": 8,
                    "validation_errors": 3,
                    "timeout_errors": 1,
                },
                "performance_metrics": {
                    "average_publish_latency": 48.5,
                    "peak_publish_latency": 450.0,
                    "message_throughput": 0.69,  # messages per second
                },
            },
        }

        await harness.send_message(diagnostic_report)
        await asyncio.sleep(0.1)

        # Verify diagnostic request
        mqtt_messages = harness.get_actor_messages("mqtt")
        request_msg = next(
            (m for m in mqtt_messages if m["type"] == "MQTT_DIAGNOSTIC_REQUEST"), None
        )
        assert request_msg is not None
        assert request_msg["payload"]["diagnostic_level"] == "comprehensive"

        # Verify diagnostic report
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        report_msg = next(
            (m for m in heartbeat_messages if m["type"] == "MQTT_DIAGNOSTIC_REPORT"),
            None,
        )
        assert report_msg is not None

        # Verify report completeness
        payload = report_msg["payload"]
        assert "broker_info" in payload
        assert "connection_statistics" in payload
        assert "message_statistics" in payload
        assert "error_summary" in payload
        assert "performance_metrics" in payload

        # Verify specific metrics
        assert payload["message_statistics"]["total_published"] == 2500
        assert payload["error_summary"]["publish_errors"] == 8
        assert payload["performance_metrics"]["average_publish_latency"] == 48.5

        await harness.cleanup()
