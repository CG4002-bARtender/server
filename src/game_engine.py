import random
import time
from .output import Output
from config import ALL_INGREDIENTS, BOTTLE_POSITIONS, POUR_TIMEOUT, Gesture, Drink, GameState, RECIPES

class GameEngine:
    def __init__(self):
        self.state = GameState.IDLE
        self.current_drink: Drink | None = None
        self.picked_up: int | None = None

        # per-round game logic
        self.round:             int       = 0
        self.score:             int       = 0
        self.bottle_map:        dict      = {}
        self.expected_sequence: list[str] = []
        self.needs_shake:       bool      = False
        self.shook:             bool      = False
        self.poured_final:      bool      = False
        self.step_results:      list[str] = []
        self._pour_start:       float | None = None

    def update(self, hall: int | None, glove: int | None, order: int | None) -> Output | None:
        prev_score = self.score
        gesture    = Gesture(glove) if glove is not None else None
        drink     = Drink(order)   if order is not None else None
        old_state = self.state
        self.state = self._update_state(hall, gesture, drink)

        if self.state == GameState.POUR and old_state != GameState.POUR:
            self._pour_start = time.time()

        has_changed_state    = self.state != old_state
        is_highlight_update  = glove is None and order is None  # hall-only call from HOVER

        if old_state == GameState.IDLE and self.state == GameState.HOVER:
            self._start_round()

        if has_changed_state or is_highlight_update:
            output = Output(state=self.state.value, hall_id=hall)

            if self.state in (GameState.GRAB, GameState.POUR, GameState.SHAKE):
                output.picked_up = self.picked_up

            if old_state == GameState.IDLE and self.state == GameState.HOVER:
                output.drink      = self.current_drink.value
                output.recipe     = RECIPES[self.current_drink]
                output.bottle_map = self.bottle_map

            if self.state == GameState.POUR:
                finishing_pour = self.needs_shake and self.shook and self.picked_up == 2
                output.pour_target = "serving_glass" if (not self.needs_shake or (self.shook and self.picked_up == 2)) else "shaker"
                if not finishing_pour:
                    output.pour_result = self.step_results[-1]

            if self.state == GameState.IDLE and old_state != GameState.IDLE:
                output.round_score = self.score - prev_score
                output.round       = self.round
                output.score       = self.score

            return output

        return None

    def _update_state(self, hall: int | None, gesture: Gesture | None, drink: Drink | None) -> GameState:
        match self.state:
            case GameState.IDLE:
                if drink is not None:
                    self.current_drink = drink
                    return GameState.HOVER

            case GameState.HOVER:
                if gesture == Gesture.GRAB and hall is not None and hall != -1:
                    self.picked_up = hall
                    return GameState.GRAB
                elif gesture == Gesture.SERVE and self._can_serve():
                    self._finalise_round()
                    self.current_drink = None
                    return GameState.IDLE

            case GameState.GRAB:
                if gesture == Gesture.RELEASE:
                    return GameState.HOVER
                elif gesture == Gesture.POUR:
                    if self.needs_shake and self.shook and self.picked_up == 2:
                        self.poured_final = True
                    else:
                        self._validate_pour()
                    return GameState.POUR
                elif gesture == Gesture.SHAKE:
                    if self.needs_shake:
                        self.shook = True
                    return GameState.SHAKE
                elif gesture == Gesture.SERVE and self._can_serve():
                    self._finalise_round()
                    self.current_drink = None
                    return GameState.IDLE

            case GameState.SHAKE:
                if gesture is not None and gesture != Gesture.SHAKE:
                    return GameState.GRAB

            case GameState.POUR:
                if self._pour_start is not None and time.time() - self._pour_start >= POUR_TIMEOUT:
                    self._pour_start = None
                    return GameState.GRAB

        return self.state

    def _start_round(self):
        self.round            += 1
        recipe = RECIPES[self.current_drink]
        self.expected_sequence = recipe["ingredients"]
        self.needs_shake       = recipe["shake"]
        self.step_results      = []
        self.shook             = False
        self.poured_final      = False
        self.bottle_map        = self._assign_bottles()

    def _assign_bottles(self) -> dict:
        positions = BOTTLE_POSITIONS.copy()
        random.shuffle(positions)
        bottle_map = {}
        for i, ingredient in enumerate(self.expected_sequence):
            bottle_map[positions[i]] = ingredient
        decoys = [x for x in ALL_INGREDIENTS if x not in self.expected_sequence]
        for pos in positions[len(self.expected_sequence):]:
            bottle_map[pos] = random.choice(decoys)
        return bottle_map

    def _validate_pour(self):
        pos = self.picked_up
        if pos not in self.bottle_map or len(self.step_results) >= len(self.expected_sequence):
            self.step_results.append("wrong")
            return
        ingredient = self.bottle_map[pos]
        expected   = self.expected_sequence[len(self.step_results)]
        result     = "correct" if ingredient == expected else "wrong"
        self.step_results.append(result)

    def _can_serve(self) -> bool:
        if self.needs_shake:
            return self.poured_final
        else:
            return len(self.step_results) >= 1

    def _finalise_round(self) -> None:
        poured_all  = len(self.step_results) == len(self.expected_sequence)
        all_correct = all(r == "correct" for r in self.step_results)
        shook_ok    = self.shook if self.needs_shake else True
        self.score += 1 if (poured_all and all_correct and shook_ok) else 0
