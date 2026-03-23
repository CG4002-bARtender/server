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
        self._engine.on_output = self._publish

    def start(self):
        self._bridge.connect()

    def _on_event(self, hall: int | None, glove: int | None, order: int | None):
        output = self._engine.update(hall, glove, order)
        if output:
            self._publish(output)

    def _publish(self, output: Output):
        payload = {"state": output.state, "hall_id": output.hall_id}
        if output.picked_up    is not None: payload["picked_up"]    = output.picked_up
        if output.drink        is not None: payload["drink"]        = output.drink
        if output.recipe       is not None: payload["recipe"]       = output.recipe
        if output.bottle_map   is not None: payload["bottle_map"]   = output.bottle_map
        if output.pour_target  is not None: payload["pour_target"]  = output.pour_target
        if output.pour_result  is not None: payload["pour_result"]  = output.pour_result
        if output.round_score  is not None: payload["round_score"]  = output.round_score
        if output.round        is not None: payload["round"]        = output.round
        if output.score        is not None: payload["score"]        = output.score
        serialised = json.dumps(payload)
        print(f'Publishing game state: {serialised}')
        self._bridge.publish(TOPIC_GAME_STATE, serialised)
