"""
JARVIS server — Event Bus

In-process async event bus for decoupled communication between services.
No external message broker needed.
"""

import asyncio
from typing import Callable, Dict, List, Any, Coroutine
from dataclasses import dataclass, field
from datetime import datetime

import structlog

logger = structlog.get_logger("jarvis.events")


@dataclass
class JarvisEvent:
    """An event in the JARVIS system."""
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"
    message_id: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# Type alias for event handler
EventHandler = Callable[[JarvisEvent], Coroutine[Any, Any, None]]


class EventBus:
    """Async in-process event bus using asyncio.Queue.
    
    Publishers fire events without knowing subscribers.
    Subscribers register handlers for specific event types.
    """

    def __init__(self, max_queue_size: int = 1000):
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._queue: asyncio.Queue[JarvisEvent] = asyncio.Queue(maxsize=max_queue_size)
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the event processing loop."""
        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.info("eventbus.started")

    async def stop(self) -> None:
        """Stop the event processing loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("eventbus.stopped")

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to an event type.
        
        Use "*" to subscribe to all events.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug("eventbus.subscribed", event_type=event_type)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]

    async def publish(self, event: JarvisEvent) -> None:
        """Publish an event to the bus."""
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("eventbus.queue_full", event_type=event.type)

    async def _process_loop(self) -> None:
        """Process events from the queue and dispatch to subscribers."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            # Get handlers for this event type + wildcard handlers
            handlers = list(self._subscribers.get(event.type, []))
            handlers.extend(self._subscribers.get("*", []))

            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(
                        "eventbus.handler_error",
                        event_type=event.type,
                        handler=handler.__qualname__,
                        error=str(e),
                    )
