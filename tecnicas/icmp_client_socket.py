#!/usr/bin/env python3
import time
import struct
import sys
import os
import socket

# --- Función para calcular el checksum de ICMP ---
# ICMP requiere un checksum calculado manualmente.
def calculate_checksum(data):
    checksum = 0
    # Sumar cada palabra de 16 bits
    for i in range(0, len(data), 2):
        # Manejar el último byte si la longitud es impar
        if i + 1 < len(data):
            word = (data[i] << 8) + data[i+1]
            checksum += word
        else:
            checksum += data[i] << 8
    
    # Añadir el acarreo
    while (checksum >> 16):
        checksum = (checksum & 0xFFFF) + (checksum >> 16)
    
    # Devolver el complemento a uno
    return ~checksum & 0xFFFF

# --- Configuración con Argumentos ---
if len(sys.argv) < 2:
    print("Uso: sudo python3 {} <IP_DEL_SERVIDOR> [cantidad_paquetes] [tamano_payload]".format(sys.argv[0]))
    sys.exit(1)

SERVER_IP = sys.argv[1]
PACKET_COUNT = int(sys.argv[2]) if len(sys.argv) > 2 else 10
PAYLOAD_SIZE = int(sys.argv[3]) if len(sys.argv) > 3 else 0
PACKET_INTERVAL = 0.5  # segundos
MAGIC_IDENTIFIER = b'LATENCY'
ICMP_ECHO_REQUEST = 8
ICMP_ID = os.getpid() & 0xFFFF # Usar el ID del proceso como identificador

# --- Fin de Configuración ---

# Crear un raw socket para ICMP
# Esto requiere privilegios de administrador (sudo)
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
except PermissionError:
    print("Error: Se requieren privilegios de administrador (sudo) para crear un raw socket.")
    sys.exit(1)

basura = os.urandom(PAYLOAD_SIZE)

print("Enviando {} paquetes de prueba a {}".format(PACKET_COUNT, SERVER_IP))
print("Payload extra por paquete: {} bytes".format(PAYLOAD_SIZE))
print("-" * 30)

for i in range(PACKET_COUNT):
    t_sent = time.time()
    
    # 1. Construir el payload personalizado (igual que antes)
    control_data = struct.pack('!Id', i, t_sent)
    custom_payload = MAGIC_IDENTIFIER + control_data + basura

    # 2. Construir una cabecera ICMP temporal (checksum en 0)
    # Formato: !BBHHH -> Type, Code, Checksum, ID, Sequence
    temp_header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, 0, ICMP_ID, i)
    
    # 3. Calcular el checksum sobre la cabecera temporal y el payload
    checksum = calculate_checksum(temp_header + custom_payload)
    
    # 4. Construir la cabecera ICMP final con el checksum correcto
    icmp_header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, checksum, ICMP_ID, i)

    # 5. Unir la cabecera y el payload para formar el paquete completo
    packet = icmp_header + custom_payload
    
    # 6. Enviar el paquete. El kernel añadirá la cabecera IP por nosotros.
    # El puerto es irrelevante para ICMP pero la tupla es necesaria.
    s.sendto(packet, (SERVER_IP, 0))
    print("Paquete {}/{} enviado (tamano payload: {} bytes)".format(i+1, PACKET_COUNT, len(custom_payload)))

    time.sleep(PACKET_INTERVAL)

print("-" * 30)
print("Prueba finalizada.")
s.close()