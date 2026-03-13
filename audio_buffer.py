"""
AudioBuffer — accumulates raw PCM chunks from the bar ESP32 and emits a
complete clip once the stream goes idle for AUDIO_IDLE_TIMEOUT seconds.

Thread-safe: chunks arrive on the MQTT thread; the main loop polls ready().
"""

import threading
import time
from config import AUDIO_IDLE_TIMEOUT


class AudioBuffer:
    def __init__(self, idle_timeout: float = AUDIO_IDLE_TIMEOUT):
        self._lock        = threading.Lock()
        self._chunks: list[bytes] = []
        self._last_chunk  = 0.0
        self._idle_timeout = idle_timeout

    def push(self, data: bytes) -> None:
        with self._lock:
            self._chunks.append(data)
            self._last_chunk = time.monotonic()

    def ready(self) -> bool:
        """True when at least one chunk has arrived and the stream has gone idle."""
        with self._lock:
            return (
                len(self._chunks) > 0
                and (time.monotonic() - self._last_chunk) >= self._idle_timeout
            )

    def consume(self) -> bytes:
        """Return the complete PCM clip and reset the buffer."""
        with self._lock:
            clip = b"".join(self._chunks)
            self._chunks.clear()
            self._last_chunk = 0.0
        return clip

    def total_bytes(self) -> int:
        with self._lock:
            return sum(len(c) for c in self._chunks)
