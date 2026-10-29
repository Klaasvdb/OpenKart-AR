"""First look at an unknown FPV car: which ports are open, is there a video stream?

Connect this computer to the car's Wi-Fi first, then:
    python tools/probe_car.py 192.168.0.1

Only the TCP side can be scanned; UDP control ports have to come from a
packet capture of the original app (see docs/HARDWARE.md).
"""

from __future__ import annotations

import argparse
import socket
import urllib.request

COMMON_TCP_PORTS = [80, 554, 7060, 8080, 8081, 8888, 9000, 6666, 7070, 5000]
HTTP_PATHS = ["/", "/?action=stream", "/video", "/stream", "/live", "/mjpeg", "/cgi-bin/stream"]


def open_tcp_ports(host: str, ports: list[int], timeout: float) -> list[int]:
    found = []
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            if s.connect_ex((host, port)) == 0:
                found.append(port)
    return found


def probe_http(host: str, port: int, timeout: float) -> None:
    for path in HTTP_PATHS:
        url = f"http://{host}:{port}{path}"
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                ctype = resp.headers.get("Content-Type", "?")
                head = resp.read(64)
                print(f"    {url} → {resp.status} {ctype} {head[:32]!r}")
        except Exception as exc:  # noqa: BLE001 - we just report everything
            print(f"    {url} → {type(exc).__name__}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("host", help="IP of the car, often 192.168.0.1 or 192.168.1.1")
    parser.add_argument("--timeout", type=float, default=0.8)
    args = parser.parse_args()

    print(f"TCP-poorten scannen op {args.host} …")
    ports = open_tcp_ports(args.host, COMMON_TCP_PORTS, args.timeout)
    print(f"  open: {ports or 'geen'}")
    for port in ports:
        if port == 554:
            print(f"  RTSP? probeer: ffplay rtsp://{args.host}:554/")
        else:
            print(f"  HTTP op {port}:")
            probe_http(args.host, port, args.timeout)


if __name__ == "__main__":
    main()
