import threading
from dataclasses import dataclass
from enum import Enum
from typing import Callable


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


ANIMATION_TIMEOUT = 2.0  # seconds


@dataclass
class Output:
    state: int
    hall_id: int | None


class GameEngine:
    def __init__(self):
        self.state = GameState.IDLE
        self.current_drink: Drink | None = None
        self.hall: int | None = None
        self.picked_up: int | None = None
        self._timer: threading.Timer | None = None
        self.on_output: Callable[[Output], None] | None = None

    def update(self, hall: int | None, glove: int | None, order: int | None) -> Output | None:
        if hall is not None:
            self.hall = hall

        gesture = Gesture(glove) if glove is not None else None
        drink   = Drink(order)   if order is not None else None

        new_state = self._update_state(gesture, drink)

        has_changed_state     = new_state != self.state
        has_updated_highlight = self.state == GameState.HOVER and hall is not None

        self.state = new_state

        if has_changed_state or has_updated_highlight:
            return Output(state=new_state.value, hall_id=self.hall)
        return None

    def _update_state(self, gesture: Gesture | None, drink: Drink | None) -> GameState:
        match self.state:
            case GameState.IDLE:
                if drink is not None:
                    self.current_drink = drink
                    return GameState.HOVER

            case GameState.HOVER:
                if gesture == Gesture.GRAB and self.hall is not None:
                    self.picked_up = self.hall
                    return GameState.GRAB
                elif gesture == Gesture.SERVE:
                    self.current_drink = None
                    return GameState.IDLE

            case GameState.GRAB:
                if gesture == Gesture.RELEASE:
                    return GameState.HOVER
                elif gesture == Gesture.POUR:
                    self._start_timer()
                    return GameState.POUR
                elif gesture == Gesture.SHAKE:
                    self._start_timer()
                    return GameState.SHAKE
                elif gesture == Gesture.SERVE:
                    self.current_drink = None
                    return GameState.IDLE

        return self.state

    def _start_timer(self):
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(ANIMATION_TIMEOUT, self._on_anim_timeout)
        self._timer.daemon = True
        self._timer.start()

    def _on_anim_timeout(self):
        self._timer = None
        self.state = GameState.GRAB
        if self.on_output:
            self.on_output(Output(state=GameState.GRAB.value, hall_id=self.hall))
