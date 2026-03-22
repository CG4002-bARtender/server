from src.mqtt_bridge import MQTTBridge
from src.game_engine import GameEngine
from src.server import Server

BROKER_HOST = "172.20.10.2"
BROKER_PORT = 1883

if __name__ == "__main__":
    bridge = MQTTBridge(BROKER_HOST, BROKER_PORT)
    engine = GameEngine()
    server = Server(bridge, engine)

    server.start()
    print(f"Server running. Connected to {BROKER_HOST}:{BROKER_PORT}")

    try:
        input("Press Enter to stop...\n")
    finally:
        server.stop()
        print("Server stopped.")
