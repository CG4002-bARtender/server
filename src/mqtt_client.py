import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, host: str, port: int = 1883, client_id: str = ""):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
        self.host = host
        self.port = port

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def _on_connect(self, _client, _userdata, _connect_flags, _reason_code, _properties):
        print(f"Connected to {self.host}:{self.port}")

    def _on_disconnect(self, _client, _userdata, _disconnect_flags, _reason_code, _properties):
        print(f"Disconnected")

    def _on_message(self, _client, _userdata, message):
        print(f"[{message.topic}] {message.payload.decode()}")

    def connect(self):
        self.client.connect(self.host, self.port)
        self.client.loop_start()

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False):
        self.client.publish(topic, payload, qos=qos, retain=retain)

    def subscribe(self, topic: str, qos: int = 0, callback=None):
        if callback:
            self.client.message_callback_add(topic, lambda c, u, m: callback(m.topic, m.payload.decode()))
        self.client.subscribe(topic, qos=qos)

    def unsubscribe(self, topic: str):
        self.client.unsubscribe(topic)
