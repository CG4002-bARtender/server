import random
from .output import Output
from config import (ALL_INGREDIENTS, BOTTLE_POSITIONS, Gesture, Drink, GameState, GameMode, RECIPES,
                    TUTORIAL_BOTTLE_POS)

class GameEngine:
    def __init__(self):
        self.state = GameState.START_SCREEN
        self._start_game()

    def update(self, hall: int | None, glove: int | None, order: int | None) -> Output | None:
        output = Output(state=self.state.value)
        gesture = Gesture(glove) if glove is not None else None
        drink   = Drink(order)   if order is not None else None

        # Tutorial mode has its own state machine (START_SCREEN → IDLE handled normally)
        if self.mode == GameMode.TUTORIAL and self.state not in (GameState.START_SCREEN,):
            return self._update_tutorial(hall, gesture)

        if self.state == GameState.HOVER and hall is not None:
            output.hall_id = hall
            self.picked_up = hall
            return output

        prev_score          = self.score
        step_results_before = len(self.step_results)
        overpour_before     = self.overpour
        old_state           = self.state

        self.state = self._update_state(gesture, drink)
        output.state = self.state.value

        if (self.state == old_state):
            return None

        if old_state == GameState.IDLE and self.state == GameState.HOVER:
            self._start_round()

        if old_state == GameState.END_SCREEN and self.state == GameState.START_SCREEN:
            self._start_game()

        if self.state in (GameState.GRAB, GameState.POUR, GameState.SHAKE):
            output.picked_up = self.picked_up

        if old_state == GameState.START_SCREEN and self.state == GameState.IDLE:
            output.mode = self.mode.value

        if old_state == GameState.IDLE and self.state == GameState.HOVER:
            output.drink      = self.current_drink.value
            output.recipe     = RECIPES[self.current_drink]
            output.bottle_map = self.bottle_map

        if self.state == GameState.POUR:
            output.pour_target = "shaker" if "shake" in self.steps else "serving_glass"
            if len(self.step_results) > step_results_before:
                output.pour_result = self.step_results[-1]
            if self.overpour and not overpour_before:
                output.overpoured = True

        if self.state in (GameState.END_SCREEN, GameState.IDLE) and old_state not in (GameState.IDLE, GameState.START_SCREEN):
            output.round_score = self.score - prev_score
            output.round       = self.round
            output.score       = self.score

        return output

    def _update_state(self, gesture: Gesture | None, drink: Drink | None) -> GameState:
        match self.state:
            case GameState.START_SCREEN:
                if gesture == Gesture.SERVE:
                    self.mode = GameMode.NORMAL
                    return GameState.IDLE
                elif gesture == Gesture.POUR:
                    self.mode = GameMode.TUTORIAL
                    return GameState.IDLE
                elif gesture == Gesture.SHAKE:
                    self.mode = GameMode.CHEAT
                    return GameState.IDLE

            case GameState.IDLE:
                if drink is not None:
                    self.current_drink = drink
                    return GameState.HOVER

            case GameState.HOVER:
                if gesture == Gesture.GRAB and self.picked_up is not None and self.picked_up != -1:
                    return GameState.GRAB
                elif gesture == Gesture.SERVE and (self.mode == GameMode.CHEAT or self.steps[self.step_index] == "serve"):
                    self._finalise_round()
                    self.current_drink = None
                    return GameState.END_SCREEN if self.round >= 3 else GameState.IDLE

            case GameState.GRAB:
                if gesture == Gesture.RELEASE:
                    return GameState.HOVER
                elif gesture == Gesture.POUR:
                    current_step = self.steps[self.step_index]
                    if self.mode == GameMode.CHEAT or current_step == "pour":
                        self._validate_pour()
                        self.step_index += 1
                    elif current_step in ("shake", "serve"):
                        self.overpour = True
                    return GameState.POUR
                elif gesture == Gesture.SHAKE:
                    if self.mode == GameMode.CHEAT or (self.steps[self.step_index] == "shake" and self.picked_up == 2):
                        self.step_index += 1
                    return GameState.SHAKE
                elif gesture == Gesture.SERVE and (self.mode == GameMode.CHEAT or self.steps[self.step_index] == "serve"):
                    self._finalise_round()
                    self.current_drink = None
                    return GameState.END_SCREEN if self.round >= 3 else GameState.IDLE

            case GameState.SHAKE:
                if gesture is not None:
                    if gesture == Gesture.GRAB:
                        return GameState.GRAB
                    elif gesture == Gesture.RELEASE:
                        return GameState.HOVER
                    else:
                        return GameState.GRAB

            case GameState.POUR:
                if gesture is not None:
                    if gesture == Gesture.GRAB:
                        return GameState.GRAB
                    elif gesture == Gesture.RELEASE:
                        return GameState.HOVER

            case GameState.END_SCREEN:
                if gesture == Gesture.SERVE:
                    return GameState.START_SCREEN

        return self.state

    def _update_tutorial(self, hall: int | None, gesture: Gesture | None) -> Output | None:
        step = self.tutorial_step

        if self.state == GameState.IDLE:
            if hall is not None:
                self.state         = GameState.HOVER
                self.picked_up     = hall
                self.tutorial_step = 0
                return Output(tutorial_step=0, hall_id=hall)
            return None

        if self.state == GameState.HOVER:
            if hall is not None:
                old            = self.picked_up
                self.picked_up = hall
                if hall != old:
                    return Output(tutorial_step=step, hall_id=hall)
                return None

            if gesture == Gesture.GRAB and self.picked_up is not None:
                if self.picked_up == TUTORIAL_BOTTLE_POS and step in (0, 1):
                    self.state = GameState.GRAB
                    if step == 0:
                        self.tutorial_step = 1
                        return Output(tutorial_step=1)
                    return None
                if self.picked_up == 2 and step in (3, 4, 5, 6):
                    self.state = GameState.GRAB
                    if step == 3:
                        self.tutorial_step = 4
                        return Output(tutorial_step=4)
                    return None

            if gesture == Gesture.SERVE and step == 7:
