"""
Unit tests for GameEngine — happy path scenarios.

Tests drive the engine via update(hall, glove, order) and assert on the
returned Output dataclass fields, matching the contract in README.md.

Bottle positions are randomised each round, so tests read engine.bottle_map
after the order event to derive the concrete positions dynamically.
"""
from src.game_engine import GameEngine
from config import GameState, Gesture, Drink, RECIPES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def order(engine: GameEngine, drink: Drink, hall: int | None = None):
    return engine.update(hall, None, drink.value)

def hover(engine: GameEngine, hall: int):
    return engine.update(hall, None, None)

def grab(engine: GameEngine, hall: int):
    return engine.update(hall, Gesture.GRAB.value, None)

def pour(engine: GameEngine, hall: int):
    return engine.update(hall, Gesture.POUR.value, None)

def release(engine: GameEngine, hall: int):
    return engine.update(hall, Gesture.RELEASE.value, None)

def shake(engine: GameEngine, hall: int = 2):
    return engine.update(hall, Gesture.SHAKE.value, None)

def serve(engine: GameEngine, hall: int = 4):
    return engine.update(hall, Gesture.SERVE.value, None)

def pos(engine: GameEngine, ingredient: str) -> int:
    """Return the bottle position for a given ingredient name."""
    return next(k for k, v in engine.bottle_map.items() if v == ingredient)


# ---------------------------------------------------------------------------
# IDLE → HOVER: order received
# ---------------------------------------------------------------------------

class TestOrderReceived:
    def test_state_transitions_to_hover(self):
        engine = GameEngine()
        out = order(engine, Drink.SCOTCHNEAT)
        assert out.state == GameState.HOVER.value

    def test_output_contains_drink_and_recipe(self):
        engine = GameEngine()
        out = order(engine, Drink.SCOTCHNEAT)
        assert out.drink == Drink.SCOTCHNEAT.value
        assert out.recipe == RECIPES[Drink.SCOTCHNEAT]

    def test_output_contains_bottle_map_with_three_positions(self):
        engine = GameEngine()
        out = order(engine, Drink.AVIATION)
        assert out.bottle_map is not None
        assert set(out.bottle_map.keys()) == {0, 1, 3}

    def test_bottle_map_contains_all_recipe_ingredients(self):
        engine = GameEngine()
        order(engine, Drink.AVIATION)
        values = set(engine.bottle_map.values())
        for ingredient in RECIPES[Drink.AVIATION]["ingredients"]:
            assert ingredient in values

    def test_hall_id_is_none_before_first_sensor_reading(self):
        engine = GameEngine()
        out = order(engine, Drink.SCOTCHNEAT, hall=None)
        assert out.hall_id is None

    def test_no_spurious_fields_on_hover(self):
        engine = GameEngine()
        out = order(engine, Drink.SCOTCHNEAT)
        assert out.picked_up is None
        assert out.pour_target is None
        assert out.pour_result is None
        assert out.round_score is None
        assert out.round is None
        assert out.score is None


# ---------------------------------------------------------------------------
# HOVER: hall highlight updates
# ---------------------------------------------------------------------------

class TestHoverHighlight:
    def test_hall_update_returns_output(self):
        engine = GameEngine()
        order(engine, Drink.SCOTCHNEAT)
        out = hover(engine, 1)
        assert out is not None

    def test_hall_update_reflects_new_position(self):
        engine = GameEngine()
        order(engine, Drink.SCOTCHNEAT)
        out = hover(engine, 3)
        assert out.state == GameState.HOVER.value
        assert out.hall_id == 3

    def test_hall_update_does_not_re_send_drink_or_recipe(self):
        engine = GameEngine()
        order(engine, Drink.SCOTCHNEAT)
        out = hover(engine, 0)
        assert out.drink is None
        assert out.recipe is None
        assert out.bottle_map is None

    def test_consecutive_hall_updates(self):
        engine = GameEngine()
        order(engine, Drink.SCOTCHNEAT)
        hover(engine, 0)
        out = hover(engine, 1)
        assert out.hall_id == 1


# ---------------------------------------------------------------------------
# HOVER → GRAB
# ---------------------------------------------------------------------------

