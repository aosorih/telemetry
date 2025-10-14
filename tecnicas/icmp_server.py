#!/usr/bin/env python3
import time
import struct
from scapy.all import sniff, ICMP, IP

# --- Configuración ---
MAGIC_IDENTIFIER = b'LATENCY'
INTERFACE_TO_SNIFF = 'ens10' # Asegúrate de que esta sea tu interfaz correcta

# Nuevo: Definimos el formato y tamaño de nuestros datos de control
# ! = Network Byte Order, I = Unsigned Int (4 bytes), d = Double (8 bytes)
CONTROL_DATA_FORMAT = '!Id'
CONTROL_DATA_SIZE = struct.calcsize(CONTROL_DATA_FORMAT) # Esto calcula el tamaño: 4 + 8 = 12 bytes
# --- Fin Configuración ---
archivo = "datos.csv"

print("Iniciando servidor receptor de latencia ICMP...")
print("Escuchando paquetes en la interfaz {}...".format(INTERFACE_TO_SNIFF))

def process_packet(packet):
    """
    Esta función se ejecuta para cada paquete capturado.
    """
    t_arrival = time.time()

    if ICMP in packet and packet[ICMP].type == 8:
        payload = packet[ICMP].load
        
        if payload.startswith(MAGIC_IDENTIFIER):
            # Calculamos dónde empiezan y terminan nuestros datos de control
            start_of_control_data = len(MAGIC_IDENTIFIER)
            end_of_control_data = start_of_control_data + CONTROL_DATA_SIZE

            # Verificamos si el payload es lo suficientemente largo
            if len(payload) >= end_of_control_data:
                try:
                    # Extraemos la rebanada (slice) exacta de bytes que nos interesa
                    control_data_bytes = payload[start_of_control_data:end_of_control_data]
                    
                    # Desempacamos el número de secuencia y el timestamp
                    seq_num, t_sent = struct.unpack(CONTROL_DATA_FORMAT, control_data_bytes)
                    
                    latency_ms = (t_arrival - t_sent) * 1000
                    packet_size = len(payload)

                    # Mensaje de salida mejorado
                    print("Paquete [{}] recibido de {} (tamano payload: {} bytes): Latencia One-Way = {:.4f} ms".format(
                        seq_num, packet[IP].src, packet_size, latency_ms))
                    with open(archivo, "a") as f:
                        f.write("tecnica:icmp, paquete:{}, latencia:{:.4f}, payload:{}\n".format(seq_num, latency_ms, packet_size))
                except struct.error:
                    print("Error: El payload recibido tiene un formato de control incorrecto.")
            # else:
                # Opcional: Descomentar si quieres un mensaje para paquetes cortos
                # print("Paquete de {} demasiado corto para ser procesado.".format(packet[IP].src))


try:
    sniff(filter="icmp", iface=INTERFACE_TO_SNIFF, prn=process_packet, store=0)
except Exception as e:
    print("Error al iniciar el sniffer: {}".format(e))
    print("Asegurate de ejecutar con 'sudo' y que la interfaz '{}' sea correcta.".format(INTERFACE_TO_SNIFF))