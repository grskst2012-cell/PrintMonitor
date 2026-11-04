
import socket
import time
import threading

from discovery import discover_printer

PRINTER_PORT = 8899
CHECK_INTERVAL = 30

printer_ip = None
printer_name = None
last_check = 0

discovery_lock = threading.Lock()


def send_command(ip: str, command: str) -> str:
    try:
        with socket.create_connection(
            (ip, PRINTER_PORT),
            timeout=3
        ) as sock:

            sock.settimeout(2)
            sock.sendall(f"~{command}\r\n".encode())

            response = b""

            while len(response) < 8192:
                try:
                    chunk = sock.recv(4096)

                    if not chunk:
                        break

                    response += chunk

                    if b"\nok\r\n" in response:
                        break

                except socket.timeout:
                    break

            return response.decode(
                "utf-8",
                errors="replace"
            ).strip()

    except OSError as error:
        return f"Connection error: {error}"


def find_printer(force=False):
    global printer_ip, printer_name, last_check

    with discovery_lock:
        now = time.monotonic()

        # Проверяем сохранённый адрес не чаще раза в 30 секунд
        if printer_ip and not force:
            if now - last_check < CHECK_INTERVAL:
                return printer_ip

            last_check = now

            response = send_command(printer_ip, "M105")

            if "Connection error:" not in response and response:
                return printer_ip

            print("Printer connection lost. Searching again...")

        print("Discovering FlashForge printer...")

        printer = discover_printer()

        last_check = time.monotonic()

        if printer:
            printer_ip = printer["ip"]
            printer_name = printer.get(
                "name",
                "FlashForge Adventurer 4"
            )

            print(f"Printer connected: {printer_ip}")
            return printer_ip

        printer_ip = None
        printer_name = None

        print("Printer not found.")
        return None


def get_status():
    ip = find_printer()

    if not ip:
        return {
            "connected": False,
            "printer": None,
            "temperatures": "Printer not found",
            "machine": "Printer not found",
            "progress": "Printer not found"
        }

    temperatures = send_command(ip, "M105")

    # Если соединение оборвалось, пробуем найти принтер заново
    if "Connection error:" in temperatures:
        ip = find_printer(force=True)

        if not ip:
            return {
                "connected": False,
                "printer": None,
                "temperatures": "Connection lost",
                "machine": "Connection lost",
                "progress": "Connection lost"
            }

        temperatures = send_command(ip, "M105")

    return {
        "connected": True,
        "printer": {
            "name": printer_name,
            "ip": ip,
            "port": PRINTER_PORT
        },
        "temperatures": temperatures,
        "machine": send_command(ip, "M119"),
        "progress": send_command(ip, "M27")
    }
