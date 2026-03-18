from .mqtt_bridge import MQTTBridge
from .game_engine import GameEngine, Output

TOPIC_GAME_STATE = "/game/state"


class Server:
    def __init__(self, bridge: MQTTBridge, engine: GameEngine):
        self._bridge = bridge
        self._engine = engine
        self._bridge.on_event = self._on_event
        self._engine.on_output = self._publish

    def start(self):
        self._bridge.connect()

    def stop(self):
        self._bridge.disconnect()

    def _on_event(self, hall: int | None, glove: int | None, order: int | None):
        output = self._engine.update(hall, glove, order)
        if output:
            self._publish(output)

    def _publish(self, output: Output):
        self._bridge.publish(TOPIC_GAME_STATE, {"state": output.state, "hall_id": output.hall_id})
