from enum import Enum

# MQTT Broker
BROKER_HOST    = "localhost"
BROKER_PORT    = 1883
TLS_BROKER_PORT = 8883
CERTS_DIR      = "certs"
TLS_ENABLED    = True

# MQTT Topics
TOPIC_HALL       = "hall"
TOPIC_GLOVE      = "glove"
TOPIC_ORDER      = "order"
TOPIC_GAME_STATE = "game"

TOPICS = [TOPIC_HALL, TOPIC_GLOVE, TOPIC_ORDER]

# Game Engine
ALL_INGREDIENTS = [
    "Gin", "Purple Liqueur", "Scotch", "Bourbon",
    "Dark Rum", "Vodka", "Midori", "Rye Whiskey", "Whiskey"
]

BOTTLE_POSITIONS = [0, 1, 3]  # 2 = mixer (fixed), 4 = serve cup (fixed)

POLL_TIMEOUT = 0.01  # seconds

class GameMode(Enum):
    NORMAL   = 0
    TUTORIAL = 1
    CHEAT    = 2


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
    START_SCREEN = 5
    END_SCREEN   = 6

TUTORIAL_BOTTLE_POS = 0

TUTORIAL_INSTRUCTIONS = [
    "Move hand to bottle to select it",                    # 0
    "Grab to pick up bottle",                              # 1
    "Pour into shaker",                                    # 2
    "Release the bottle",                                  # 3
    "Move hand to shaker, and grab to pick up the shaker", # 4
    "Shake the shaker",                                    # 5
    "Pour the shaker into glass",                          # 6
    "Release the shaker",                                  # 7
    "Thumbs up to serve",                                  # 8
]

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
