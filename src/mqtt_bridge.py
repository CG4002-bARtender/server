import queue
import threading
from typing import Callable
from .mqtt_client import MQTTClient
from config import TOPIC_HALL, TOPIC_GLOVE, TOPIC_ORDER, TOPICS, POLL_TIMEOUT

from src.game_engine import GameState

OnEventCallback = Callable[[int | None, int | None, int | None], None]



class MQTTBridge:
    def __init__(self, host: str, port: int = 8883,
             ca_cert: str = None, client_cert: str = None, client_key: str = None):
        self._client = MQTTClient(host, port, client_id="bridge",
                               ca_cert=ca_cert,
                               client_cert=client_cert,
                               client_key=client_key)
        self.on_event: OnEventCallback | None = None
        self._get_state: Callable[[], GameState] | None = None

        self._hall_value: int | None = None
        self._hall_lock = threading.Lock()
        self._hall_updated = threading.Event()  # set only in HOVER, for highlight priority

        self._glove_queue: queue.Queue = queue.Queue()  # populated only when state != IDLE
        self._order_queue: queue.Queue = queue.Queue()  # populated only when state == IDLE

        self._worker = threading.Thread(target=self._process_events, daemon=True)

    def connect(self):
        self._worker.start()
        self._client.connect()
        for topic in TOPICS:
            self._client.subscribe(topic, callback=self._make_handler(topic))

    def publish(self, topic: str, payload: bytes):
        self._client.publish(topic, payload)

    def _process_events(self):
        while True:
            # Priority 1: order (only arrives in IDLE)
            try:
                order = self._order_queue.get_nowait()
                self.on_event(None, None, order)
                continue
            except queue.Empty:
                pass

            # Priority 2: hall highlight update (only arrives in HOVER)
            if self._hall_updated.is_set():
                self._hall_updated.clear()
                with self._hall_lock:
                    hall = self._hall_value
                self.on_event(hall, None, None)
                continue  # re-check hall before consuming any gesture

            # Priority 3: gesture  (arrives in all other states)
            try:
                glove = self._glove_queue.get(timeout=POLL_TIMEOUT)
            except queue.Empty:
                glove = None
            self.on_event(None, glove, None)

    def _make_handler(self, topic: str):
        def handler(_topic, payload):
            if not payload:
                return
            value = int(payload[0])
            print(f'Received id: {value} from topic: {topic}')

            state = self._get_state()

            if topic == TOPIC_HALL:
                with self._hall_lock:
                    changed = value != self._hall_value
                    self._hall_value = value
                if state == GameState.HOVER and changed:
                    self._hall_updated.set()

            elif topic == TOPIC_GLOVE and state != GameState.IDLE:
                    self._glove_queue.put(value)

            elif topic == TOPIC_ORDER and state == GameState.IDLE:
                    self._order_queue.put(value)

        return handler
