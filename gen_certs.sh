#!/bin/bash
# certs/     — non-ESP devices (game_engine, ultra96, unity) on port 8883
#              broker cert has SAN (IP + mDNS hostname)
# esp_certs/ — ESP devices (bar, glove) on port 8885
#              broker cert has CN=bARtender.local, no SAN (mbedTLS checks CN only)

BROKER_IP="172.20.10.2"
BROKER_HOSTNAME="bARtender.local"

mkdir -p certs esp_certs

# =============================================================================
# certs/ — non-ESP devices
# =============================================================================
echo "=== Generating certs/ (non-ESP) ==="

openssl genrsa -out certs/ca.key 2048
openssl req -x509 -new -nodes -key certs/ca.key -days 3650 -out certs/ca.crt -sha256 \
  -subj "/CN=bARtender-CA"

openssl genrsa -out certs/broker.key 2048
openssl req -new -key certs/broker.key -out certs/broker.csr -subj "/CN=broker"
cat > /tmp/broker_ext.cnf <<EOF
[ext]
subjectAltName=IP:${BROKER_IP},IP:127.0.0.1,DNS:localhost,DNS:${BROKER_HOSTNAME}
extendedKeyUsage=serverAuth
EOF
openssl x509 -req -in certs/broker.csr -CA certs/ca.crt -CAkey certs/ca.key \
  -CAcreateserial -out certs/broker.crt -days 365 -sha256 \
  -extfile /tmp/broker_ext.cnf -extensions ext
rm /tmp/broker_ext.cnf certs/broker.csr

for DEVICE in game_engine ultra96 unity; do
  openssl genrsa -out certs/${DEVICE}.key 2048
  openssl req -new -key certs/${DEVICE}.key -out certs/${DEVICE}.csr -subj "/CN=${DEVICE}"
  openssl x509 -req -in certs/${DEVICE}.csr -CA certs/ca.crt -CAkey certs/ca.key \
    -CAcreateserial -out certs/${DEVICE}.crt -days 365 -sha256
  rm certs/${DEVICE}.csr
  echo "  Generated: ${DEVICE}.crt"
done

# =============================================================================
# esp_certs/ — ESP devices
# =============================================================================
echo "=== Generating esp_certs/ (ESP) ==="

openssl genrsa -out esp_certs/ca.key 2048
openssl req -x509 -new -nodes -key esp_certs/ca.key -days 3650 -out esp_certs/ca.crt -sha256 \
  -subj "/CN=bARtender-ESP"

# CN=IP, no SAN — mbedTLS checks CN against the IP it connects to
openssl genrsa -out esp_certs/broker.key 2048
openssl req -new -key esp_certs/broker.key -out esp_certs/broker.csr \
  -subj "/CN=${BROKER_IP}"
openssl x509 -req -in esp_certs/broker.csr -CA esp_certs/ca.crt -CAkey esp_certs/ca.key \
  -CAcreateserial -out esp_certs/broker.crt -days 365 -sha256
rm esp_certs/broker.csr

for DEVICE in bar glove; do
  openssl genrsa -out esp_certs/${DEVICE}.key 2048
  openssl req -new -key esp_certs/${DEVICE}.key -out esp_certs/${DEVICE}.csr -subj "/CN=${DEVICE}"
  openssl x509 -req -in esp_certs/${DEVICE}.csr -CA esp_certs/ca.crt -CAkey esp_certs/ca.key \
    -CAcreateserial -out esp_certs/${DEVICE}.crt -days 365 -sha256
  rm esp_certs/${DEVICE}.csr
  echo "  Generated: ${DEVICE}.crt"
done

echo ""
echo "Done!"
echo "  certs/     ca.crt, broker.crt (SAN: IP:${BROKER_IP}, DNS:${BROKER_HOSTNAME}), game_engine/ultra96/unity certs"
echo "  esp_certs/ ca.crt, broker.crt (CN:${BROKER_HOSTNAME}), bar/glove certs"