<<<<<<< Updated upstream
=======
                self._start_game()
>>>>>>> Stashed changes
                self.state = GameState.START_SCREEN
                return Output(state=GameState.START_SCREEN.value)

            return None

        if self.state == GameState.GRAB:
            if gesture == Gesture.POUR:
                if step == 1:
                    self.state         = GameState.POUR
                    self.tutorial_step = 2
                    return Output(tutorial_step=2)
                if step == 5:
                    self.state         = GameState.POUR
                    self.tutorial_step = 6
                    return Output(tutorial_step=6)

            if gesture == Gesture.SHAKE and step == 4 and self.picked_up == 2:
                self.state         = GameState.SHAKE
                self.tutorial_step = 5
                return Output(tutorial_step=5)

            if gesture == Gesture.RELEASE:
                return self._tutorial_release(step)

            return None

        if self.state == GameState.POUR:
            if gesture == Gesture.GRAB:
                self.state = GameState.GRAB
                return None
            if gesture == Gesture.RELEASE:
                return self._tutorial_release(step)
            return None

        if self.state == GameState.SHAKE:
            if gesture is not None and gesture != Gesture.SHAKE:
                if gesture == Gesture.POUR and step == 5:
                    self.state         = GameState.POUR
                    self.tutorial_step = 6
                    return Output(tutorial_step=6)
                self.state = GameState.GRAB
                return None
            return None

        return None

    def _tutorial_release(self, step: int) -> Output | None:
        self.state = GameState.HOVER
        if step == 2:
            self.tutorial_step = 3
            return Output(tutorial_step=3)
        if step == 6:
            self.tutorial_step = 7
            return Output(tutorial_step=7)
        return None

    def _start_game(self):
        self.current_drink: Drink | None = None
        self.picked_up: int | None = None
        self.prev_hall: int | None = None
        self.mode: GameMode = GameMode.NORMAL

        self.round:             int       = 0
        self.score:             int       = 0
        self.tutorial_step:     int       = 0
        self.bottle_map:        dict      = {}
        self.expected_sequence: list[str] = []
        self.steps:             list[str] = []
        self.step_index:        int       = 0
        self.overpour:          bool      = False
        self.step_results:      list[str] = []

    def _start_round(self):
        self.round             += 1
        recipe                  = RECIPES[self.current_drink]
        self.expected_sequence  = recipe["ingredients"]
        self.step_results       = []
        self.bottle_map         = self._assign_bottles()
        self.steps              = ["pour"] * len(recipe["ingredients"])
        if recipe["shake"]:
            self.steps.append("shake")
        self.steps.append("serve")
        self.step_index         = 0
        self.overpour           = False

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
        if self.mode == GameMode.CHEAT:
            self.step_results.append("correct")
            return
        ingredient = self.bottle_map.get(self.picked_up)
        expected   = self.expected_sequence[len(self.step_results)]
        result     = "correct" if ingredient == expected else "wrong"
        self.step_results.append(result)

    def _finalise_round(self) -> None:
        if self.mode == GameMode.CHEAT:
            self.score += 1
            return
        poured_all  = len(self.step_results) == len(self.expected_sequence)
        all_correct = all(r == "correct" for r in self.step_results)
        self.score += 1 if (poured_all and all_correct and not self.overpour) else 0
