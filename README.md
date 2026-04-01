# Game Engine — Visualizer Integration Reference

The game engine publishes all output to the `/game` MQTT topic as JSON.
Each message always contains `state` and `hall_id`. Additional fields are present only for specific events.

---

## State Values

| `state` | Meaning |
|---------|---------|
| `0` | IDLE — waiting for an order |
| `1` | HOVER — order received, highlighting bottles |
| `2` | GRAB — bottle picked up |
| `3` | POUR — pouring animation playing |
| `4` | SHAKE — shaking (held until GRAB gesture released) |
| `5` | START_SCREEN — initial screen before game begins |
| `6` | END_SCREEN — shown after the final round |

---

## Bar Layout

```
      [ 4 = serve cup ]
[ 0 ] [ 1 ] [ 2 = mixer ] [ 3 ]
```

- `0`, `1`, `3` — ingredient bottle slots (randomly assigned each round)
- `2` — mixer (fixed)
- `4` — serve cup (fixed)

---

## Output Messages

### 0. Game started — `START_SCREEN → IDLE`

Fired when the player makes a SERVE gesture on the start screen. The game is now ready to receive drink orders.

```json
{
  "state": 0,
  "hall_id": null,
  "round_score": 0,
  "round": 0,
  "score": 0
}
```

- All scoring fields are `0` since no rounds have been played yet.

---

### 1. New order — `IDLE → HOVER`

Fired when a drink order comes in. Includes the drink, its recipe, and the bottle layout for the round.

```json
{
  "state": 1,
  "hall_id": 2,
  "drink": 0,
  "recipe": { "ingredients": ["Gin", "Purple Liqueur"], "shake": true },
  "bottle_map": { "0": "Gin", "1": "Purple Liqueur", "3": "Scotch" }
}
```

- `drink`: integer matching the drink enum (`0` = Aviation, `1` = Godfather, etc.).
- `recipe`: the ingredient list (in required pour order) and whether a shake is required. Pours are validated against this order — pouring the right ingredient at the wrong step counts as wrong.
- `bottle_map` keys are string representations of integer position IDs (e.g. `"0"` corresponds to `hall_id` `0`), always a subset of `"0"`, `"1"`, `"3"`. Values are ingredient name strings.

---

### 2. Hover position updated

Fired when the player's hand moves to a new position while hovering. Used to update bottle highlight.

```json
{
  "state": 1,
  "hall_id": 3
}
```

---

### 3. Bottle grabbed — `HOVER → GRAB`

```json
{
  "state": 2,
  "hall_id": 1,
  "picked_up": 1
}
```

---

### 4. Bottle poured — `GRAB → POUR`

Fired when the player pours. `pour_target` tells the viz which animation to play.

**Ingredient pour** (bottle → shaker, or bottle → serving glass for non-shake drinks):

For bottle -> shaker (for shake = "true" recipes)
```json
{
  "state": 3,
  "hall_id": 1,
  "picked_up": 1,
  "pour_target": "shaker",
  "pour_result": "correct"
}
```

For bottle -> serving glass directly (for shake = "false" recipes)
```json
{
  "state": 3,
  "hall_id": 1,
  "picked_up": 1,
  "pour_target": "serving_glass",
  "pour_result": "correct"
}
```

**Finishing pour** (shaker → serving glass, only for shake drinks after shaking):
```json
{
  "state": 3,
  "hall_id": 2,
  "picked_up": 2,
  "pour_target": "serving_glass"
}
```

- `pour_target`: `"shaker"` if the drink requires a shake and it hasn't happened yet; `"serving_glass"` otherwise.
- `pour_result`: `"correct"` or `"wrong"` for this pour step. Not present on the finishing pour — viz should advance its step counter on each ingredient pour and mark it accordingly.

---

### 5. Pour animation complete — back to `GRAB`

Fired by the animation timer after `POUR`.

```json
{
  "state": 2,
  "hall_id": 1,
  "picked_up": 1
}
```

---

### 6. Bottle released — `GRAB → HOVER`

```json
{
  "state": 1,
  "hall_id": 1
}
```

---

### 7. Shaking — `GRAB → SHAKE`

```json
{
  "state": 4,
  "hall_id": 2,
  "picked_up": 2
}
```

---

### 8. Shake released — `SHAKE → GRAB`

Fired when the glove gesture changes from `SHAKE` back to `GRAB`.

```json
{
  "state": 2,
  "hall_id": 2,
  "picked_up": 2
}
```

---

### 9a. Round ended (mid-game) — `HOVER → IDLE` or `GRAB → IDLE`

Fired when the player serves the drink during rounds 1–2. Includes scoring for the round, then returns to IDLE for the next order.

```json
{
  "state": 0,
  "hall_id": 4,
  "round_score": 1,
  "round": 1,
  "score": 1
}
```

### 9b. Final round ended — `HOVER → END_SCREEN` or `GRAB → END_SCREEN`

Fired when the player serves the drink on round 3 (the final round). Includes scoring for the round and transitions to the end screen.

```json
{
  "state": 6,
  "hall_id": 4,
  "round_score": 1,
  "round": 3,
  "score": 2
}
```

- `round_score`: `1` = pass, `0` = fail for this round.
- `round`: the round number just completed (1-indexed).
- `score`: cumulative total across all rounds this session.
- For **non-shake drinks**, SERVE is accepted from HOVER or GRAB once at least one ingredient pour has been made. For **shake drinks**, SERVE is accepted only after the full sequence is complete (all ingredients poured → shaken → finishing pour). Serving with missing or incorrect steps results in `round_score: 0`.

---

### 10. Game restarted — `END_SCREEN → IDLE`

Fired when the player makes a SERVE gesture on the end screen. The game returns to idle, ready for new drink orders.

```json
{
  "state": 0,
  "hall_id": null
}
```

---

## Fields Reference

| Field | Type | Values | When present |
|-------|------|--------|--------------|
| `state` | `int` | `0` IDLE, `1` HOVER, `2` GRAB, `3` POUR, `4` SHAKE, `5` START_SCREEN, `6` END_SCREEN | Always |
| `hall_id` | `int \| null` | `0`, `1`, `2`, `3`, `4` (bar positions) or `null` before first sensor reading | Always |
| `picked_up` | `int` | `0`, `1`, `2`, `3`, `4` (position of held bottle) | While bottle is held (GRAB, POUR, SHAKE) |
| `drink` | `int` | `0` Aviation, `1` Godfather, `2` IrishCoffee, `3` Martini, `4` MidoriSour, `5` OldFashioned, `6` ScotchNeat, `7` Tuxedo, `8` VodkaNeat, `9` WhiskeyNeat | IDLE → HOVER only |
| `recipe` | `{ ingredients: string[], shake: bool }` | `ingredients`: ordered list of ingredient name strings; `shake`: `true` or `false` | IDLE → HOVER only |
| `bottle_map` | `{ string: string }` | Keys: `"0"`, `"1"`, `"3"` (subset); values: ingredient name strings | IDLE → HOVER only |
| `pour_target` | `string` | `"shaker"` or `"serving_glass"` | GRAB → POUR only |
| `pour_result` | `string` | `"correct"` or `"wrong"` | GRAB → POUR (ingredient pours only, not finishing pour) |
| `round_score` | `int` | `1` (pass) or `0` (fail) | SERVE (→ IDLE or → END_SCREEN) |
| `round` | `int` | 1-indexed round number | SERVE (→ IDLE or → END_SCREEN) |
| `score` | `int` | Cumulative score across all rounds (≥ 0) | SERVE (→ IDLE or → END_SCREEN) |
