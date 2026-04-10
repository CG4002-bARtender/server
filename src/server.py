import json
from .mqtt_bridge import MQTTBridge
from .game_engine import GameEngine, Output
from config import TOPIC_GAME_STATE

class Server:
    def __init__(self, bridge: MQTTBridge, engine: GameEngine):
        self._bridge = bridge
        self._engine = engine
        self._bridge.on_event = self._on_event
        self._bridge._get_state = lambda: self._engine.state
        self._bridge._get_mode  = lambda: self._engine.mode
        self._engine.on_output = self._publish

    def start(self):
        self._bridge.connect()
        self._publish(Output(state=self._engine.state.value))

    def _on_event(self, hall: int | None, glove: int | None, order: int | None):
        output = self._engine.update(hall, glove, order)
        if output:
            self._publish(output)

    def _publish(self, output: Output):
        serialised = json.dumps(output.to_dict())
        print(f'Publishing game state: {serialised}')
        self._bridge.publish(TOPIC_GAME_STATE, serialised)
