from dataclasses import dataclass, field, asdict

@dataclass
class Output:
    state:        int
    hall_id:      int | None       = field(default=None)  # 0 - 3, hall ids of the detected hall effect
    mode:         int | None       = field(default=None)  # 0=normal, 1=tutorial, 2=cheat; sent on START_SCREEN→IDLE
    picked_up:    int | None       = field(default=None)  # set while a bottle is held (GRAB/POUR/SHAKE)
    drink:        int | None       = field(default=None)  # drink enum value, sent on IDLE→HOVER
    recipe:       dict | None      = field(default=None)  # {"ingredients": [...], "shake": bool}, sent on IDLE→HOVER
    bottle_map:   dict | None      = field(default=None)  # sent on IDLE→HOVER
    pour_target:  str | None       = field(default=None)  # "shaker" | "serving_glass"
    pour_result:  str | None       = field(default=None)  # "correct" | "wrong" for this pour step
    round_score:  int | None       = field(default=None)  # sent on SERVE
    round:        int | None       = field(default=None)  # current round number, sent on SERVE
    score:        int | None       = field(default=None)  # cumulative, sent on SERVE

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}
