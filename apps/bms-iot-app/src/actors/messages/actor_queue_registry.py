import asyncio
from typing import Dict, List
import logging

from src.actors.messages.message_type import (
    ActorName,
    ActorMessage,
    ActorMessageType,
    AllowedPayloadTypes,
)

logger = logging.getLogger(__name__)


# --- Registry supporting one-to-one and broadcast messaging ---
class ActorQueueRegistry:
    def __init__(self) -> None:
        self.queues: Dict[ActorName, asyncio.Queue] = {}

    def register(self, name: ActorName):
        if name in self.queues:
            raise ValueError(f"Actor {name} already registered.")
        self.queues[name] = asyncio.Queue()
        logger.info(f"[Registry] Registered actor: {name}")

    def get_queue(self, name: ActorName) -> asyncio.Queue:
        if name not in self.queues:
            raise KeyError(f"No queue registered for actor {name}")
        return self.queues[name]

    async def send_from(
        self,
        sender: ActorName,
        receiver: ActorName,
        type: ActorMessageType,
        payload: AllowedPayloadTypes,
    ):
        msg = ActorMessage(
            sender=sender, receiver=receiver, message_type=type, payload=payload
        )
        await self.send(msg)

    async def broadcast_from(
        self,
        sender: ActorName,
        type: ActorMessageType,
        payload: AllowedPayloadTypes,
        exclude: List[ActorName] = [],
    ):
        base_msg = ActorMessage(
            sender=sender,
            receiver=ActorName.MQTT,  # gets overwritten per actor
            message_type=type,
            payload=payload,
        )
        await self.broadcast(base_msg, exclude=exclude)

    async def send(self, message: ActorMessage):
        if message.receiver not in self.queues:
            raise ValueError(f"Receiver {message.receiver} not found in registry")
        await self.queues[message.receiver].put(message)
        logger.info(f"[Registry] Sent message to {message.receiver}")

    async def broadcast(self, message: ActorMessage, exclude: List[ActorName] = []):
        for actor_name, queue in self.queues.items():
            if actor_name == message.sender or actor_name in exclude:
                continue
            await queue.put(message.model_copy(update={"receiver": actor_name}))
            logger.info(
                f"[Registry] Broadcast message to {actor_name}: {message.message_type}"
            )
