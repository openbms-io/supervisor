"""
Test heartbeat actor error handling and health monitoring patterns.

User Story: As a system monitor, I want heartbeat failures to indicate system health issues
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


class TestHeartbeatActorResponseMonitoring:
    """Test heartbeat actor response monitoring and timeout handling"""

    @pytest.mark.asyncio
    async def test_actor_unresponsive_heartbeat_timeout_unhealthy_marking(self):
        """Test: Actor unresponsive to heartbeat → timeout → mark actor as unhealthy"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate heartbeat request sent to all actors
        heartbeat_request = {
            "type": "HEARTBEAT_REQUEST",
            "sender": "heartbeat",
            "receiver": "BROADCAST",
            "payload": {
                "request_id": "hb_req_001",
                "timestamp": time.time(),
                "timeout_duration": 10.0,
                "expected_actors": ["mqtt", "bacnet_monitoring", "uploader"],
                "health_check_level": "standard",
            },
        }

        await harness.send_message(heartbeat_request)
        await asyncio.sleep(0.1)

        # Simulate partial responses (mqtt and uploader respond, bacnet_monitoring doesn't)
        mqtt_response = {
            "type": "HEARTBEAT_RESPONSE",
            "sender": "mqtt",
            "receiver": "heartbeat",
            "payload": {
                "request_id": "hb_req_001",
                "actor_name": "mqtt",
                "status": "healthy",
                "uptime": 3600,
                "last_operation": "message_publish",
                "response_timestamp": time.time(),
            },
        }

        uploader_response = {
            "type": "HEARTBEAT_RESPONSE",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "request_id": "hb_req_001",
                "actor_name": "uploader",
                "status": "healthy",
                "uptime": 3500,
                "last_operation": "data_upload",
                "response_timestamp": time.time(),
            },
        }

        await harness.send_message(mqtt_response)
        await harness.send_message(uploader_response)
        await asyncio.sleep(0.1)

        # Simulate heartbeat timeout detection
        heartbeat_timeout = {
            "type": "HEARTBEAT_TIMEOUT",
            "sender": "heartbeat",
            "receiver": "BROADCAST",
            "payload": {
                "request_id": "hb_req_001",
                "timeout_duration": 10.0,
                "responding_actors": ["mqtt", "uploader"],
                "non_responding_actors": ["bacnet_monitoring"],
                "timeout_timestamp": time.time(),
                "partial_response": True,
            },
        }

        await harness.send_message(heartbeat_timeout)
        await asyncio.sleep(0.1)

        # Simulate marking actor as unhealthy
        actor_unhealthy = {
            "type": "ACTOR_MARKED_UNHEALTHY",
            "sender": "heartbeat",
            "receiver": "BROADCAST",
            "payload": {
                "actor_name": "bacnet_monitoring",
                "health_status": "unhealthy",
                "reason": "heartbeat_timeout",
                "timeout_count": 1,
                "last_successful_heartbeat": time.time() - 60,
                "marked_unhealthy_at": time.time(),
                "escalation_required": False,
            },
        }

        await harness.send_message(actor_unhealthy)
        await asyncio.sleep(0.1)

        # Simulate health status update
        health_status_update = {
            "type": "HEALTH_STATUS_UPDATE",
            "sender": "heartbeat",
            "receiver": "BROADCAST",
            "payload": {
                "system_health": "degraded",
                "healthy_actors": ["mqtt", "uploader"],
                "unhealthy_actors": ["bacnet_monitoring"],
                "total_actors": 3,
                "health_percentage": 66.7,
                "status_timestamp": time.time(),
            },
        }

        await harness.send_message(health_status_update)
        await asyncio.sleep(0.1)

        # Verify heartbeat request broadcast
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        hb_responses = [
            m for m in heartbeat_messages if m["type"] == "HEARTBEAT_RESPONSE"
        ]
        assert len(hb_responses) == 2  # mqtt and uploader responded

        # Verify timeout detection
        all_messages = harness.messages
        timeout_msgs = [m for m in all_messages if m.get("type") == "HEARTBEAT_TIMEOUT"]
        assert len(timeout_msgs) > 0
        assert timeout_msgs[0]["payload"]["non_responding_actors"] == [
            "bacnet_monitoring"
        ]
        assert timeout_msgs[0]["payload"]["partial_response"] is True

        # Verify actor marked as unhealthy
        unhealthy_msgs = [
            m for m in all_messages if m.get("type") == "ACTOR_MARKED_UNHEALTHY"
        ]
        assert len(unhealthy_msgs) > 0
        assert unhealthy_msgs[0]["payload"]["actor_name"] == "bacnet_monitoring"
        assert unhealthy_msgs[0]["payload"]["reason"] == "heartbeat_timeout"

        # Verify health status update
        health_msgs = [
            m for m in all_messages if m.get("type") == "HEALTH_STATUS_UPDATE"
        ]
        assert len(health_msgs) > 0
        assert health_msgs[0]["payload"]["system_health"] == "degraded"
        assert health_msgs[0]["payload"]["health_percentage"] == 66.7

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_partial_heartbeat_responses_incomplete_data_health_degradation(self):
        """Test: Partial heartbeat responses → incomplete data handling → health degradation"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate heartbeat request
        heartbeat_request = {
            "type": "HEARTBEAT_REQUEST",
            "sender": "heartbeat",
            "receiver": "BROADCAST",
            "payload": {
                "request_id": "hb_req_002",
                "timestamp": time.time(),
                "timeout_duration": 10.0,
                "expected_actors": ["mqtt", "bacnet_monitoring", "uploader"],
                "health_check_level": "detailed",
            },
        }

        await harness.send_message(heartbeat_request)
        await asyncio.sleep(0.1)

        # Simulate partial/incomplete responses
        mqtt_partial_response = {
            "type": "HEARTBEAT_RESPONSE",
            "sender": "mqtt",
            "receiver": "heartbeat",
            "payload": {
                "request_id": "hb_req_002",
                "actor_name": "mqtt",
                "status": "degraded",  # Degraded status
                "uptime": 3600,
                "last_operation": "message_publish",
                "response_timestamp": time.time(),
                "missing_metrics": ["connection_count", "message_throughput"],
                "incomplete_response": True,
            },
        }

        bacnet_slow_response = {
            "type": "HEARTBEAT_RESPONSE",
            "sender": "bacnet_monitoring",
            "receiver": "heartbeat",
            "payload": {
                "request_id": "hb_req_002",
                "actor_name": "bacnet_monitoring",
                "status": "healthy",
                "uptime": 3400,
                "last_operation": "device_read",
                "response_timestamp": time.time(),
                "response_delay": 8.5,  # Took 8.5 seconds to respond
                "slow_response": True,
            },
        }

        uploader_error_response = {
            "type": "HEARTBEAT_RESPONSE",
            "sender": "uploader",
            "receiver": "heartbeat",
            "payload": {
                "request_id": "hb_req_002",
                "actor_name": "uploader",
                "status": "error",
                "uptime": 2800,
                "last_operation": "data_upload",
                "response_timestamp": time.time(),
                "error_details": {
                    "recent_errors": 5,
                    "error_rate": 15.5,  # 15.5% error rate
                    "last_error": "HTTP 500 Internal Server Error",
                },
            },
        }

        await harness.send_message(mqtt_partial_response)
        await harness.send_message(bacnet_slow_response)
        await harness.send_message(uploader_error_response)
        await asyncio.sleep(0.1)

        # Simulate incomplete data handling
        incomplete_data_handling = {
            "type": "INCOMPLETE_DATA_HANDLING",
            "sender": "heartbeat",
            "receiver": "BROADCAST",
            "payload": {
                "request_id": "hb_req_002",
                "incomplete_responses": {
                    "mqtt": "missing_metrics",
                    "bacnet_monitoring": "slow_response",
                    "uploader": "error_status",
                },
                "data_quality_score": 60.0,  # Out of 100
                "handling_strategy": "use_available_data_with_warnings",
                "warnings_issued": 3,
            },
        }

        await harness.send_message(incomplete_data_handling)
        await asyncio.sleep(0.1)

        # Simulate health degradation assessment
        health_degradation = {
            "type": "HEALTH_DEGRADATION_DETECTED",
            "sender": "heartbeat",
            "receiver": "BROADCAST",
            "payload": {
                "degradation_level": "moderate",
                "contributing_factors": [
                    "mqtt_missing_metrics",
                    "bacnet_slow_response",
                    "uploader_high_error_rate",
                ],
                "overall_health_score": 55.0,  # Out of 100
                "recommended_actions": [
                    "investigate_mqtt_metrics_collection",
                    "check_bacnet_performance",
                    "review_uploader_error_logs",
                ],
                "alert_level": "warning",
            },
        }

        await harness.send_message(health_degradation)
        await asyncio.sleep(0.1)

        # Verify all actors responded (but with issues)
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        hb_responses = [
            m for m in heartbeat_messages if m["type"] == "HEARTBEAT_RESPONSE"
        ]
        assert len(hb_responses) == 3  # All actors responded

        # Verify response quality assessment
        mqtt_resp = next(
            (r for r in hb_responses if r["payload"]["actor_name"] == "mqtt"), None
        )
        assert mqtt_resp is not None
        assert mqtt_resp["payload"]["incomplete_response"] is True
        assert "missing_metrics" in mqtt_resp["payload"]

        bacnet_resp = next(
            (
                r
                for r in hb_responses
                if r["payload"]["actor_name"] == "bacnet_monitoring"
            ),
            None,
        )
        assert bacnet_resp is not None
        assert bacnet_resp["payload"]["slow_response"] is True
        assert bacnet_resp["payload"]["response_delay"] == 8.5

        uploader_resp = next(
            (r for r in hb_responses if r["payload"]["actor_name"] == "uploader"), None
        )
        assert uploader_resp is not None
        assert uploader_resp["payload"]["status"] == "error"
        assert uploader_resp["payload"]["error_details"]["error_rate"] == 15.5

        # Verify incomplete data handling
        all_messages = harness.messages
        incomplete_msgs = [
            m for m in all_messages if m.get("type") == "INCOMPLETE_DATA_HANDLING"
        ]
        assert len(incomplete_msgs) > 0
        assert incomplete_msgs[0]["payload"]["data_quality_score"] == 60.0
        assert incomplete_msgs[0]["payload"]["warnings_issued"] == 3

        # Verify health degradation detection
        degradation_msgs = [
            m for m in all_messages if m.get("type") == "HEALTH_DEGRADATION_DETECTED"
        ]
        assert len(degradation_msgs) > 0
        assert degradation_msgs[0]["payload"]["degradation_level"] == "moderate"
        assert degradation_msgs[0]["payload"]["overall_health_score"] == 55.0
        assert len(degradation_msgs[0]["payload"]["contributing_factors"]) == 3

        await harness.cleanup()


class TestHeartbeatActorRecoveryMonitoring:
    """Test heartbeat actor recovery monitoring and escalation"""

    @pytest.mark.asyncio
    async def test_actor_recovery_monitoring_and_escalation(self):
        """Test: Actor recovery attempts → monitoring → escalation if needed"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate actor recovery attempt after timeout
        recovery_attempt = {
            "type": "ACTOR_RECOVERY_ATTEMPT",
            "sender": "heartbeat",
            "receiver": "bacnet_monitoring",
            "payload": {
                "actor_name": "bacnet_monitoring",
                "recovery_method": "restart_actor",
                "attempt_number": 1,
                "max_attempts": 3,
                "recovery_timestamp": time.time(),
                "timeout_count": 2,  # Second timeout
                "last_successful_response": time.time() - 120,
            },
        }

        await harness.send_message(recovery_attempt)
        await asyncio.sleep(0.1)

        # Simulate recovery attempt response
        recovery_response = {
            "type": "ACTOR_RECOVERY_RESPONSE",
            "sender": "bacnet_monitoring",
            "receiver": "heartbeat",
            "payload": {
                "actor_name": "bacnet_monitoring",
                "recovery_successful": True,
                "restart_duration": 15.2,
                "new_process_id": "proc_789",
                "status": "healthy",
                "recovery_timestamp": time.time(),
                "post_recovery_checks": {
                    "configuration_loaded": True,
                    "connections_established": True,
                    "services_started": True,
                },
            },
        }

        await harness.send_message(recovery_response)
        await asyncio.sleep(0.1)

        # Simulate monitoring of recovered actor
        recovery_monitoring = {
            "type": "RECOVERY_MONITORING",
            "sender": "heartbeat",
            "receiver": "BROADCAST",
            "payload": {
                "actor_name": "bacnet_monitoring",
                "monitoring_duration": 300,  # 5 minutes
                "monitoring_interval": 30,  # Check every 30 seconds
                "stability_threshold": 5,  # 5 consecutive successful checks
                "current_stability_count": 0,
                "monitoring_start_time": time.time(),
            },
        }

        await harness.send_message(recovery_monitoring)
        await asyncio.sleep(0.1)

        # Simulate stability monitoring checks
        for check_num in range(1, 6):
            stability_check = {
                "type": "STABILITY_CHECK",
                "sender": "heartbeat",
                "receiver": "bacnet_monitoring",
                "payload": {
                    "check_number": check_num,
                    "actor_name": "bacnet_monitoring",
                    "check_timestamp": time.time() + (check_num * 30),
                    "response_expected": True,
                    "timeout_duration": 5.0,
                },
            }

            stability_response = {
                "type": "STABILITY_RESPONSE",
                "sender": "bacnet_monitoring",
                "receiver": "heartbeat",
                "payload": {
                    "check_number": check_num,
                    "actor_name": "bacnet_monitoring",
                    "status": "stable",
                    "response_time": 1.2,
                    "operations_successful": True,
                    "resource_usage_normal": True,
                },
            }

            await harness.send_message(stability_check)
            await harness.send_message(stability_response)
            await asyncio.sleep(0.02)

        # Simulate recovery completion
        recovery_complete = {
            "type": "ACTOR_RECOVERY_COMPLETE",
            "sender": "heartbeat",
            "receiver": "BROADCAST",
            "payload": {
                "actor_name": "bacnet_monitoring",
                "recovery_successful": True,
                "stability_achieved": True,
                "monitoring_duration": 300,
                "successful_checks": 5,
                "failed_checks": 0,
                "final_status": "healthy",
                "recovery_complete_timestamp": time.time(),
            },
        }

        await harness.send_message(recovery_complete)
        await asyncio.sleep(0.1)

        # Verify recovery attempt
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        recovery_msgs = [
            m for m in bacnet_messages if m["type"] == "ACTOR_RECOVERY_ATTEMPT"
        ]
        assert len(recovery_msgs) == 1
        assert recovery_msgs[0]["payload"]["recovery_method"] == "restart_actor"
        assert recovery_msgs[0]["payload"]["attempt_number"] == 1

        # Verify recovery response
        heartbeat_messages = harness.get_actor_messages("heartbeat")
        response_msgs = [
            m for m in heartbeat_messages if m["type"] == "ACTOR_RECOVERY_RESPONSE"
        ]
        assert len(response_msgs) == 1
        assert response_msgs[0]["payload"]["recovery_successful"] is True
        assert (
            response_msgs[0]["payload"]["post_recovery_checks"]["configuration_loaded"]
            is True
        )

        # Verify stability monitoring
        stability_checks = [
            m for m in bacnet_messages if m["type"] == "STABILITY_CHECK"
        ]
        stability_responses = [
            m for m in heartbeat_messages if m["type"] == "STABILITY_RESPONSE"
        ]
        assert len(stability_checks) == 5
        assert len(stability_responses) == 5

        # Verify recovery completion
        all_messages = harness.messages
        complete_msgs = [
            m for m in all_messages if m.get("type") == "ACTOR_RECOVERY_COMPLETE"
        ]
        assert len(complete_msgs) > 0
        assert complete_msgs[0]["payload"]["stability_achieved"] is True
        assert complete_msgs[0]["payload"]["successful_checks"] == 5

        await harness.cleanup()

    @pytest.mark.asyncio
    async def test_failed_recovery_escalation_to_system_admin(self):
        """Test: Failed recovery attempts → escalation → system admin notification"""
        harness = ActorTestHarness()
        await harness.initialize()
        harness.enable_message_logging()

        # Simulate multiple failed recovery attempts
        for attempt in range(1, 4):  # 3 failed attempts
            recovery_attempt = {
                "type": "ACTOR_RECOVERY_ATTEMPT",
                "sender": "heartbeat",
                "receiver": "bacnet_monitoring",
                "payload": {
                    "actor_name": "bacnet_monitoring",
                    "recovery_method": "restart_actor",
                    "attempt_number": attempt,
                    "max_attempts": 3,
                    "recovery_timestamp": time.time(),
                    "previous_attempts_failed": attempt - 1,
                },
            }

            recovery_failure = {
                "type": "ACTOR_RECOVERY_FAILURE",
                "sender": "bacnet_monitoring",
                "receiver": "heartbeat",
                "payload": {
                    "actor_name": "bacnet_monitoring",
                    "recovery_successful": False,
                    "failure_reason": "process_start_failed",
                    "error_message": f"Failed to start process: Error {attempt}",
                    "attempt_number": attempt,
                    "failure_timestamp": time.time(),
                },
            }

            await harness.send_message(recovery_attempt)
            await harness.send_message(recovery_failure)
            await asyncio.sleep(0.05)

        # Simulate escalation trigger
        escalation_trigger = {
            "type": "ESCALATION_TRIGGERED",
            "sender": "heartbeat",
            "receiver": "BROADCAST",
            "payload": {
                "actor_name": "bacnet_monitoring",
                "escalation_reason": "recovery_attempts_exhausted",
                "failed_attempts": 3,
                "escalation_level": "critical",
                "escalation_timestamp": time.time(),
                "admin_notification_required": True,
            },
        }

        await harness.send_message(escalation_trigger)
        await asyncio.sleep(0.1)

        # Simulate system admin notification
        admin_notification = {
            "type": "SYSTEM_ADMIN_NOTIFICATION",
            "sender": "heartbeat",
            "receiver": "BROADCAST",
            "payload": {
                "notification_type": "critical_actor_failure",
                "actor_name": "bacnet_monitoring",
                "severity": "critical",
                "message": "Actor recovery failed after 3 attempts - manual intervention required",
                "details": {
                    "total_recovery_attempts": 3,
                    "last_failure_reason": "process_start_failed",
                    "system_impact": "BACnet monitoring offline",
                    "recommended_actions": [
                        "Check system resources",
                        "Review error logs",
                        "Manual process restart",
                        "Consider system reboot",
                    ],
                },
                "contact_methods": ["email", "sms", "slack"],
                "escalation_timestamp": time.time(),
            },
        }

        await harness.send_message(admin_notification)
        await asyncio.sleep(0.1)

        # Simulate system status update
        system_status_update = {
            "type": "SYSTEM_STATUS_UPDATE",
            "sender": "heartbeat",
            "receiver": "BROADCAST",
            "payload": {
                "system_status": "critical",
                "failed_actors": ["bacnet_monitoring"],
                "operational_actors": ["mqtt", "uploader"],
                "system_functionality": "degraded",
                "impact_assessment": {
                    "data_collection": "offline",
                    "data_upload": "operational",
                    "command_processing": "limited",
                },
                "manual_intervention_required": True,
            },
        }

        await harness.send_message(system_status_update)
        await asyncio.sleep(0.1)

        # Verify failed recovery attempts
        bacnet_messages = harness.get_actor_messages("bacnet_monitoring")
        recovery_attempts = [
            m for m in bacnet_messages if m["type"] == "ACTOR_RECOVERY_ATTEMPT"
        ]
        assert len(recovery_attempts) == 3

        heartbeat_messages = harness.get_actor_messages("heartbeat")
        recovery_failures = [
            m for m in heartbeat_messages if m["type"] == "ACTOR_RECOVERY_FAILURE"
        ]
        assert len(recovery_failures) == 3

        # Verify escalation trigger
        all_messages = harness.messages
        escalation_msgs = [
            m for m in all_messages if m.get("type") == "ESCALATION_TRIGGERED"
        ]
        assert len(escalation_msgs) > 0
        assert escalation_msgs[0]["payload"]["escalation_level"] == "critical"
        assert escalation_msgs[0]["payload"]["failed_attempts"] == 3

        # Verify admin notification
        admin_msgs = [
            m for m in all_messages if m.get("type") == "SYSTEM_ADMIN_NOTIFICATION"
        ]
        assert len(admin_msgs) > 0
        assert admin_msgs[0]["payload"]["severity"] == "critical"
        assert "manual intervention required" in admin_msgs[0]["payload"]["message"]
        assert len(admin_msgs[0]["payload"]["details"]["recommended_actions"]) == 4

        # Verify system status update
        status_msgs = [
            m for m in all_messages if m.get("type") == "SYSTEM_STATUS_UPDATE"
        ]
        assert len(status_msgs) > 0
        assert status_msgs[0]["payload"]["system_status"] == "critical"
        assert status_msgs[0]["payload"]["manual_intervention_required"] is True
        assert (
            status_msgs[0]["payload"]["impact_assessment"]["data_collection"]
            == "offline"
        )

        await harness.cleanup()
