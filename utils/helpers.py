"""Guards, logging setup, and string utilities."""

import ipaddress
import logging
import re
import socket
import sys
from urllib.parse import urlparse

# Patterns
DOMAIN_RE = re.compile(r"^(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$")


def configure_logging(level: str = "INFO") -> None:
    """Configure stdout logging levels and silence noisy external modules."""
    logging.basicConfig(
        level=level.upper(),
        format="%(levelname)-8s | %(message)s",
        stream=sys.stdout,
    )
    for lib in ("httpx", "httpcore", "openai", "tavily"):
        logging.getLogger(lib).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a standard library logger aligned with the global configuration."""
    return logging.getLogger(name)


def validate_company_name(name: str) -> str:
    """Clean unprintable characters and validate the strict length of the company seed."""
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", name).strip()
    if not cleaned or len(cleaned) > 120:
        raise ValueError("Company name must be 1-120 safe characters.")
    return cleaned


def sanitise_domain(raw: str) -> str:
    """Extract and validate cleanly formed domains against RFC 1123."""
    normalised = raw.strip()
    if "://" not in normalised:
        normalised = f"https://{normalised}"
    host = (urlparse(normalised).hostname or "").lower()
    if not host or not DOMAIN_RE.match(host):
        raise ValueError(f"Invalid domain: {raw!r}")
    return host


def is_safe_url(url: str) -> bool:
    """Block loopback/private IPs to prevent SSRF using native Python properties."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    host = parsed.hostname or ""
    try:
        addr = ipaddress.ip_address(socket.gethostbyname(host))
        return not (addr.is_private or addr.is_loopback or addr.is_link_local)
    except (socket.gaierror, ValueError):
        return True
