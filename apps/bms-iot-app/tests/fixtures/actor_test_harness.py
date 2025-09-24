"""
ActorTestHarness utility for testing actor interactions.

This module provides utilities for setting up and testing actor-based systems
with proper message flow validation and actor lifecycle management.
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from unittest.mock import Mock, AsyncMock
from dataclasses import dataclass, field
from datetime import datetime
import time


@dataclass
class MessageLog:
    """Log entry for actor messages"""

    timestamp: datetime
    sender: str
    receiver: str
    message_type: str
    payload: Dict[str, Any]
    message_id: str = field(default_factory=lambda: str(id(object())))


class ActorTestHarness:
    """
    Test harness for actor integration testing.

    User Story: As a developer, I want to test actor interactions without
    setting up the full Pykka system during unit tests.
    """

    def __init__(self):
        self.actors: Dict[str, Mock] = {}
        self.messages: List[Dict[str, Any]] = []  # All messages
        self.message_log: List[MessageLog] = []
        self.message_handlers: Dict[str, List[Callable]] = {}
        self._running = False
        self._initialized = False
        self._cleaned_up = False
        self._message_logging_enabled = False
        self._actor_messages: Dict[str, List[Dict[str, Any]]] = {}
        self._start_time = time.time()
        self._message_queue_limits: Dict[str, int] = {}
        self._routing_rules: Dict[str, str] = {}
        self._subscriptions: Dict[str, List[str]] = {}

        # Mock external components
        self.mqtt_client = AsyncMock()
        self.bacnet_wrapper = AsyncMock()
        self.rest_client = AsyncMock()

        # Setup mock returns
        self.mqtt_client.is_connected = True
        self.mqtt_client.published_messages = []
        self.mqtt_client.subscriptions = []

        self.bacnet_wrapper.is_connected = True
        self.bacnet_wrapper.device_id = "test_device_123"
        self.bacnet_wrapper.read_points = AsyncMock(return_value={"temp1": 25.0})

        self.rest_client.uploaded_data = []

    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the actor system with all required actors.

        Args:
            config: Optional configuration for actors
        """
        # Default actors to create
        default_actors = ["mqtt", "bacnet_monitoring", "uploader", "heartbeat"]

        # Create actors
        for actor_name in default_actors:
            await self._create_actor(actor_name, config)

        self._initialized = True
        self._running = True
        self._cleaned_up = False

    async def _create_actor(
        self, name: str, config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a mock actor with given name and config"""
        actor = AsyncMock()
        actor.name = name
        actor.tell = AsyncMock(side_effect=self._create_tell_handler(name))
        actor.ask = AsyncMock()
        actor.received_messages = []
        actor.sent_messages = []
        actor.config = config.get(name, {}) if config else {}
        actor.status = "healthy"

        # Special handling for MQTT actor
        if name == "mqtt":
            actor.client = self.mqtt_client
        elif name == "bacnet_monitoring":
            actor.wrapper = self.bacnet_wrapper
        elif name == "uploader":
            actor.client = self.rest_client

        self.actors[name] = actor
        self.message_handlers[name] = []
        self._actor_messages[name] = []

    def _create_tell_handler(self, actor_name: str):
        """Create a tell message handler for an actor"""

        async def tell_handler(message):
            # Log the message
            log_entry = MessageLog(
                timestamp=datetime.now(),
                sender=message.get("sender", "unknown"),
                receiver=actor_name,
                message_type=message.get(
                    "message_type", message.get("type", "unknown")
                ),
                payload=message.get("payload", {}),
            )
            self.message_log.append(log_entry)

            # Add to actor's received messages
            if actor_name in self.actors:
                self.actors[actor_name].received_messages.append(message)
                self._actor_messages[actor_name].append(message)

            # Add to global messages if logging enabled
            if self._message_logging_enabled:
                self.messages.append(message)

            # Handle broadcast messages
            if message.get("receiver") == "BROADCAST":
                for other_actor in self.actors:
                    if other_actor != actor_name:
                        self._actor_messages[other_actor].append(message)

            # Call registered message handlers
            for handler in self.message_handlers.get(actor_name, []):
                await handler(message)

            return True

        return tell_handler

    async def cleanup(self) -> None:
        """Cleanup the actor system"""
        for actor_name in list(self.actors.keys()):
            # Clean up each actor
            if hasattr(self.actors[actor_name], "cleanup"):
                await self.actors[actor_name].cleanup()

        self.actors.clear()
        self.messages.clear()
        self._actor_messages.clear()
        self.message_handlers.clear()

        self._initialized = False
        self._running = False
        self._cleaned_up = True

    def get_actor(self, name: str) -> Optional[Mock]:
        """Get an actor by name"""
        return self.actors.get(name)

    def list_actors(self) -> List[str]:
        """List all actor names"""
        return list(self.actors.keys())

    def is_initialized(self) -> bool:
        """Check if the harness is initialized"""
        return self._initialized

    def enable_message_logging(self) -> None:
        """Enable message logging"""
        self._message_logging_enabled = True

    def _record_message(self, message: Dict[str, Any]) -> None:
        """Record a message"""
        if self._message_logging_enabled:
            self.messages.append(message)

    async def send_message(
        self, message_or_sender, receiver=None, message_type=None, payload=None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a message through the actor system.

        Supports both new dictionary interface and legacy parameter interface:
        - New: send_message({'type': 'TEST', 'sender': 'A', 'receiver': 'B', 'payload': {}})
        - Legacy: send_message('A', 'B', 'TEST', {})

        Returns:
            Result of sending or None/error (for new interface)
            True/False (for legacy interface)
        """
        # Handle legacy interface (4 parameters)
        if receiver is not None:
            return await self.send_message_legacy(
                message_or_sender, receiver, message_type, payload or {}
            )

        # Handle new interface (message dictionary)
        message = message_or_sender

        # Validate message
        if not message.get("sender") or not message.get("receiver"):
            return {"error": "malformed_message"}

        if message.get("payload") is None:
            return {"error": "invalid_payload"}

        receiver_name = message.get("receiver")

        # Check for invalid recipient
        if receiver_name not in self.actors and receiver_name != "BROADCAST":
            # Send error back to sender
            if message.get("sender") in self.actors:
                error_msg = {
                    "type": "DELIVERY_ERROR",
                    "sender": "system",
                    "receiver": message.get("sender"),
                    "payload": {
                        "original_message_id": message.get("id"),
                        "error": "recipient_not_found",
                    },
                }
                await self.actors[message.get("sender")].tell(error_msg)
            return {"error": "recipient_not_found"}

        # Check queue limits
        if receiver_name in self._message_queue_limits:
            limit = self._message_queue_limits[receiver_name]
            if len(self._actor_messages.get(receiver_name, [])) >= limit:
                return {"status": "queue_full"}

        # Record message
        self._record_message(message)

        # Handle broadcast
        if receiver_name == "BROADCAST":
            for actor_name, actor in self.actors.items():
                if actor_name != message.get("sender"):
                    await actor.tell(message)
                    self._actor_messages[actor_name].append(message)
        else:
            # Send to specific actor
            await self.actors[receiver_name].tell(message)

        return {"status": "sent"}

    async def send_message_with_ack(
        self, message: Dict[str, Any], timeout: float = 1.0
    ) -> Optional[Dict[str, Any]]:
        """Send message and wait for acknowledgment"""
        result = await self.send_message(message)

        if result and result.get("error"):
            return None

        # Simulate acknowledgment
        await asyncio.sleep(0.1)  # Small delay

        if message.get("receiver") in self.actors:
            return {"message_id": message.get("id"), "status": "delivered"}
        else:
            return {"status": "timeout"}

    async def send_message_with_retry(
        self, message: Dict[str, Any], retry_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Send message with retry logic"""
        max_retries = retry_config.get("max_retries", 3)
        retry_delay = retry_config.get("retry_delay", 0.1)

        for attempt in range(1, max_retries + 1):
            result = await self.send_message(message)
            if result and not result.get("error"):
                return {"delivered": True, "attempts": attempt}
            await asyncio.sleep(retry_delay)

        return {"delivered": False, "attempts": max_retries}

    def get_actor_messages(self, actor_name: str) -> List[Dict[str, Any]]:
        """Get all messages received by an actor"""
        return self._actor_messages.get(actor_name, [])

    async def restart_actor(self, actor_name: str) -> None:
        """Restart an actor"""
        if actor_name in self.actors:
            # Save config
            config = (
                self.actors[actor_name].config
                if hasattr(self.actors[actor_name], "config")
                else {}
            )

            # Remove old actor
            del self.actors[actor_name]

            # Create new actor
            await self._create_actor(actor_name, {"actor_name": config})

    def _simulate_actor_failure(self, actor_name: str) -> None:
        """Simulate an actor failure"""
        if actor_name in self.actors:
            self.actors[actor_name].status = "failed"

    def _is_actor_failed(self, actor_name: str) -> bool:
        """Check if an actor is in failed state"""
        if actor_name in self.actors:
            return getattr(self.actors[actor_name], "status", "healthy") == "failed"
        return False

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        return {
            "actor_count": len(self.actors),
            "message_count": len(self.messages),
            "uptime": time.time() - self._start_time,
        }

    def get_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get health status of all actors"""
        health = {}
        for actor_name, actor in self.actors.items():
            health[actor_name] = {
                "status": getattr(actor, "status", "unknown"),
                "messages_received": len(self._actor_messages.get(actor_name, [])),
            }
        return health

    def get_message_throughput(self) -> Dict[str, Any]:
        """Get message throughput metrics"""
        uptime = time.time() - self._start_time
        total_messages = len(self.messages)
        return {
            "total_messages": total_messages,
            "messages_per_second": total_messages / uptime if uptime > 0 else 0,
        }

    def set_message_queue_limit(self, actor_name: str, limit: int) -> None:
        """Set message queue limit for an actor"""
        self._message_queue_limits[actor_name] = limit

    async def send_request(
        self, request: Dict[str, Any], timeout: float = 1.0
    ) -> Optional[Dict[str, Any]]:
        """Send request and wait for response"""
        await self.send_message(request)

        # Simulate response
        await asyncio.sleep(0.1)

        return {
            "request_id": request.get("id"),
            "type": "STATUS_RESPONSE",
            "payload": {"status": "operational"},
        }

    async def subscribe_actor(self, actor_name: str, topic: str) -> None:
        """Subscribe an actor to a topic"""
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
        if actor_name not in self._subscriptions[topic]:
            self._subscriptions[topic].append(actor_name)

    async def publish_to_topic(self, publication: Dict[str, Any]) -> None:
        """Publish message to a topic"""
        topic = publication.get("topic")
        if topic in self._subscriptions:
            for subscriber in self._subscriptions[topic]:
                msg = {
                    "topic": topic,
                    "type": "TOPIC_MESSAGE",
                    "sender": publication.get("publisher"),
                    "receiver": subscriber,
                    "payload": publication.get("payload"),
                }
                await self.send_message(msg)

    async def route_chain_message(self, message: Dict[str, Any]) -> None:
        """Route message through a chain of actors"""
        chain = message.get("chain", [])
        current_index = message.get("current_index", 0)

        if current_index < len(chain):
            current_actor = chain[current_index]
            message["current_index"] = current_index + 1
            message["sender"] = (
                chain[current_index - 1] if current_index > 0 else "system"
            )
            message["receiver"] = current_actor

            await self.send_message(message)

            # Continue chain
            if current_index + 1 < len(chain):
                await asyncio.sleep(0.05)
                await self.route_chain_message(message)

    def set_routing_rules(self, rules: Dict[str, str]) -> None:
        """Set routing rules for conditional routing"""
        self._routing_rules = rules

    async def route_by_type(self, message: Dict[str, Any]) -> None:
        """Route message based on type using routing rules"""
        msg_type = message.get("type")
        if msg_type in self._routing_rules:
            target = self._routing_rules[msg_type]
            message["sender"] = "router"
            message["receiver"] = target
            await self.send_message(message)

    # Legacy compatibility methods
    async def setup_actors(self, actor_names: List[str]) -> None:
        """
        Setup mock actors for testing (legacy method).

        Args:
            actor_names: List of actor names to create
        """
        for name in actor_names:
            await self._create_actor(name, None)

        self._running = True

    async def send_message_legacy(
        self, sender: str, receiver: str, message_type: str, payload: Dict[str, Any]
    ) -> bool:
        """
        Send a message between actors (legacy interface).

        Args:
            sender: Sender actor name
            receiver: Receiver actor name
            message_type: Type of message
            payload: Message payload

        Returns:
            True if message was sent successfully
        """
        if not self._running:
            raise RuntimeError("ActorTestHarness not running. Call setup_actors first.")

        message = {
            "sender": sender,
            "receiver": receiver,
            "message_type": message_type,
            "payload": payload,
        }

        # Record message (only if not already logged by tell_handler)
        # tell_handler will log this, so we don't need to duplicate here

        # Send to receiver
        if receiver in self.actors:
            await self.actors[receiver].tell(message)
            self.actors[receiver].received_messages.append(message)

            # Add to sender's sent messages
            if sender in self.actors:
                self.actors[sender].sent_messages.append(message)

            return True

        return False

    async def get_actor_messages_legacy(self, actor_name: str) -> List[Dict[str, Any]]:
        """
        Get all messages received by an actor (legacy interface).

        Args:
            actor_name: Name of the actor

        Returns:
            List of messages received by the actor
        """
        if actor_name in self.actors:
            return self.actors[actor_name].received_messages
        return []

    def register_message_handler(self, actor_name: str, handler: Callable) -> None:
        """
        Register a message handler for an actor.

        Args:
            actor_name: Name of the actor
            handler: Async function to handle messages
        """
        if actor_name not in self.message_handlers:
            self.message_handlers[actor_name] = []
        self.message_handlers[actor_name].append(handler)

    def get_message_log(self) -> List[MessageLog]:
        """
        Get the complete message log.

        Returns:
            List of all message log entries
        """
        return self.message_log

    def clear_message_log(self) -> None:
        """Clear the message log"""
        self.message_log.clear()
        self.messages.clear()
        # Reinitialize actor messages instead of clearing completely
        for actor_name in self.actors:
            self._actor_messages[actor_name] = []
        for actor in self.actors.values():
            actor.received_messages.clear()
            if hasattr(actor, "sent_messages"):
                actor.sent_messages.clear()

    async def wait_for_message(
        self, actor_name: str, message_type: str, timeout: float = 1.0
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for a specific message type to arrive at an actor.

        Args:
            actor_name: Name of the actor to wait for message
            message_type: Type of message to wait for
            timeout: Timeout in seconds

        Returns:
            The message if received, None if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            messages = self.get_actor_messages(actor_name)
            for message in reversed(messages):  # Check newest first
                if (
                    message.get("type") == message_type
                    or message.get("message_type") == message_type
                ):
                    return message

            await asyncio.sleep(0.05)  # Small delay before checking again

        return None  # Timeout

    def get_received_messages(self, actor_name: str) -> List[Dict[str, Any]]:
        """Legacy method - use get_actor_messages instead"""
        return self.get_actor_messages(actor_name)

    def get_messages_between(self, sender: str, receiver: str) -> List[Any]:
        """Get messages between two actors (legacy interface)"""
        messages = []
        for log_entry in self.message_log:
            if log_entry.sender == sender and log_entry.receiver == receiver:
                messages.append(log_entry)
        return messages
