import json
import queue
import threading
from typing import Callable
from .mqtt_client import MQTTClient
from config import TOPIC_HALL, TOPIC_GLOVE, TOPIC_ORDER, TOPICS

OnEventCallback = Callable[[int | None, int | None, int | None], None]

class MQTTBridge:
    def __init__(self, host: str, port: int = 1883):
        self._client = MQTTClient(host, port, client_id="bridge")
        self.on_event: OnEventCallback | None = None
        self._queue: queue.Queue = queue.Queue()
        self._worker = threading.Thread(target=self._process_events, daemon=True)

    def connect(self):
        self._worker.start()
        self._client.connect()
        for topic in TOPICS:
            self._client.subscribe(topic, callback=self._make_handler(topic))

    def disconnect(self):
        self._queue.put(None)  # sentinel to stop worker
        self._worker.join()
        self._client.disconnect()

    def publish(self, topic: str, payload: bytes):
        self._client.publish(topic, payload)

    def _process_events(self):
        while True:
            item = self._queue.get()
            if item is None:
                break
            hall, glove, order = item
            if self.on_event:
                self.on_event(hall, glove, order)

    def _make_handler(self, topic: str):
        def handler(_topic: str, payload: str | bytes):
            try:
                if topic in (TOPIC_GLOVE, TOPIC_HALL):
                    value = int(payload[0])
                else:
                    data = json.loads(payload)
                    value = int(data["id"])
                print(f'Received id: {value} from topic: {topic}')
            except (json.JSONDecodeError, KeyError, ValueError, IndexError) as e:
                print(f"[MQTTBridge] Bad message on {topic}: {e}")
                return

            if topic == TOPIC_HALL:
                self._queue.put((value, None, None))
            elif topic == TOPIC_GLOVE:
                self._queue.put((None, value, None))
            elif topic == TOPIC_ORDER:
                self._queue.put((None, None, value))

        return handler
