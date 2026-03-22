from typing import Callable
from .mqtt_client import MQTTClient

TOPIC_HALL  = "hall"
TOPIC_GLOVE = "glove"
TOPIC_ORDER = "order"

TOPICS = [TOPIC_HALL, TOPIC_GLOVE, TOPIC_ORDER]

OnEventCallback = Callable[[int | None, int | None, int | None], None]

class MQTTBridge:
    def __init__(self, host: str, port: int = 1883):
        self._client = MQTTClient(host, port, client_id="bridge")
        self.on_event: OnEventCallback | None = None

    def connect(self):
        self._client.connect()
        for topic in TOPICS:
            self._client.subscribe(topic, callback=self._make_handler(topic))

    def disconnect(self):
        self._client.disconnect()

    def publish(self, topic: str, payload: bytes):
        self._client.publish(topic, payload)

    def _make_handler(self, topic: str):
        def handler(_topic: str, payload: bytes):
            try:
                value = int(payload[0])
                print(f'Received id: {value} from topic: {topic}')
            except (IndexError, ValueError) as e:
                print(f"[MQTTBridge] Bad message on {topic}: {e}")
                return

            if topic == TOPIC_HALL:
                hall, glove, order = value, None, None
            elif topic == TOPIC_GLOVE:
                hall, glove, order = None, value, None
            elif topic == TOPIC_ORDER:
                hall, glove, order = None, None, value

            self.on_event(hall, glove, order)

        return handler
