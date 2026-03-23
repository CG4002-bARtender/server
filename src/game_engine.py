import random
from dataclasses import dataclass, field
from enum import Enum
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

        # per-update accumulators (reset each update() call)
        self._last_round_score: int | None = None

    def update(self, hall: int | None, glove: int | None, order: int | None) -> Output | None:
        self._last_round_score = None

        gesture   = Gesture(glove) if glove is not None else None
        drink     = Drink(order)   if order is not None else None
        old_state = self.state
        self.state = self._update_state(hall, gesture, drink)

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
                output.round_score = self._last_round_score
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
                elif gesture == Gesture.SERVE:
                    self._last_round_score = self._finalise_round()
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
                    self._validate_shake()
                    return GameState.SHAKE
                elif gesture == Gesture.SERVE:
                    self._last_round_score = self._finalise_round()
                    self.current_drink = None
                    return GameState.IDLE

            case GameState.SHAKE:
                if gesture is not None and gesture != Gesture.SHAKE:
                    return GameState.GRAB

            case GameState.POUR:
                if gesture == Gesture.RELEASE:
                    return GameState.HOVER
                if gesture == Gesture.GRAB:
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
        if pos not in self.bottle_map or len(self.step_results) >= len(self.expected_sequence):
            self.step_results.append("wrong")
            return
        ingredient = self.bottle_map[pos]
        expected   = self.expected_sequence[len(self.step_results)]
        result     = "correct" if ingredient == expected else "wrong"
        self.step_results.append(result)

    def _validate_shake(self):
        if self.needs_shake:
            self.shook = True

    def _finalise_round(self) -> int:
        poured_all  = len(self.step_results) == len(self.expected_sequence)
        all_correct = all(r == "correct" for r in self.step_results)
        shook_ok    = self.shook if self.needs_shake else True
        round_score = 1 if (poured_all and all_correct and shook_ok) else 0
        self.score += round_score
        return round_score
