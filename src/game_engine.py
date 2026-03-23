import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable
from config import ALL_INGREDIENTS, BOTTLE_POSITIONS


class Gesture(Enum):
    GRAB    = 0
    RELEASE = 1
    POUR    = 2
    SHAKE   = 3
    SERVE   = 4


class Drink(Enum):
    AVIATION     = 0
    GODFATHER    = 1
    IRISHCOFFEE  = 2
    MARTINI      = 3
    MIDORISOUR   = 4
    OLDFASHIONED = 5
    SCOTCHNEAT   = 6
    TUXEDO       = 7
    VODKANEAT    = 8
    WHISKEYNEAT  = 9


class GameState(Enum):
    IDLE  = 0
    HOVER = 1
    GRAB  = 2
    POUR  = 3
    SHAKE = 4



RECIPES: dict[Drink, dict] = {
    Drink.AVIATION:     {"ingredients": ["Gin", "Purple Liqueur"], "shake": True},
    Drink.GODFATHER:    {"ingredients": ["Scotch", "Bourbon"],     "shake": False},
    Drink.IRISHCOFFEE:  {"ingredients": ["Bourbon", "Dark Rum"],   "shake": False},
    Drink.MARTINI:      {"ingredients": ["Gin", "Vodka"],          "shake": True},
    Drink.MIDORISOUR:   {"ingredients": ["Midori", "Vodka"],       "shake": True},
    Drink.OLDFASHIONED: {"ingredients": ["Bourbon", "Rye Whiskey"],"shake": False},
    Drink.SCOTCHNEAT:   {"ingredients": ["Scotch"],                "shake": False},
    Drink.TUXEDO:       {"ingredients": ["Gin", "Scotch"],         "shake": True},
    Drink.VODKANEAT:    {"ingredients": ["Vodka"],                 "shake": False},
    Drink.WHISKEYNEAT:  {"ingredients": ["Whiskey"],               "shake": False},
}


@dataclass
class Output:
    state:        int
    hall_id:      int | None
    picked_up:    int | None       = field(default=None)  # set while a bottle is held (GRAB/POUR/SHAKE)
    drink:        int | None       = field(default=None)  # drink enum value, sent on IDLE→HOVER
    recipe:       dict | None      = field(default=None)  # {"ingredients": [...], "shake": bool}, sent on IDLE→HOVER
    bottle_map:   dict | None      = field(default=None)  # sent on IDLE→HOVER
    pour_target:  str | None       = field(default=None)  # "shaker" | "serving_glass"
    pour_result:  str | None       = field(default=None)  # "correct" | "wrong" for this pour step
    round_score:  int | None       = field(default=None)  # sent on SERVE
    round:        int | None       = field(default=None)  # current round number, sent on SERVE
    score:        int | None       = field(default=None)  # cumulative, sent on SERVE


