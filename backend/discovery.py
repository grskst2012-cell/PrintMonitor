import socket
import struct
import time
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed

# Определяем адрес сетевого интерфейса автоматически.
# UDP connect здесь не отправляет данные на внешний сервер:
# он используется ОС только для выбора локального интерфейса.
def get_local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()


MULTICAST_GROUP = "225.0.0.9"
DISCOVERY_PORT = 8899
PRINTER_TCP_PORT = 8899


def get_local_network():
    local_ip = get_local_ip()
    if not local_ip:
        return None, None

    # Пока используется типичная маска домашней сети /24.
    # При необходимости поддержку других масок можно добавить отдельно.
    network = ipaddress.ip_network(f"{local_ip}/24", strict=False)
    return local_ip, network


def parse_packet(packet, address):
    if len(packet) != 140:
        return None

    name = packet[:128].split(b"\x00", 1)[0]
    name = name.decode("utf-8", errors="replace").strip()

    tcp_port = int.from_bytes(packet[132:134], "big")
    vendor_id = int.from_bytes(packet[134:136], "big")
    product_id = int.from_bytes(packet[136:138], "big")

    if tcp_port != PRINTER_TCP_PORT or vendor_id != 0x2B71:
        return None

    return {
        "ip": address[0],
        "name": name or "FlashForge",
        "port": tcp_port,
        "product_id": hex(product_id),
        "method": "multicast"
    }


def discover_multicast(timeout=3):
    local_ip = get_local_ip()
    if not local_ip:
        print("Cannot determine the active network interface.")
        return None

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", DISCOVERY_PORT))

        interface = socket.inet_aton(local_ip)

        membership = struct.pack(
            "4s4s",
            socket.inet_aton(MULTICAST_GROUP),
            interface
        )

        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            membership
        )

        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            interface
        )

        sock.sendto(b"\x00", (MULTICAST_GROUP, DISCOVERY_PORT))

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            sock.settimeout(max(0.1, deadline - time.monotonic()))

            try:
                packet, address = sock.recvfrom(2048)
            except socket.timeout:
                break

            printer = parse_packet(packet, address)

            if printer:
                return printer

    except OSError as error:
        print(f"Multicast error: {error}")

    finally:
        sock.close()

    return None


def check_ip(ip):
    try:
        with socket.create_connection(
            (str(ip), PRINTER_TCP_PORT),
            timeout=0.4
        ) as sock:

            sock.settimeout(1.0)
            sock.sendall(b"~M105\r\n")

            response = b""

            while len(response) < 4096:
                try:
                    chunk = sock.recv(2048)
                    if not chunk:
                        break

                    response += chunk

                    if b"ok" in response.lower():
                        break

                except socket.timeout:
                    break

            decoded = response.decode("utf-8", errors="replace")

            if "M105 Received" in decoded or "T0:" in decoded:
                return {
                    "ip": str(ip),
                    "name": "FlashForge printer",
                    "port": PRINTER_TCP_PORT,
                    "method": "network_scan"
                }

    except OSError:
        pass

    return None


def discover_by_scan():
    local_ip, network = get_local_network()

    if not local_ip or not network:
        print("Cannot determine the local network. Network scan skipped.")
        return None

    print(f"Scanning local network {network}...")

    with ThreadPoolExecutor(max_workers=64) as executor:
        futures = [
            executor.submit(check_ip, ip)
            for ip in network.hosts()
        ]

        for future in as_completed(futures):
            printer = future.result()

            if printer:
                return printer

    return None


def discover_printer():
    print("Searching via multicast...")

    printer = discover_multicast()

    if printer:
        return printer

    print("Multicast did not find printer.")
    print("Starting network scan...")

    return discover_by_scan()


if __name__ == "__main__":
    printer = discover_printer()

    if printer:
        print("\nPrinter found!")
        for key, value in printer.items():
            print(f"{key}: {value}")
    else:
        print("\nFlashForge printer not found.")
