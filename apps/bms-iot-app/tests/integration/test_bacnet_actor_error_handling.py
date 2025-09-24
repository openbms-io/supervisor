"""
Test BACnet actor error handling and recovery patterns.

User Story: As a building manager, I want BACnet device failures to not crash the system
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


class TestBACnetConnectionFailureHandling:
    """Test BACnet connection failure scenarios and recovery"""

    @pytest.mark.asyncio
    async def test_bac0_connection_failure_retry_offline_marking(self):
        """Test: BAC0 connection failure → retry logic → device marked offline"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate BAC0 connection failure
        connection_failure = {
            "type": "BACNET_CONNECTION_FAILURE",
            "sender": "bacnet_monitoring",
            "receiver": "heartbeat",
            "payload": {
                "device_ip": "192.168.1.100",
                "device_id": 1001,
                "error": "ConnectionError: Device unreachable",
                "retry_count": 1,
                "max_retries": 3,
                "connection_timeout": 5.0,
            },
        }

        await harness.send_message(connection_failure)
        await asyncio.sleep(0.1)

        # Simulate retry attempts
        for retry_count in range(2, 4):  # Retry 2 and 3
            retry_attempt = {
                "type": "BACNET_RETRY_ATTEMPT",
                "sender": "bacnet_monitoring",
                "receiver": "heartbeat",
                "payload": {
                    "device_ip": "192.168.1.100",
                    "device_id": 1001,
                    "retry_count": retry_count,
                    "backoff_delay": retry_count * 2,  # Linear backoff
                    "attempt_timestamp": time.time(),
                    "retry_strategy": "exponential_backoff",
                },
            }
            await harness.send_message(retry_attempt)
            await asyncio.sleep(0.05)

        # Simulate device marked offline after retries exhausted
        device_offline = {
            "type": "BACNET_DEVICE_OFFLINE",
            "sender": "bacnet_monitoring",
            "receiver": "BROADCAST",
            "payload": {
                "device_ip": "192.168.1.100",
                "device_id": 1001,
                "offline_timestamp": time.time(),
                "total_retry_attempts": 3,
                "next_check_interval": 300,  # 5 minutes
                "offline_reason": "connection_failure_after_retries",
            },
        }

        await harness.send_message(device_offline)
        await asyncio.sleep(0.1)

        # Verify connection failure notification
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        failure_msg = next(
            (m for m in heartbeat_messages if m["type"] == "BACNET_CONNECTION_FAILURE"),
            None,
        )
        assert failure_msg is not None
        assert failure_msg["payload"]["device_id"] == 1001
        assert failure_msg["payload"]["max_retries"] == 3

        # Verify retry attempts
        retry_msgs = [
            m for m in heartbeat_messages if m["type"] == "BACNET_RETRY_ATTEMPT"
        ]
        assert len(retry_msgs) == 2  # Retry 2 and 3

        # Verify device offline broadcast
        all_messages = harness.messages
        offline_msgs = [
            m for m in all_messages if m.get("type") == "BACNET_DEVICE_OFFLINE"
        ]
        assert len(offline_msgs) > 0
        assert (
            offline_msgs[0]["payload"]["offline_reason"]
            == "connection_failure_after_retries"
        )

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_bacnet_device_timeout_skip_next_cycle(self):
        """Test: BACnet device timeout → timeout handling → skip device in next cycle"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate device timeout during read operation
        device_timeout = {
            "type": "BACNET_DEVICE_TIMEOUT",
            "sender": "bacnet_monitoring",
            "receiver": "heartbeat",
            "payload": {
                "device_ip": "192.168.1.101",
                "device_id": 1002,
                "operation": "read_multiple_points",
                "timeout_duration": 10.0,
                "points_requested": 15,
                "points_received": 3,
                "partial_data_available": True,
            },
        }

        await harness.send_message(device_timeout)
        await asyncio.sleep(0.1)

        # Send timeout strategy decision
        timeout_strategy = {
            "type": "BACNET_TIMEOUT_STRATEGY",
            "sender": "bacnet_monitoring",
            "receiver": "heartbeat",
            "payload": {
                "device_id": 1002,
                "strategy": "skip_next_cycle",
                "skip_duration": 60,  # Skip for 1 minute
                "fallback_action": "use_cached_data",
                "timeout_threshold_exceeded": True,
                "consecutive_timeouts": 1,
            },
        }

        await harness.send_message(timeout_strategy)
        await asyncio.sleep(0.1)

        # Simulate next cycle skip notification
        cycle_skip = {
            "type": "BACNET_CYCLE_SKIP",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_id": 1002,
                "skip_reason": "recent_timeout",
                "skipped_at": time.time(),
                "next_attempt_at": time.time() + 60,
                "using_cached_data": True,
                "cached_data_age": 120,  # 2 minutes old
            },
        }

        await harness.send_message(cycle_skip)
        await asyncio.sleep(0.1)

        # Verify timeout handling
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        timeout_msg = next(
            (m for m in heartbeat_messages if m["type"] == "BACNET_DEVICE_TIMEOUT"),
            None,
        )
        assert timeout_msg is not None
        assert timeout_msg["payload"]["timeout_duration"] == 10.0
        assert timeout_msg["payload"]["partial_data_available"] is True

        # Verify timeout strategy
        strategy_msg = next(
            (m for m in heartbeat_messages if m["type"] == "BACNET_TIMEOUT_STRATEGY"),
            None,
        )
        assert strategy_msg is not None
        assert strategy_msg["payload"]["strategy"] == "skip_next_cycle"
        assert strategy_msg["payload"]["skip_duration"] == 60

        # Verify cycle skip notification to uploader
        uploader_messages = harness.get_actor_messages("uploader")
        skip_msg = next(
            (m for m in uploader_messages if m["type"] == "BACNET_CYCLE_SKIP"), None
        )
        assert skip_msg is not None
        assert skip_msg["payload"]["using_cached_data"] is True

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_bacnet_network_partition_isolation_reconnection(self):
        """Test: BACnet network partition → isolation detection → reconnection workflow"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate network partition detection
        network_partition = {
            "type": "BACNET_NETWORK_PARTITION",
            "sender": "bacnet_monitoring",
            "receiver": "BROADCAST",
            "payload": {
                "partition_detected": True,
                "affected_devices": [1001, 1002, 1003],
                "network_segment": "192.168.1.0/24",
                "partition_timestamp": time.time(),
                "detection_method": "multiple_device_failure",
            },
        }

        await harness.send_message(network_partition)
        await asyncio.sleep(0.1)

        # Simulate isolation mode activation
        isolation_mode = {
            "type": "BACNET_ISOLATION_MODE_ACTIVATED",
            "sender": "bacnet_monitoring",
            "receiver": "heartbeat",
            "payload": {
                "isolation_level": "network_segment",
                "affected_devices": [1001, 1002, 1003],
                "isolation_duration": 0,  # Until reconnection
                "monitoring_strategy": "periodic_ping",
                "ping_interval": 30,  # Every 30 seconds
            },
        }

        await harness.send_message(isolation_mode)
        await asyncio.sleep(0.1)

        # Simulate periodic connectivity checks
        for check_count in range(1, 4):
            connectivity_check = {
                "type": "BACNET_CONNECTIVITY_CHECK",
                "sender": "bacnet_monitoring",
                "receiver": "heartbeat",
                "payload": {
                    "check_number": check_count,
                    "devices_tested": [1001, 1002, 1003],
                    "devices_responsive": (
                        [] if check_count < 3 else [1001, 1003]
                    ),  # Partial recovery on 3rd check
                    "check_timestamp": time.time(),
                    "next_check_in": 30,
                },
            }
            await harness.send_message(connectivity_check)
            await asyncio.sleep(0.05)

        # Simulate partial network recovery
        partial_recovery = {
            "type": "BACNET_PARTIAL_RECOVERY",
            "sender": "bacnet_monitoring",
            "receiver": "BROADCAST",
            "payload": {
                "recovered_devices": [1001, 1003],
                "still_unreachable": [1002],
                "recovery_timestamp": time.time(),
                "recovery_method": "gradual_reconnection",
                "network_stability": "improving",
            },
        }

        await harness.send_message(partial_recovery)
        await asyncio.sleep(0.1)

        # Verify network partition detection
        all_messages = harness.messages
        partition_msgs = [
            m for m in all_messages if m.get("type") == "BACNET_NETWORK_PARTITION"
        ]
        assert len(partition_msgs) > 0
        assert len(partition_msgs[0]["payload"]["affected_devices"]) == 3

        # Verify isolation mode activation
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        isolation_msg = next(
            (
                m
                for m in heartbeat_messages
                if m["type"] == "BACNET_ISOLATION_MODE_ACTIVATED"
            ),
            None,
        )
        assert isolation_msg is not None
        assert isolation_msg["payload"]["isolation_level"] == "network_segment"

        # Verify connectivity checks
        check_msgs = [
            m for m in heartbeat_messages if m["type"] == "BACNET_CONNECTIVITY_CHECK"
        ]
        assert len(check_msgs) == 3

        # Verify partial recovery
        recovery_msgs = [
            m for m in all_messages if m.get("type") == "BACNET_PARTIAL_RECOVERY"
        ]
        assert len(recovery_msgs) > 0
        assert len(recovery_msgs[0]["payload"]["recovered_devices"]) == 2
        assert len(recovery_msgs[0]["payload"]["still_unreachable"]) == 1

        await harness.cleanup()


