#!/usr/bin/env python3
import socket
import struct
import time
import sys
import os

# --- Configuracion con Argumentos ---

# 1. Validar argumento de IP (obligatorio)
if len(sys.argv) < 2:
    # Mensaje de uso actualizado para incluir el nuevo argumento
    print("Uso: python3 {} <IP_DEL_SERVIDOR> [cantidad_paquetes] [tamano_payload]".format(sys.argv[0]))
    print("Ejemplo: python3 {} 192.168.1.1 50 100".format(sys.argv[0]))
    sys.exit(1)

SERVER_IP = sys.argv[1]
SERVER_PORT = 12345

# 2. Leer argumentos opcionales o usar valores por defecto
#    El segundo argumento sera la cantidad de paquetes, el tercero el tamano.
PACKET_COUNT = int(sys.argv[2]) if len(sys.argv) > 2 else 20
PAYLOAD_SIZE = int(sys.argv[3]) if len(sys.argv) > 3 else 0
PACKET_INTERVAL = 0.5  # segundos
# --- Fin Configuracion ---
MAGIC_IDENTIFIER = b'LATENCY'
# Crear un socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Generar el payload basura una sola vez para ser eficientes.
basura = os.urandom(PAYLOAD_SIZE)

print("Enviando {} paquetes a {}:{}".format(PACKET_COUNT, SERVER_IP, SERVER_PORT))
print("Tamano total del payload por paquete: {} bytes (12 de control + {} de basura)".format(12 + PAYLOAD_SIZE, PAYLOAD_SIZE))

for seq_num in range(PACKET_COUNT):
    t_sent = time.time()
    
    # Empaquetar los datos de control (secuencia y timestamp)
    control_data = struct.pack('!Id', seq_num, t_sent)
    
    # Unir los datos de control con el payload basura
    payload = MAGIC_IDENTIFIER + control_data + basura
    
    sock.sendto(payload, (SERVER_IP, SERVER_PORT))
    
    print("Paquete [{}] enviado (tamano total: {} bytes)".format(seq_num, len(payload)))
    
    time.sleep(PACKET_INTERVAL)

print("Prueba finalizada.")
sock.close()