class GameEngine:
    def __init__(self):
        self.state = GameState.IDLE
        self.current_drink: Drink | None = None
        self.hall: int | None = None
        self.picked_up: int | None = None
        self.on_output: Callable[[Output], None] | None = None

        # per-round game logic
        self.round:             int       = 0
        self.score:             int       = 0
        self.bottle_map:        dict      = {}
        self.expected_sequence: list[str] = []
        self.needs_shake:       bool      = False
        self.shook:             bool      = False
        self.poured_final:      bool      = False
        self.step_results:      list[str] = []

        # per-update accumulators (reset each update() call)
        self._last_round_score: int | None = None

    def update(self, hall: int | None, glove: int | None, order: int | None) -> Output | None:
        print(f"[update] called | state={self.state.name} | hall={hall} glove={glove} order={order}")
        if hall is not None:
            self.hall = hall
        self._last_round_score = None

        gesture   = Gesture(glove) if glove is not None else None
        drink     = Drink(order)   if order is not None else None
        old_state = self.state
        new_state = self._update_state(gesture, drink)

        print(f"[update] gesture={gesture} drink={drink} | {old_state.name} -> {new_state.name}")

        has_changed_state     = new_state != old_state
        has_updated_highlight = old_state == GameState.HOVER and hall is not None

        if old_state == GameState.IDLE and new_state == GameState.HOVER:
            self._start_round()

        self.state = new_state

        if has_changed_state or has_updated_highlight:
            output = Output(state=new_state.value, hall_id=self.hall)

            if new_state in (GameState.GRAB, GameState.POUR, GameState.SHAKE):
                output.picked_up = self.picked_up

            if old_state == GameState.IDLE and new_state == GameState.HOVER:
                output.drink      = self.current_drink.value
                output.recipe     = RECIPES[self.current_drink]
                output.bottle_map = self.bottle_map

            if new_state == GameState.POUR:
                finishing_pour = self.needs_shake and self.shook and self.picked_up == 2
                output.pour_target = "serving_glass" if (not self.needs_shake or (self.shook and self.picked_up == 2)) else "shaker"
                if not finishing_pour:
                    output.pour_result = self.step_results[-1]
                print(f"[update] POUR | finishing_pour={finishing_pour} pour_target={output.pour_target} pour_result={output.pour_result}")

            if new_state == GameState.IDLE and old_state != GameState.IDLE:
                output.round_score = self._last_round_score
                output.round       = self.round
                output.score       = self.score
                print(f"[update] round ended | round_score={output.round_score} round={output.round} score={output.score}")

            print(f"[update] emitting output: {output}")
            return output

        print(f"[update] no state change and no highlight update, returning None")
        return None

    def _update_state(self, gesture: Gesture | None, drink: Drink | None) -> GameState:
        print(f"[_update_state] state={self.state.name} gesture={gesture} drink={drink} | picked_up={self.picked_up} hall={self.hall}")
        match self.state:
            case GameState.IDLE:
                if drink is not None:
                    self.current_drink = drink
                    print(f"[_update_state] IDLE: received order {drink.name}, -> HOVER")
                    return GameState.HOVER

            case GameState.HOVER:
                if gesture == Gesture.GRAB and self.hall is not None and self.hall != -1:
                    self.picked_up = self.hall
                    print(f"[_update_state] HOVER: GRAB at hall={self.hall}, picked_up={self.picked_up} -> GRAB")
                    return GameState.GRAB
                elif gesture == Gesture.SERVE:
                    print(f"[_update_state] HOVER: SERVE gesture -> finalising round -> IDLE")
                    self._last_round_score = self._finalise_round()
                    self.current_drink = None
                    return GameState.IDLE
                else:
                    print(f"[_update_state] HOVER: gesture={gesture} hall={self.hall}, no transition")

            case GameState.GRAB:
                if gesture == Gesture.RELEASE:
                    print(f"[_update_state] GRAB: RELEASE -> HOVER")
                    return GameState.HOVER
                elif gesture == Gesture.POUR:
                    if self.needs_shake and self.shook and self.picked_up == 2:
                        self.poured_final = True
                        print(f"[_update_state] GRAB: finishing pour -> POUR")
                    else:
                        self._validate_pour()
                        print(f"[_update_state] GRAB: pour validated, step_results={self.step_results} -> POUR")
                    return GameState.POUR
                elif gesture == Gesture.SHAKE:
                    print(f"[_update_state] GRAB: SHAKE | needs_shake={self.needs_shake} shook={self.shook} picked_up={self.picked_up}")
                    self._validate_shake()
                    print(f"[_update_state] GRAB: after shake, shook={self.shook} -> SHAKE")
                    return GameState.SHAKE
                elif gesture == Gesture.SERVE:
                    print(f"[_update_state] GRAB: SERVE -> finalising round -> IDLE")
                    self._last_round_score = self._finalise_round()
                    self.current_drink = None
                    return GameState.IDLE
                else:
                    print(f"[_update_state] GRAB: unhandled gesture={gesture}")

            case GameState.SHAKE:
                if gesture is not None and gesture != Gesture.SHAKE:
                    print(f"[_update_state] SHAKE: gesture={gesture} != SHAKE -> GRAB")
                    return GameState.GRAB
                else:
                    print(f"[_update_state] SHAKE: still shaking, gesture={gesture}")

            case GameState.POUR:
                if gesture == Gesture.RELEASE:
                    print(f"[_update_state] POUR: RELEASE -> HOVER")
                    return GameState.HOVER
                if gesture == Gesture.GRAB:
                    print(f"[_update_state] POUR: GRAB -> GRAB")
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
        self.bottle_map        = self._assign_bottles(self.expected_sequence)
        print(f"[_start_round] round={self.round} drink={self.current_drink.name} expected={self.expected_sequence} needs_shake={self.needs_shake} bottle_map={self.bottle_map}")

    def _assign_bottles(self, ingredients: list[str]) -> dict:
        positions = BOTTLE_POSITIONS.copy()
        random.shuffle(positions)
        bottle_map = {}
        for i, ingredient in enumerate(ingredients):
            bottle_map[positions[i]] = ingredient
        decoys = [x for x in ALL_INGREDIENTS if x not in ingredients]
        for pos in positions[len(ingredients):]:
            bottle_map[pos] = random.choice(decoys)
        return bottle_map

    def _validate_pour(self):
        pos = self.picked_up
        print(f"[_validate_pour] pos={pos} bottle_map={self.bottle_map} step_results={self.step_results} expected={self.expected_sequence}")
        if pos not in self.bottle_map or len(self.step_results) >= len(self.expected_sequence):
            print(f"[_validate_pour] invalid pour (pos not in map or already complete) -> 'wrong'")
            self.step_results.append("wrong")
            return
        ingredient = self.bottle_map[pos]
        expected   = self.expected_sequence[len(self.step_results)]
        result     = "correct" if ingredient == expected else "wrong"
        print(f"[_validate_pour] poured '{ingredient}' expected '{expected}' -> {result}")
        self.step_results.append(result)

    def _validate_shake(self):
        print(f"[_validate_shake] needs_shake={self.needs_shake} shook (before)={self.shook}")
        if self.needs_shake:
            self.shook = True
        print(f"[_validate_shake] shook (after)={self.shook}")

    def _finalise_round(self) -> int:
        poured_all  = len(self.step_results) == len(self.expected_sequence)
        all_correct = all(r == "correct" for r in self.step_results)
        shook_ok    = self.shook if self.needs_shake else True
        round_score = 1 if (poured_all and all_correct and shook_ok) else 0
        self.score += round_score
        print(f"[_finalise_round] step_results={self.step_results} expected={self.expected_sequence}")
        print(f"[_finalise_round] poured_all={poured_all} all_correct={all_correct} needs_shake={self.needs_shake} shook={self.shook} shook_ok={shook_ok}")
        print(f"[_finalise_round] round_score={round_score} cumulative_score={self.score}")
        return round_score

