"""Tests for the InMemoryEventStore."""

import pytest
from mcp.types import JSONRPCMessage, JSONRPCRequest

from omni_nli.event_store import InMemoryEventStore, EventEntry


def _make_message(method: str = "test") -> JSONRPCMessage:
    """Create a test JSONRPC message."""
    return JSONRPCMessage(JSONRPCRequest(jsonrpc="2.0", id=1, method=method))


class TestInMemoryEventStore:
    """Tests for InMemoryEventStore."""

    @pytest.fixture
    def store(self) -> InMemoryEventStore:
        return InMemoryEventStore(max_events_per_stream=3, max_streams=2)

    async def test_store_event_creates_stream(self, store: InMemoryEventStore):
        """Storing an event should create a new stream."""
        event_id = await store.store_event("stream-1", _make_message())

        assert event_id is not None
        assert "stream-1" in store.streams
        assert len(store.streams["stream-1"]) == 1
        assert event_id in store.event_index

    async def test_store_multiple_events_same_stream(self, store: InMemoryEventStore):
        """Multiple events should be stored in the same stream."""
        event_id_1 = await store.store_event("stream-1", _make_message("method1"))
        event_id_2 = await store.store_event("stream-1", _make_message("method2"))

        assert len(store.streams["stream-1"]) == 2
        assert event_id_1 in store.event_index
        assert event_id_2 in store.event_index

    async def test_event_eviction_when_stream_full(self, store: InMemoryEventStore):
        """Oldest event should be evicted when stream reaches max_events_per_stream."""
        # Store 3 events (max_events_per_stream=3)
        event_id_1 = await store.store_event("stream-1", _make_message("method1"))
        await store.store_event("stream-1", _make_message("method2"))
        await store.store_event("stream-1", _make_message("method3"))

        # First event should still be in index
        assert event_id_1 in store.event_index
        assert len(store.streams["stream-1"]) == 3

        # Store 4th event, should evict the oldest
        await store.store_event("stream-1", _make_message("method4"))

        # First event should be evicted
        assert event_id_1 not in store.event_index
        assert len(store.streams["stream-1"]) == 3

    async def test_stream_eviction_when_max_streams_reached(self, store: InMemoryEventStore):
        """Oldest stream should be evicted when max_streams is reached."""
        # Store events in 2 streams (max_streams=2)
        event_id_stream1 = await store.store_event("stream-1", _make_message())
        await store.store_event("stream-2", _make_message())

        assert "stream-1" in store.streams
        assert "stream-2" in store.streams

        # Store event in 3rd stream, should evict oldest (stream-1)
        await store.store_event("stream-3", _make_message())

        assert "stream-1" not in store.streams
        assert event_id_stream1 not in store.event_index
        assert "stream-2" in store.streams
        assert "stream-3" in store.streams

    async def test_replay_events_after_returns_none_for_unknown_event(
        self, store: InMemoryEventStore
    ):
        """replay_events_after should return None for unknown event ID."""
        collected_events = []

        async def callback(event):
            collected_events.append(event)

        result = await store.replay_events_after("unknown-event-id", callback)

        assert result is None
        assert len(collected_events) == 0

    async def test_replay_events_after_replays_subsequent_events(
        self, store: InMemoryEventStore
    ):
        """replay_events_after should replay events after the specified event."""
        event_id_1 = await store.store_event("stream-1", _make_message("method1"))
        await store.store_event("stream-1", _make_message("method2"))
        await store.store_event("stream-1", _make_message("method3"))

        collected_events = []

        async def callback(event):
            collected_events.append(event)

        result = await store.replay_events_after(event_id_1, callback)

        assert result == "stream-1"
        assert len(collected_events) == 2  # method2 and method3

    async def test_replay_events_after_last_event_returns_empty(
        self, store: InMemoryEventStore
    ):
        """replay_events_after on the last event should return no events."""
        await store.store_event("stream-1", _make_message("method1"))
        event_id_last = await store.store_event("stream-1", _make_message("method2"))

        collected_events = []

        async def callback(event):
            collected_events.append(event)

        result = await store.replay_events_after(event_id_last, callback)

        assert result == "stream-1"
        assert len(collected_events) == 0

    async def test_stream_order_tracking(self, store: InMemoryEventStore):
        """Stream order should be tracked correctly for LRU eviction."""
        await store.store_event("stream-1", _make_message())
        await store.store_event("stream-2", _make_message())

        assert list(store._stream_order) == ["stream-1", "stream-2"]

    async def test_event_entry_dataclass(self):
        """EventEntry dataclass should work correctly."""
        entry = EventEntry(
            event_id="test-id",
            stream_id="test-stream",
            message=_make_message(),
        )

        assert entry.event_id == "test-id"
        assert entry.stream_id == "test-stream"
        assert entry.message is not None