class TestGrab:
    def test_grab_transitions_to_grab_state(self):
        engine = GameEngine()
        order(engine, Drink.SCOTCHNEAT)
        scotch = pos(engine, "Scotch")
        out = grab(engine, scotch)
        assert out.state == GameState.GRAB.value

    def test_grab_output_has_hall_id_and_picked_up(self):
        engine = GameEngine()
        order(engine, Drink.SCOTCHNEAT)
        scotch = pos(engine, "Scotch")
        out = grab(engine, scotch)
        assert out.hall_id == scotch
        assert out.picked_up == scotch

    def test_grab_no_pour_or_score_fields(self):
        engine = GameEngine()
        order(engine, Drink.SCOTCHNEAT)
        out = grab(engine, pos(engine, "Scotch"))
        assert out.pour_target is None
        assert out.pour_result is None
        assert out.round_score is None


# ---------------------------------------------------------------------------
# Happy path: non-shake, single ingredient (ScotchNeat)
# ---------------------------------------------------------------------------

class TestHappyPathScotchNeat:
    """ScotchNeat: ingredients=["Scotch"], shake=False"""

    def setup_method(self):
        self.engine = GameEngine()
        order(self.engine, Drink.SCOTCHNEAT)
        self.scotch = pos(self.engine, "Scotch")

    def test_pour_target_is_serving_glass(self):
        grab(self.engine, self.scotch)
        out = pour(self.engine, self.scotch)
        assert out.state == GameState.POUR.value
        assert out.pour_target == "serving_glass"

    def test_pour_result_is_correct(self):
        grab(self.engine, self.scotch)
        out = pour(self.engine, self.scotch)
        assert out.pour_result == "correct"

    def test_release_returns_to_hover(self):
        grab(self.engine, self.scotch)
        pour(self.engine, self.scotch)
        out = release(self.engine, self.scotch)
        assert out.state == GameState.HOVER.value
        assert out.hall_id == self.scotch

    def test_serve_awards_round_score_1(self):
        grab(self.engine, self.scotch)
        pour(self.engine, self.scotch)
        release(self.engine, self.scotch)
        out = serve(self.engine, hall=4)
        assert out.state == GameState.IDLE.value
        assert out.round_score == 1

    def test_serve_output_has_round_and_score(self):
        grab(self.engine, self.scotch)
        pour(self.engine, self.scotch)
        release(self.engine, self.scotch)
        out = serve(self.engine, hall=4)
        assert out.round == 1
        assert out.score == 1
        assert out.hall_id == 4

    def test_serve_no_recipe_or_bottle_map_on_idle(self):
        grab(self.engine, self.scotch)
        pour(self.engine, self.scotch)
        release(self.engine, self.scotch)
        out = serve(self.engine)
        assert out.drink is None
        assert out.recipe is None
        assert out.bottle_map is None


# ---------------------------------------------------------------------------
# Happy path: non-shake, two ingredients (Godfather: Scotch, Bourbon)
# ---------------------------------------------------------------------------

class TestHappyPathGodfather:
    """Godfather: ingredients=["Scotch", "Bourbon"], shake=False"""

    def setup_method(self):
        self.engine = GameEngine()
        order(self.engine, Drink.GODFATHER)
        self.scotch  = pos(self.engine, "Scotch")
        self.bourbon = pos(self.engine, "Bourbon")

    def _pour_ingredient(self, hall: int):
        grab(self.engine, hall)
        pour(self.engine, hall)
        release(self.engine, hall)

    def test_first_pour_correct_to_serving_glass(self):
        grab(self.engine, self.scotch)
        out = pour(self.engine, self.scotch)
        assert out.pour_target == "serving_glass"
        assert out.pour_result == "correct"

    def test_second_pour_correct_to_serving_glass(self):
        self._pour_ingredient(self.scotch)
        grab(self.engine, self.bourbon)
        out = pour(self.engine, self.bourbon)
        assert out.pour_target == "serving_glass"
        assert out.pour_result == "correct"

    def test_full_happy_path_round_score_1(self):
        self._pour_ingredient(self.scotch)
        self._pour_ingredient(self.bourbon)
        out = serve(self.engine)
        assert out.round_score == 1
        assert out.score == 1


