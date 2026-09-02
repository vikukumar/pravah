"""
PRAVAH SSRF-Safe HTTP Utilities
==================================
Protects against Server-Side Request Forgery (SSRF) for the HTTP Request node.

Blocked address spaces (per PRD §43):
  - Loopback:         127.0.0.0/8
  - Private A:        10.0.0.0/8
  - Private B:        172.16.0.0/12
  - Private C:        192.168.0.0/16
  - Link-local:       169.254.0.0/16  (includes AWS metadata 169.254.169.254)
  - IPv6 loopback:    ::1
  - IPv6 link-local:  fe80::/10
  - IPv6 ULA:         fc00::/7

Admin can configure explicit allowlist overrides for trusted internal services.
"""

import ipaddress
import socket
from typing import Optional
from urllib.parse import urlparse

# SSRF-blocked IP network ranges
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("10.0.0.0/8"),        # Private A
    ipaddress.ip_network("172.16.0.0/12"),     # Private B
    ipaddress.ip_network("192.168.0.0/16"),    # Private C
    ipaddress.ip_network("169.254.0.0/16"),    # Link-local (AWS metadata endpoint)
    ipaddress.ip_network("0.0.0.0/8"),         # IANA reserved
    ipaddress.ip_network("100.64.0.0/10"),     # CGNAT
    ipaddress.ip_network("198.18.0.0/15"),     # Benchmark testing
    ipaddress.ip_network("240.0.0.0/4"),       # Reserved future use
    ipaddress.ip_network("::1/128"),            # IPv6 loopback
    ipaddress.ip_network("fe80::/10"),          # IPv6 link-local
    ipaddress.ip_network("fc00::/7"),           # IPv6 ULA
]

# Blocked hostnames (always blocked regardless of resolution)
_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata",
    "instance-data",
}


class SSRFViolationError(Exception):
    """Raised when a request URL would result in an SSRF vulnerability."""
    pass


def validate_url_safe(url: str, allowlist: Optional[list] = None) -> None:
    """
    Validate that a URL is safe to request (not targeting private/internal networks).

    Args:
        url:       The URL to validate
        allowlist: Optional list of trusted hostnames/CIDRs that bypass the block

    Raises:
        SSRFViolationError: If the URL targets a blocked internal network
        ValueError:         If the URL is malformed
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    parsed = urlparse(url)

    # Must be HTTP/HTTPS
    if parsed.scheme not in ("http", "https"):
        raise SSRFViolationError(
            f"URL scheme '{parsed.scheme}' is not allowed. Only http and https are permitted."
        )

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must contain a valid hostname")

    hostname = hostname.lower().strip(".")

    # Check against blocked hostnames
    if hostname in _BLOCKED_HOSTNAMES:
        raise SSRFViolationError(
            f"Hostname '{hostname}' is not allowed for security reasons."
        )

    # Check allowlist bypass
    if allowlist and hostname in allowlist:
        return

    # Resolve hostname to IP(s) and check each
    try:
        addr_infos = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        raise SSRFViolationError(
            f"Could not resolve hostname '{hostname}'. Request blocked for security."
        )

    for addr_info in addr_infos:
        ip_str = addr_info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
            for network in _BLOCKED_NETWORKS:
                if ip in network:
                    raise SSRFViolationError(
                        f"Request to '{hostname}' ({ip_str}) is blocked: "
                        f"target IP is within a private/reserved network range."
                    )
        except ValueError:
            continue  # Skip malformed IPs


def is_url_safe(url: str, allowlist: Optional[list] = None) -> tuple[bool, str]:
    """
    Returns (is_safe, reason) without raising an exception.
    Convenience wrapper for pre-flight checks.
    """
    try:
        validate_url_safe(url, allowlist)
        return True, "URL is safe"
    except (SSRFViolationError, ValueError) as e:
        return False, str(e)
