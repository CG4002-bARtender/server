"""
Fields published on game/state (consumed by game engine):
  current_order   str   drink the player is supposed to make
  last_gesture    str   most recent gesture label from the glove
  last_recipe     str   recipe classification from Ultra96
  hall_sensor     int   index of the active hall sensor (-1 = none)
  score           int   cumulative score
  cup_status      str   "empty" | "filling" | "ready"
  bottles_grabbed list  bottle indices currently near hall sensors
"""

import json
import threading
from typing import Any


class GameState:
    def __init__(self):
        self._lock = threading.Lock()
        self._state: dict[str, Any] = {
            "current_order":  "none",
            "last_gesture":   "none",
            "last_recipe":    "none",
            "hall_sensor":    -1,
            "score":          0,
            "cup_status":     "empty",
            "bottles_grabbed": [],
        }

    def update(self, **kwargs) -> None:
        with self._lock:
            for k, v in kwargs.items():
                if k in self._state:
                    self._state[k] = v

    def to_json(self) -> str:
        with self._lock:
            return json.dumps(self._state)

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._state)
