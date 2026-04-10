import json
from .mqtt_bridge import MQTTBridge
from .game_engine import GameEngine, GameState, Output
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
            needs_ack = self._needs_anim_ack(output)
            if needs_ack:
                self._bridge.clear_anim_ack()
            self._publish(output)
            if needs_ack:
                print(f"Waiting for anim ACK (state={output.state})")
                self._bridge.wait_for_anim_ack()

    def _needs_anim_ack(self, output: Output) -> bool:
        s = output.state
        if s == GameState.POUR.value:       # state=3: wait for pour + untilt
            return True
        if s == GameState.SHAKE.value:      # state=4: wait for shake + return
            return True
        if s == GameState.IDLE.value and output.round is not None:  # state=0, round end
            return True
        if s == GameState.END_SCREEN.value: # state=6: wait for game end result
            return True
        return False

    def _publish(self, output: Output):
        serialised = json.dumps(output.to_dict())
        print(f'Publishing game state: {serialised}')
        self._bridge.publish(TOPIC_GAME_STATE, serialised)
