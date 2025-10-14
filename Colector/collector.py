from scapy.all import *
import argparse
import struct
from datetime import datetime

def parse_telemetry(payload, offset=0):
    """Parsea telemetría desde un offset específico (48+48+32 bits = 16 bytes)"""
    try:
        start = offset
        end = offset + 16
        
        if len(payload) < end:
            return None

        # Extraer los 12 bytes relevantes
        telemetry_data = payload[start:end]

        # Dividir los bytes
        ingress_bytes = telemetry_data[:6]      # Primeros 6 bytes (48 bits)
        egress_bytes = telemetry_data[6:12]     # Siguientes 6 bytes (48 bits)
        packet_size_bytes = telemetry_data[12:16]  # Últimos 4 bytes (32 bits)
        # Convertir a enteros (big-endian)
        ingress_time = int.from_bytes(ingress_bytes, byteorder='big')
        egress_time = int.from_bytes(egress_bytes, byteorder='big')
        packet_size = int.from_bytes(packet_size_bytes, byteorder='big')
        return {
            'ingress_time': ingress_time,
            'egress_time': egress_time,
            'packet_size': packet_size,
            'ingress_hex': ingress_bytes.hex(),
            'egress_hex': egress_bytes.hex(),
            'raw_bytes': telemetry_data.hex()  # Para depuración
        }
    except Exception as e:
        print("Error parsing telemetry: ",{e})
        return None

def packet_handler(pkt, offset=0):
    """Procesa paquetes con offset personalizado"""
    archivo = "datos.txt"
    seq_num = 0
    if Ether in pkt:
        eth = pkt[Ether]
        payload = bytes(eth.payload)
        
        print("\n[+] Paquete capturado (EtherType: 0x{:04x}):".format(eth.type))
        
        telemetry = parse_telemetry(payload, offset)
        if telemetry:
            print("\n[!] Telemetría detectada:")
            latencia = telemetry['egress_time'] - telemetry['ingress_time']
            packet_size = telemetry['packet_size']
            print("Latencia microseg: ",latencia)
            with open(archivo, "a") as f:
                f.write("tecnica:int, paquete:{}, latencia:{:.4f}, payload:{}\n".format(seq_num+1, latencia, packet_size))
        else:
            print("No se detectó estructura de telemetría")

def main():
    parser = argparse.ArgumentParser(description='Sniffer avanzado para telemetría')
    parser.add_argument('-i', '--interface', required=True, help='Interfaz de red')
    parser.add_argument('-o', '--offset', type=int, default=0,
                       help='Offset en bytes donde empieza la telemetría')
    
    args = parser.parse_args()
    
    print(f"\n[+] Iniciando captura en {args.interface}")
    filter_string = "ether dst 52:54:00:9b:95:c8 and ether src 00:21:c1:24:90:a0 and ether proto 0x88b9"
    sniff(
	filter=filter_string,
        iface=args.interface,
        prn=lambda x: packet_handler(x, args.offset),
        store=0
    )

if __name__ == "__main__":
    main()