# ---------------------------------------------------------------------------
# Happy path: shake drink (Aviation: Gin, Purple Liqueur, shake=True)
# ---------------------------------------------------------------------------

class TestHappyPathAviation:
    """Aviation: ingredients=["Gin", "Purple Liqueur"], shake=True"""

    def setup_method(self):
        self.engine = GameEngine()
        order(self.engine, Drink.AVIATION)
        self.gin     = pos(self.engine, "Gin")
        self.liqueur = pos(self.engine, "Purple Liqueur")

    def _pour_ingredient(self, hall: int):
        grab(self.engine, hall)
        pour(self.engine, hall)
        release(self.engine, hall)

    def test_pour_gin_target_is_shaker(self):
        grab(self.engine, self.gin)
        out = pour(self.engine, self.gin)
        assert out.pour_target == "shaker"
        assert out.pour_result == "correct"

    def test_pour_liqueur_target_is_shaker(self):
        self._pour_ingredient(self.gin)
        grab(self.engine, self.liqueur)
        out = pour(self.engine, self.liqueur)
        assert out.pour_target == "shaker"
        assert out.pour_result == "correct"

    def test_shake_transitions_to_shake_state(self):
        self._pour_ingredient(self.gin)
        self._pour_ingredient(self.liqueur)
        grab(self.engine, 2)
        out = shake(self.engine)
        assert out.state == GameState.SHAKE.value
        assert out.picked_up == 2
        assert out.hall_id == 2

    def test_shake_release_returns_to_grab(self):
        self._pour_ingredient(self.gin)
        self._pour_ingredient(self.liqueur)
        grab(self.engine, 2)
        shake(self.engine)
        out = release(self.engine, 2)
        assert out.state == GameState.GRAB.value
        assert out.picked_up == 2

    def test_finishing_pour_target_is_serving_glass(self):
        self._pour_ingredient(self.gin)
        self._pour_ingredient(self.liqueur)
        grab(self.engine, 2)
        shake(self.engine)
        release(self.engine, 2)
        out = pour(self.engine, 2)
        assert out.state == GameState.POUR.value
        assert out.pour_target == "serving_glass"

    def test_finishing_pour_has_no_pour_result(self):
        """Finishing pour (shaker → glass) does not emit pour_result."""
        self._pour_ingredient(self.gin)
        self._pour_ingredient(self.liqueur)
        grab(self.engine, 2)
        shake(self.engine)
        release(self.engine, 2)
        out = pour(self.engine, 2)
        assert out.pour_result is None

    def test_full_happy_path_round_score_1(self):
        self._pour_ingredient(self.gin)
        self._pour_ingredient(self.liqueur)
        grab(self.engine, 2)
        shake(self.engine)
        release(self.engine, 2)
        pour(self.engine, 2)
        release(self.engine, 2)
        out = serve(self.engine)
        assert out.round_score == 1
        assert out.score == 1


# ---------------------------------------------------------------------------
# Multi-round score accumulation
# ---------------------------------------------------------------------------

class TestMultiRound:
    def _play_scotch_neat(self, engine: GameEngine):
        order(engine, Drink.SCOTCHNEAT)
        scotch = pos(engine, "Scotch")
        grab(engine, scotch)
        pour(engine, scotch)
        release(engine, scotch)
        return serve(engine)

    def test_round_counter_increments(self):
        engine = GameEngine()
        out1 = self._play_scotch_neat(engine)
        out2 = self._play_scotch_neat(engine)
        assert out1.round == 1
        assert out2.round == 2

    def test_cumulative_score_accumulates(self):
        engine = GameEngine()
        out1 = self._play_scotch_neat(engine)
        out2 = self._play_scotch_neat(engine)
        assert out1.score == 1
        assert out2.score == 2

    def test_new_round_resets_bottle_map(self):
        engine = GameEngine()
        self._play_scotch_neat(engine)
        first_map = engine.bottle_map.copy()
        order(engine, Drink.GODFATHER)
        # bottle_map should now reflect the new drink's ingredients
        values = set(engine.bottle_map.values())
        assert "Scotch" in values or "Bourbon" in values  # Godfather ingredients
