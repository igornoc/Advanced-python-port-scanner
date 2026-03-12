import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

COMMON_PORTS = {
    20: "FTP-Data",
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    67: "DHCP",
    68: "DHCP",
    69: "TFTP",
    80: "HTTP",
    110: "POP3",
    119: "NNTP",
    123: "NTP",
    135: "RPC",
    137: "NetBIOS-NS",
    138: "NetBIOS-DGM",
    139: "NetBIOS-SSN",
    143: "IMAP",
    161: "SNMP",
    179: "BGP",
    389: "LDAP",
    443: "HTTPS",
    445: "SMB",
    465: "SMTPS",
    514: "Syslog",
    587: "SMTP Submission",
    636: "LDAPS",
    993: "IMAPS",
    995: "POP3S",
    1433: "MSSQL",
    1521: "Oracle DB",
    1723: "PPTP",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    6379: "Redis",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt",
}

DEFAULT_TIMEOUT = 0.7
MAX_WORKERS = 100
BANNER_PORTS = {21, 22, 25, 110, 143, 443, 587, 993, 995}


class Color:
    RESET = "\033[0m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"


def supports_ansi() -> bool:
    return True


def c(text: str, color: str) -> str:
    return f"{color}{text}{Color.RESET}" if supports_ansi() else text


def resolve_target(target: str) -> str | None:
    try:
        return socket.gethostbyname(target)
    except socket.gaierror:
        return None


def grab_banner(sock: socket.socket, port: int) -> str:
    try:
        if port in {80, 8080, 8000, 8888}:
            sock.sendall(b"HEAD / HTTP/1.0\r\nHost: target\r\n\r\n")
        elif port in {21, 25, 110, 143, 587, 993, 995}:
            pass
        else:
            return "N/A"

        banner = sock.recv(1024).decode(errors="ignore").strip()
        return banner[:80] if banner else "No banner"
    except Exception:
        return "No banner"


def scan_port(target_ip: str, port: int, timeout: float) -> tuple[int, str, str] | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((target_ip, port))
            if result == 0:
                service = COMMON_PORTS.get(port, "Unknown")
                banner = "N/A"
                if port in BANNER_PORTS or port in {80, 8080, 8000, 8888}:
                    banner = grab_banner(sock, port)
                return port, service, banner
    except socket.error:
        return None
    return None


def get_port_range() -> tuple[int, int]:
    print("Enter port range to scan.")
    start_input = input("Start port [default 1]: ").strip()
    end_input = input("End port [default 1024]: ").strip()

    start_port = int(start_input) if start_input else 1
    end_port = int(end_input) if end_input else 1024

    if start_port < 1 or end_port > 65535 or start_port > end_port:
        raise ValueError("Invalid port range. Ports must be between 1 and 65535.")
    return start_port, end_port


def get_timeout() -> float:
    timeout_input = input(f"Timeout in seconds [default {DEFAULT_TIMEOUT}]: ").strip()
    timeout = float(timeout_input) if timeout_input else DEFAULT_TIMEOUT
    if timeout <= 0:
        raise ValueError("Timeout must be greater than 0.")
    return timeout


def print_header() -> None:
    print(c("=" * 72, Color.BLUE))
    print(c("                 ADVANCED PYTHON PORT SCANNER", Color.BOLD + Color.CYAN))
    print(c("=" * 72, Color.BLUE))


def main() -> None:
    print_header()

    target = input("Enter target IP or domain: ").strip()
    if not target:
        print(c("No target provided. Exiting.", Color.RED))
        return

    target_ip = resolve_target(target)
    if not target_ip:
        print(c("Error: Hostname could not be resolved.", Color.RED))
        return

    try:
        start_port, end_port = get_port_range()
        timeout = get_timeout()
    except ValueError as e:
        print(c(f"Error: {e}", Color.RED))
        return

    start_time = datetime.now()

    print()
    print(c(f"Target:      {target} ({target_ip})", Color.CYAN))
    print(c(f"Port range:  {start_port}-{end_port}", Color.CYAN))
    print(c(f"Timeout:     {timeout}s", Color.CYAN))
    print(c(f"Started at:  {start_time}", Color.CYAN))
    print()

    open_ports: list[tuple[int, str, str]] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(scan_port, target_ip, port, timeout): port
            for port in range(start_port, end_port + 1)
        }

        for future in as_completed(futures):
            result = future.result()
            if result:
                open_ports.append(result)
                port, service, banner = result
                print(c(f"[OPEN] Port {port:<5} Service: {service}", Color.GREEN))
                if banner not in {"N/A", "No banner"}:
                    print(c(f"       Banner: {banner}", Color.YELLOW))

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    open_ports.sort(key=lambda x: x[0])

    print()
    print(c("-" * 72, Color.BLUE))
    print(c("SCAN SUMMARY", Color.BOLD + Color.CYAN))
    print(c("-" * 72, Color.BLUE))

    if open_ports:
        for port, service, banner in open_ports:
            print(f"Port {port:<5} | Service: {service:<15} | Banner: {banner}")
    else:
        print("No open ports found in the selected range.")

    print()
    print(c(f"Total open ports: {len(open_ports)}", Color.CYAN))
    print(c(f"Completed at:     {end_time}", Color.CYAN))
    print(c(f"Duration:         {duration:.2f} seconds", Color.CYAN))
    print(c("-" * 72, Color.BLUE))


if __name__ == "__main__":
    main()