class TestBACnetDataHandlingErrors:
    """Test BACnet data handling and parsing errors"""

    @pytest.mark.asyncio
    async def test_invalid_bacnet_response_error_parsing_continue(self):
        """Test: Invalid BACnet response → error parsing → continue with other devices"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate invalid BACnet response received
        invalid_response = {
            "type": "BACNET_INVALID_RESPONSE",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_ip": "192.168.1.104",
                "device_id": 1004,
                "operation": "read_present_value",
                "point_name": "AV_Temperature_01",
                "raw_response": "corrupted_binary_data_0x4A5B3C",
                "parsing_errors": [
                    "Invalid BACnet data type",
                    "Checksum mismatch",
                    "Unexpected response length",
                ],
                "error_timestamp": time.time(),
            },
        }

        await harness.send_message(invalid_response)
        await asyncio.sleep(0.1)

        # Send parsing error handling strategy
        parsing_strategy = {
            "type": "BACNET_PARSING_STRATEGY",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_id": 1004,
                "strategy": "skip_point_continue_device",
                "failed_point": "AV_Temperature_01",
                "fallback_action": "use_last_known_value",
                "last_known_value": 22.5,
                "last_known_timestamp": time.time() - 300,
            },
        }

        await harness.send_message(parsing_strategy)
        await asyncio.sleep(0.1)

        # Simulate continuing with other devices
        continue_processing = {
            "type": "BACNET_CONTINUE_WITH_OTHER_DEVICES",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "skipped_device": 1004,
                "continuing_with_devices": [1001, 1002, 1003],
                "processing_resumed": True,
                "total_devices_in_cycle": 4,
                "successful_devices": 3,
                "failed_devices": 1,
            },
        }

        await harness.send_message(continue_processing)
        await asyncio.sleep(0.1)

        # Send successful processing of other devices
        successful_processing = {
            "type": "BACNET_SUCCESSFUL_DEVICE_READ",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_id": 1001,
                "points_read": 12,
                "points_successful": 12,
                "points_failed": 0,
                "read_duration": 2.3,
                "data_quality": "good",
            },
        }

        await harness.send_message(successful_processing)
        await asyncio.sleep(0.1)

        # Verify invalid response handling
        uploader_messages = harness.get_actor_messages("uploader")
        invalid_msg = next(
            (m for m in uploader_messages if m["type"] == "BACNET_INVALID_RESPONSE"),
            None,
        )
        assert invalid_msg is not None
        assert len(invalid_msg["payload"]["parsing_errors"]) == 3
        assert invalid_msg["payload"]["device_id"] == 1004

        # Verify parsing strategy
        strategy_msg = next(
            (m for m in uploader_messages if m["type"] == "BACNET_PARSING_STRATEGY"),
            None,
        )
        assert strategy_msg is not None
        assert strategy_msg["payload"]["strategy"] == "skip_point_continue_device"
        assert strategy_msg["payload"]["fallback_action"] == "use_last_known_value"

        # Verify processing continued with other devices
        continue_msg = next(
            (
                m
                for m in uploader_messages
                if m["type"] == "BACNET_CONTINUE_WITH_OTHER_DEVICES"
            ),
            None,
        )
        assert continue_msg is not None
        assert continue_msg["payload"]["successful_devices"] == 3
        assert continue_msg["payload"]["failed_devices"] == 1

        # Verify successful device processing
        success_msg = next(
            (
                m
                for m in uploader_messages
                if m["type"] == "BACNET_SUCCESSFUL_DEVICE_READ"
            ),
            None,
        )
        assert success_msg is not None
        assert success_msg["payload"]["points_successful"] == 12

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_bac0_exception_during_read_error_logging(self):
        """Test: BAC0 exception during read → exception handling → error logging"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate BAC0 exception during read
        bac0_exception = {
            "type": "BACNET_BAC0_EXCEPTION",
            "sender": "bacnet_monitoring",
            "receiver": "heartbeat",
            "payload": {
                "device_ip": "192.168.1.105",
                "device_id": 1005,
                "operation": "read_multiple",
                "exception_type": "ReadPropertyException",
                "exception_message": "Object does not support property",
                "exception_details": {
                    "object_identifier": "analogValue:1",
                    "property_identifier": "present-value",
                    "error_class": "property",
                    "error_code": "unknown-property",
                },
                "stack_trace": "BAC0.core.io.IOExceptions.ReadPropertyException...",
                "operation_timestamp": time.time(),
            },
        }

        await harness.send_message(bac0_exception)
        await asyncio.sleep(0.1)

        # Send exception handling decision
        exception_handling = {
            "type": "BACNET_EXCEPTION_HANDLING",
            "sender": "bacnet_monitoring",
            "receiver": "heartbeat",
            "payload": {
                "device_id": 1005,
                "exception_type": "ReadPropertyException",
                "handling_strategy": "log_and_skip_property",
                "recovery_action": "try_alternative_property",
                "alternative_property": "reliability",
                "error_logged": True,
                "operation_continued": True,
            },
        }

        await harness.send_message(exception_handling)
        await asyncio.sleep(0.1)

        # Simulate error logging details
        error_logged = {
            "type": "BACNET_ERROR_LOGGED",
            "sender": "bacnet_monitoring",
            "receiver": "heartbeat",
            "payload": {
                "log_level": "ERROR",
                "log_message": "BAC0 ReadPropertyException for device 1005",
                "log_details": {
                    "device_id": 1005,
                    "operation": "read_multiple",
                    "error_class": "property",
                    "error_code": "unknown-property",
                    "timestamp": time.time(),
                },
                "log_category": "bacnet_operations",
                "error_count_for_device": 1,
            },
        }

        await harness.send_message(error_logged)
        await asyncio.sleep(0.1)

        # Simulate successful alternative property read
        alternative_success = {
            "type": "BACNET_ALTERNATIVE_READ_SUCCESS",
            "sender": "bacnet_monitoring",
            "receiver": "uploader",
            "payload": {
                "device_id": 1005,
                "original_property": "present-value",
                "alternative_property": "reliability",
                "alternative_value": "no-fault-detected",
                "read_successful": True,
                "fallback_strategy_used": True,
            },
        }

        await harness.send_message(alternative_success)
        await asyncio.sleep(0.1)

        # Verify BAC0 exception handling
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        exception_msg = next(
            (m for m in heartbeat_messages if m["type"] == "BACNET_BAC0_EXCEPTION"),
            None,
        )
        assert exception_msg is not None
        assert exception_msg["payload"]["exception_type"] == "ReadPropertyException"
        assert exception_msg["payload"]["device_id"] == 1005

        # Verify exception handling strategy
        handling_msg = next(
            (m for m in heartbeat_messages if m["type"] == "BACNET_EXCEPTION_HANDLING"),
            None,
        )
        assert handling_msg is not None
        assert handling_msg["payload"]["handling_strategy"] == "log_and_skip_property"
        assert handling_msg["payload"]["recovery_action"] == "try_alternative_property"

        # Verify error logging
        logged_msg = next(
            (m for m in heartbeat_messages if m["type"] == "BACNET_ERROR_LOGGED"), None
        )
        assert logged_msg is not None
        assert logged_msg["payload"]["log_level"] == "ERROR"
        assert logged_msg["payload"]["error_count_for_device"] == 1

        # Verify alternative read success
        uploader_messages = harness.get_actor_messages("uploader")
        alt_success_msg = next(
            (
                m
                for m in uploader_messages
                if m["type"] == "BACNET_ALTERNATIVE_READ_SUCCESS"
            ),
            None,
        )
        assert alt_success_msg is not None
        assert alt_success_msg["payload"]["alternative_property"] == "reliability"
        assert alt_success_msg["payload"]["read_successful"] is True

        await harness.cleanup()


