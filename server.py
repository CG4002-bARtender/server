#!/usr/bin/env python3
"""
bARtender Game Server
=====================

Threads
-------
  T1 main        poll AudioBuffer; drive state publish loop
  T2 mqtt_loop   paho network I/O (automatic via loop_start)
"""

import struct
import time
import threading
import paho.mqtt.client as mqtt

import config
import colors
from audio_buffer import AudioBuffer
from game_state   import GameState

# ── Shared state ───────────────────────────────────────────────────────────────
audio_buf   = AudioBuffer()
game_state  = GameState()

# Pending recipe result from Ultra96 (set by MQTT callback, consumed by main loop)
_pending_recipe: str | None = None
_recipe_lock = threading.Lock()

# ─────────────────────────────────────────────────────────────────────────────
# MQTT callbacks


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"{colors.INFO} MQTT connected (broker {config.BROKER_HOST}:{config.BROKER_PORT})")
        client.subscribe(config.TOPIC_AUDIO)
        client.subscribe(config.TOPIC_HALL)
        client.subscribe(config.TOPIC_GESTURE)
        client.subscribe(config.TOPIC_ULTRA96_RECIPE_OUT)
        client.subscribe(config.TOPIC_ENGINE_OUTPUT)
        print(f"{colors.INFO} Subscribed: {config.TOPIC_AUDIO}, {config.TOPIC_HALL}, "
              f"{config.TOPIC_GESTURE}, {config.TOPIC_ULTRA96_RECIPE_OUT}, "
              f"{config.TOPIC_ENGINE_OUTPUT}")
    else:
        print(f"{colors.ERROR} MQTT connect failed rc={rc}")


def on_message(client, userdata, msg):
    topic   = msg.topic
    payload = msg.payload

    # ── Raw PCM audio chunk from bar ESP32 ────────────────────────────────────
    if topic == config.TOPIC_AUDIO:
        audio_buf.push(payload)
        kb = audio_buf.total_bytes() / 1024
        print(f"\r{colors.AUDIO} buffering… {kb:.1f} kB", end="", flush=True)
        return

    # ── Hall sensor change from bar ESP32 ─────────────────────────────────────
    if topic == config.TOPIC_HALL:
        # 1-byte signed int: sensor index, -1 = no magnet
        if len(payload) >= 1:
            hall_idx = struct.unpack("b", payload[:1])[0]
            game_state.update(hall_sensor=hall_idx)
            label = f"A{hall_idx}" if hall_idx >= 0 else "none"
            print(f"\n{colors.HALL} sensor={label}")
            _publish_game_state(client)
        return

    # ── Gesture event from glove ───────────────────────────────────────────────
    if topic == config.TOPIC_GESTURE:
        try:
            import json
            data    = json.loads(payload)
            gesture = str(data.get("gesture", "unknown"))
            conf    = float(data.get("confidence", 0.0))
            game_state.update(last_gesture=gesture)
            print(f"\n{colors.GESTURE} gesture={gesture} conf={conf:.2f}")
            _publish_game_state(client)
        except Exception as e:
            print(f"\n{colors.ERROR} bad gesture payload: {e}")
        return

    # ── Game engine output → forward to visualiser ────────────────────────────
    if topic == config.TOPIC_ENGINE_OUTPUT:
        try:
            import json
            data = json.loads(payload)
            game_state.update(**data)
            print(f"\n{colors.GAME} engine output received, forwarding to visualiser")
            _publish_game_state(client)
        except Exception as e:
            print(f"\n{colors.ERROR} bad engine output payload: {e}")
        return

    # ── Recipe classification result from Ultra96 ─────────────────────────────
    if topic == config.TOPIC_ULTRA96_RECIPE_OUT:
        try:
            import json
            data   = json.loads(payload)
            recipe = str(data.get("recipe", "unknown"))
            print(f"\n{colors.RECIPE} recipe={recipe}")
            with _recipe_lock:
                global _pending_recipe
                _pending_recipe = recipe
        except Exception as e:
            print(f"\n{colors.ERROR} bad recipe payload: {e}")
        return


def on_disconnect(client, userdata, rc):
    print(f"\n{colors.ERROR} MQTT disconnected rc={rc}, reconnecting…")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _publish_game_state(client: mqtt.Client) -> None:
    payload = game_state.to_json()
    client.publish(config.TOPIC_GAME_STATE, payload, qos=0, retain=True)
 


def _send_ack(client: mqtt.Client, success: bool) -> None:
    byte = b"\x01" if success else b"\x00"
    client.publish(config.TOPIC_ACK, byte, qos=1)
    label = "ACK" if success else "NACK"
    print(f"{colors.INFO} sent {label} to bar ESP32")


def _forward_audio_to_ultra96(client: mqtt.Client, clip: bytes) -> None:
    """
    Forward a complete PCM clip to Ultra96 for recipe classification.
    Ultra96 is expected to reply on TOPIC_ULTRA96_RECIPE_OUT.
    Payload format: raw PCM bytes (int16 LE, 8 kHz mono), same as what
    the ESP32 emits.  Add framing / metadata here when the Ultra96 model
    contract is finalised.
    """
    client.publish(config.TOPIC_ULTRA96_AUDIO_IN, clip, qos=1)
    print(f"{colors.AUDIO} forwarded {len(clip)/1024:.1f} kB clip → Ultra96")


# ─────────────────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────────────────

def main():
    global _pending_recipe

    client = mqtt.Client(client_id="game_server")
    client.on_connect    = on_connect
    client.on_message    = on_message
    client.on_disconnect = on_disconnect

    client.connect(config.BROKER_HOST, config.BROKER_PORT, keepalive=60)
    client.loop_start()   # T2: paho network thread

    print(f"{colors.INFO} bARtender game server started")

    STATE_PUBLISH_INTERVAL = 0.5   # periodic heartbeat even without new events

    last_state_publish = 0.0
    pending_clip: bytes | None = None  # clip waiting for Ultra96 response

    try:
        while True:
            now = time.monotonic()

            # ── Audio clip ready? 
            if audio_buf.ready():
                print()   # newline after progress indicator
                clip = audio_buf.consume()
                print(f"{colors.AUDIO} clip complete — {len(clip)/1024:.1f} kB, forwarding to Ultra96")
                pending_clip = clip
                _forward_audio_to_ultra96(client, clip)
                # ACK will be sent once we get the recipe back (or time out)

            # ── Recipe result arrived from Ultra96? 
            with _recipe_lock:
                recipe = _pending_recipe
                _pending_recipe = None

            if recipe is not None:
                game_state.update(last_recipe=recipe)
                _publish_game_state(client)
                _send_ack(client, success=True)
                pending_clip = None

            # ── Periodic game/state heartbeat ──────────────────────────────────
            if now - last_state_publish >= STATE_PUBLISH_INTERVAL:
                _publish_game_state(client)
                last_state_publish = now

            time.sleep(0.05)

    except KeyboardInterrupt:
        print(f"\n{colors.INFO} shutting down")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
