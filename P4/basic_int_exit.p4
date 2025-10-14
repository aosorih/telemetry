// SPDX-License-Identifier: Apache-2.0
/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

#define ETHERTYPE_TELEMETRY 0x88B9
#define REPORT_MIRROR_SESSION_ID 1
#define NORMAL_PACKET 0
#define PKT_INSTANCE_TYPE_EGRESS_CLONE 2
#define ETHERNET_HS 14 

const bit<48> DST_MAC_MIRROR = 0x525400a8766b;
const bit<16> TYPE_IPV4 = 0x800;
const bit<8>  TYPE_UDP  = 0x11;
/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> length;
    bit<16> checksum;
}

#define REPORT_HS 16  // bytes
header telemetry_t {
    bit<48> ingress_timestamp;
    bit<48> egress_timestamp;
    bit<32> packet_size;
}

struct metadata {
    @field_list(1) 
    bit<48> ingress_time_sw1;
    bit<48> egress_time;
    bit<32> packet_size;
}

struct headers {
    ethernet_t   ethernet;
    ipv4_t       ipv4;
    udp_t        udp;
    telemetry_t telemetry;
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        // === 3. MODIFICAR PARSER PARA QUE RECONOZCA UDP ===
        transition select(hdr.ipv4.protocol) {
            TYPE_UDP: parse_udp;
            default: accept; // Otros protocolos (como ICMP) se aceptan sin parsear L4
        }
    }

    // MODIFICACIÓN 1: El parser ahora busca el encabezado de telemetría después de UDP.
    state parse_udp {
        packet.extract(hdr.udp);
        transition parse_telemetry; // En lugar de 'accept', vamos al siguiente estado.
    }

    // MODIFICACIÓN 2: Nuevo estado para extraer el encabezado de telemetría.
    state parse_telemetry {
        packet.extract(hdr.telemetry);
        transition accept;
    }
}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
    action drop() {
        mark_to_drop(standard_metadata);
    }

    action ipv4_forward(egressSpec_t port) {
        standard_metadata.egress_spec = port;
        meta.packet_size = standard_metadata.packet_length;       
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }

    apply {
        if (hdr.ipv4.isValid()) {
            if(hdr.telemetry.isValid()){
                meta.ingress_time_sw1 = hdr.telemetry.ingress_timestamp;
                // Opcional: registrar el valor leído para depuración.
                log_msg("TELEMETRY_READ: time_ingress_sw1: {}", {meta.ingress_time_sw1});
            }
            ipv4_lpm.apply();
        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply {  
        if (standard_metadata.instance_type == PKT_INSTANCE_TYPE_EGRESS_CLONE) {
            hdr.ipv4.setInvalid();
            hdr.udp.setInvalid();
            hdr.telemetry.setValid();
            hdr.ethernet.etherType = ETHERTYPE_TELEMETRY;
            hdr.ethernet.dstAddr = DST_MAC_MIRROR;
            hdr.telemetry.ingress_timestamp = meta.ingress_time_sw1;
            hdr.telemetry.egress_timestamp = standard_metadata.egress_global_timestamp;
            hdr.telemetry.packet_size = meta.packet_size;
            log_msg("TELEMETRY: time_ingress: {}, time_egress: {}, packet_size: {}", {meta.ingress_time, standard_metadata.egress_global_timestamp, meta.packet_size});
            truncate(ETHERNET_HS + REPORT_HS);
        } else {
            //version vieja P4
            clone3<metadata>(CloneType.E2E, REPORT_MIRROR_SESSION_ID, meta);
            //version nueva P4
            //clone_preserving_field_list(CloneType.E2E, REPORT_MIRROR_SESSION_ID, 1);
            hdr.telemetry.setInvalid();
        }        
    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
     apply {
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.udp);
        packet.emit(hdr.telemetry);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;