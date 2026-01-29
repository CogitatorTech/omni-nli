import logging
from collections import deque
from dataclasses import dataclass
from uuid import uuid4

from mcp.server.streamable_http import EventCallback, EventId, EventMessage, EventStore, StreamId
from mcp.types import JSONRPCMessage

logger = logging.getLogger(__name__)


@dataclass
class EventEntry:
    event_id: EventId
    stream_id: StreamId
    message: JSONRPCMessage


class InMemoryEventStore(EventStore):
    def __init__(self, max_events_per_stream: int = 200, max_streams: int = 1000) -> None:
        self.max_events_per_stream = max_events_per_stream
        self.max_streams = max_streams
        self.streams: dict[StreamId, deque[EventEntry]] = {}
        self.event_index: dict[EventId, EventEntry] = {}
        self._stream_order: deque[StreamId] = deque()  # Track stream creation order for LRU

    async def store_event(self, stream_id: StreamId, message: JSONRPCMessage) -> EventId:
        event_id = str(uuid4())
        event_entry = EventEntry(event_id=event_id, stream_id=stream_id, message=message)

        is_new_stream = stream_id not in self.streams
        if is_new_stream:
            # Evict the oldest stream if we've reached the limit
            while len(self.streams) >= self.max_streams and self._stream_order:
                oldest_stream_id = self._stream_order.popleft()
                if oldest_stream_id in self.streams:
                    # Remove all events from this stream from the index
                    for event in self.streams[oldest_stream_id]:
                        self.event_index.pop(event.event_id, None)
                    del self.streams[oldest_stream_id]

            self.streams[stream_id] = deque(maxlen=self.max_events_per_stream)
            self._stream_order.append(stream_id)

        if len(self.streams[stream_id]) == self.max_events_per_stream:
            oldest_event = self.streams[stream_id][0]
            self.event_index.pop(oldest_event.event_id, None)

        self.streams[stream_id].append(event_entry)
        self.event_index[event_id] = event_entry

        return event_id

    async def replay_events_after(
        self,
        last_event_id: EventId,
        send_callback: EventCallback,
    ) -> StreamId | None:
        if last_event_id not in self.event_index:
            logger.warning(f"Event ID {last_event_id} not found in store")
            return None

        last_event = self.event_index[last_event_id]
        stream_id = last_event.stream_id
        stream_events = self.streams.get(last_event.stream_id, deque())

        found_last = False
        for event in stream_events:
            if found_last:
                await send_callback(EventMessage(event.message, event.event_id))
            elif event.event_id == last_event_id:
                found_last = True

        return stream_id
