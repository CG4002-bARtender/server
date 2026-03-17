"""
bARtender Game Server — Config
All tunable constants in one place.
"""

# ── MQTT broker (laptop, localhost) 
BROKER_HOST = "localhost"
BROKER_PORT  = 8883          # plain; swap to 8883 + TLS when certs are ready

# ── Topics published BY the ESP32 bar station 
TOPIC_AUDIO = "audio"        # raw PCM chunks (bytes)
TOPIC_HALL  = "hall"         # 1-byte: int8, index of closest hall sensor (-1 = none)

# ── Topic published BY the glove ESP32 (via BLE relay or direct MQTT) 
TOPIC_GESTURE = "gesture"    # JSON: {"gesture": <str>, "confidence": <float>}

# ── Topics published by the server
TOPIC_RECIPE    = "recipe"       # forwarded from Ultra96 → bar ESP ACK
TOPIC_ACK       = "ack"          # 0x01 ACK / 0x00 NACK back to bar ESP
TOPIC_GAME_STATE    = "game/state"         # consumed by Unity visualiser & game engine
TOPIC_ENGINE_OUTPUT = "game/engine/output" # published by game engine; forwards to visualiser

# ── Ultra96 inference endpoint (via SSH reverse tunnel) 
ULTRA96_BROKER_HOST = "localhost"
ULTRA96_BROKER_PORT  = 8883      # tunnel maps Ultra96:1883 → localhost:1883
TOPIC_ULTRA96_AUDIO_IN  = "ultra96/audio_in"   # server → Ultra96
TOPIC_ULTRA96_RECIPE_OUT = "ultra96/recipe_out" # Ultra96 → server

# ── Audio reassembly 
AUDIO_CHUNK_SIZE   = 8 * 1024    # must match ESP32 config::mqtt::AUDIO_CHUNK_SIZE
AUDIO_IDLE_TIMEOUT = 1.5         # seconds of silence → treat clip as complete

# ── Game state defaults 
INITIAL_SCORE = 0
