"""Unit tests for guards and string utilities."""

import pytest
from utils.helpers import is_safe_url, sanitise_domain, validate_company_name


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("example.com", "example.com"),  # bare domain
        ("HTTPS://EX.COM", "ex.com"),  # uppercase + protocol stripped
        ("  spaces.net  ", "spaces.net"),  # surrounding whitespace stripped
        ("docs.google.com", "docs.google.com"),  # subdomain passes
        ("https://example.com/some/path", "example.com"),  # path stripped
    ],
)
def test_sanitise_domain_valid(raw: str, expected: str) -> None:
    assert sanitise_domain(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "192.168.1.1",  # bare IP rejected
        "not a domain",  # spaces in middle rejected
        "",  # empty string rejected
    ],
)
def test_sanitise_domain_invalid(raw: str) -> None:
    with pytest.raises(ValueError):
        sanitise_domain(raw)


@pytest.mark.parametrize(
    "url, safe",
    [
        ("https://example.com/api", True),  # normal external URL
        ("http://example.com", False),  # non-HTTPS blocked
        ("https://127.0.0.1", False),  # loopback blocked
        ("https://169.254.169.254", False),  # metadata blocked
        ("https://10.0.0.1", False),  # private range blocked
        ("https://192.168.1.1", False),  # private range blocked
    ],
)
def test_is_safe_url(url: str, safe: bool) -> None:
    assert is_safe_url(url) == safe


def test_validate_company_name_valid() -> None:
    assert validate_company_name("Nike") == "Nike"


def test_validate_company_name_strips_control_chars() -> None:
    assert validate_company_name("Nik\x00e") == "Nike"


def test_validate_company_name_only_control_chars() -> None:
    with pytest.raises(ValueError):
        validate_company_name("\x00\x01\x1f")


def test_validate_company_name_blank() -> None:
    with pytest.raises(ValueError):
        validate_company_name("   ")


def test_validate_company_name_too_long() -> None:
    with pytest.raises(ValueError):
        validate_company_name("A" * 121)
