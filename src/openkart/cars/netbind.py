"""Sockets bound to one Wi-Fi interface.

All cars usually share the same IP (e.g. 192.168.0.1), each behind its own USB
Wi-Fi dongle. A normal socket would pick one route for all of them, so we bind
each car's sockets to its dongle with SO_BINDTODEVICE (Linux only; may need
CAP_NET_RAW: `sudo setcap cap_net_raw+ep $(readlink -f $(which python))`).

If that turns out unreliable, the fallback is one network namespace per dongle.
"""

from __future__ import annotations

import socket


def udp_socket(interface: str | None, local_port: int = 0) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if interface:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, interface.encode() + b"\0")
    sock.bind(("0.0.0.0", local_port))
    return sock


def tcp_connect(interface: str | None, host: str, port: int, timeout: float = 3.0) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if interface:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, interface.encode() + b"\0")
    sock.settimeout(timeout)
    sock.connect((host, port))
    return sock
