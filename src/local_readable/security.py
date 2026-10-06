from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


def is_loopback_host(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        return False
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def assert_local_url(url: str) -> None:
    if not is_loopback_host(url):
        raise ValueError(f"外部ホストは禁止されています: {url}")

