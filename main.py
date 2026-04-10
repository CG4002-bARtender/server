from src.mqtt_bridge import MQTTBridge
from src.game_engine import GameEngine
from src.server import Server
from config import BROKER_HOST, BROKER_PORT, TLS_BROKER_PORT, CERTS_DIR, TLS_ENABLED

def main():
    if TLS_ENABLED:
        bridge = MQTTBridge(BROKER_HOST, TLS_BROKER_PORT,
                            ca_cert=f"{CERTS_DIR}/ca.crt",
                            client_cert=f"{CERTS_DIR}/game_engine.crt",
                            client_key=f"{CERTS_DIR}/game_engine.key")
    else:
        bridge = MQTTBridge(BROKER_HOST, BROKER_PORT)
    engine = GameEngine()
    server = Server(bridge, engine)
    
    server.start()
    print(f"Server running. Connected to {BROKER_HOST}:{TLS_BROKER_PORT if TLS_ENABLED else BROKER_PORT}")


    try:
        input("Press Enter to stop the server...\n")
    except KeyboardInterrupt:       
        pass

if __name__ == "__main__":
    main()
