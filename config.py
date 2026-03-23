# MQTT Broker
BROKER_HOST = "172.20.10.2"
BROKER_PORT = 1883

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
