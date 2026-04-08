from src.mqtt_bridge import MQTTBridge
from src.game_engine import GameEngine
from src.server import Server

BROKER_HOST = "localhost"
BROKER_PORT = 8883

if __name__ == "__main__":
    bridge = MQTTBridge(BROKER_HOST, BROKER_PORT,
                        ca_cert="certs/ca.crt",
                        client_cert="certs/game_engine.crt",
                        client_key="certs/game_engine.key")
    engine = GameEngine()
    server = Server(bridge, engine)

    server.start()
    print(f"Server running. Connected to {BROKER_HOST}:{BROKER_PORT}")

    try:
        input("Press Enter to stop the server...\n")
    except KeyboardInterrupt:       
        pass