class TestBACnetPerformanceMonitoring:
    """Test BACnet performance monitoring and degradation handling"""

    @pytest.mark.asyncio
    async def test_bacnet_performance_degradation_monitoring(self):
        """Test: BACnet performance degradation monitoring and adaptive response"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate performance degradation detection
        performance_degradation = {
            "type": "BACNET_PERFORMANCE_DEGRADATION",
            "sender": "bacnet_monitoring",
            "receiver": "heartbeat",
            "payload": {
                "degradation_type": "response_time_increase",
                "baseline_response_time": 1.2,  # seconds
                "current_response_time": 5.8,  # seconds
                "degradation_percentage": 383,  # 383% increase
                "affected_devices": [1001, 1002, 1003],
                "detection_timestamp": time.time(),
                "degradation_trend": "increasing",
            },
        }

        await harness.send_message(performance_degradation)
        await asyncio.sleep(0.1)

        # Send adaptive response strategy
        adaptive_strategy = {
            "type": "BACNET_ADAPTIVE_STRATEGY",
            "sender": "bacnet_monitoring",
            "receiver": "heartbeat",
            "payload": {
                "strategy_type": "reduce_polling_frequency",
                "original_polling_interval": 30,  # 30 seconds
                "new_polling_interval": 60,  # 60 seconds
                "timeout_adjustment": "increase_by_50_percent",
                "new_timeout": 15.0,  # increased from 10.0
                "batch_size_reduction": "reduce_by_half",
                "new_batch_size": 5,  # reduced from 10
            },
        }

        await harness.send_message(adaptive_strategy)
        await asyncio.sleep(0.1)

        # Simulate strategy implementation results
        strategy_results = {
            "type": "BACNET_STRATEGY_RESULTS",
            "sender": "bacnet_monitoring",
            "receiver": "heartbeat",
            "payload": {
                "strategy_applied": "reduce_polling_frequency",
                "implementation_timestamp": time.time(),
                "immediate_impact": {
                    "response_time_improvement": 2.1,  # Down to 3.7s from 5.8s
                    "error_rate_reduction": 15.0,  # 15% fewer errors
                    "successful_reads_percentage": 85,  # Up from 70%
                },
                "monitoring_period": 300,  # Monitor for 5 minutes
                "success_metrics": {
                    "strategy_effective": True,
                    "performance_stabilizing": True,
                },
            },
        }

        await harness.send_message(strategy_results)
        await asyncio.sleep(0.1)

        # Verify performance degradation detection
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        degradation_msg = next(
            (
                m
                for m in heartbeat_messages
                if m["type"] == "BACNET_PERFORMANCE_DEGRADATION"
            ),
            None,
        )
        assert degradation_msg is not None
        assert degradation_msg["payload"]["degradation_percentage"] == 383
        assert len(degradation_msg["payload"]["affected_devices"]) == 3

        # Verify adaptive strategy
        strategy_msg = next(
            (m for m in heartbeat_messages if m["type"] == "BACNET_ADAPTIVE_STRATEGY"),
            None,
        )
        assert strategy_msg is not None
        assert strategy_msg["payload"]["strategy_type"] == "reduce_polling_frequency"
        assert strategy_msg["payload"]["new_polling_interval"] == 60

        # Verify strategy results
        results_msg = next(
            (m for m in heartbeat_messages if m["type"] == "BACNET_STRATEGY_RESULTS"),
            None,
        )
        assert results_msg is not None
        assert (
            results_msg["payload"]["immediate_impact"]["response_time_improvement"]
            == 2.1
        )
        assert results_msg["payload"]["success_metrics"]["strategy_effective"] is True

        await harness.cleanup()
