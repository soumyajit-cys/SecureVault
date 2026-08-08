"""
Device fingerprinting from request headers.

The fingerprint is a SHA-256 digest of the
User-Agent plus the Client Hints and Accept-Language
headers when present. It is a *session* property,
not a tracking ID: it lets the server tell "same
browser, same device" apart well enough to flag
first-seen devices during login.
"""

from __future__ import annotations

import hashlib
import re

# Mozilla/5.0 (Windows NT 10.0; Win64; x64)
# AppleWebKit/537.36 (KHTML, like Gecko)
# Chrome/126.0.0.0 Safari/537.36

_OS_PATTERNS = [
    (re.compile(r"Windows NT 10\.0"), "Windows 10"),
    (re.compile(r"Windows NT 6\.3"), "Windows 8.1"),
    (re.compile(r"Windows NT 6\.1"), "Windows 7"),
    (re.compile(r"Windows"), "Windows"),
    (re.compile(r"Android (\d[\d.]*)"), "Android"),
    (re.compile(r"iPhone OS (\d[\d_]*)"), "iOS"),
    (re.compile(r"iPad.*OS (\d[\d_]*)"), "iPadOS"),
    (re.compile(r"Mac OS X (\d[\d._]*)"), "macOS"),
    (re.compile(r"CrOS"), "ChromeOS"),
    (re.compile(r"Linux"), "Linux"),
]

_BROWSER_PATTERNS = [
    (re.compile(r"Edg/"), "Edge"),
    (re.compile(r"OPR/"), "Opera"),
    (re.compile(r"Chrome/"), "Chrome"),
    (re.compile(r"Firefox/"), "Firefox"),
    (re.compile(r"Safari/"), "Safari"),
    (re.compile(r"curl/"), "curl"),
    (re.compile(r"python-requests"), "python-requests"),
]

_MOBILE_MARKERS = [
    "Mobile",
    "iPhone",
    "Android",
]

_TABLET_MARKERS = [
    "iPad",
    "Tablet",
]


def fingerprint_from_headers(
    user_agent: str | None,
    accept_language: str | None = None,
    sec_ch_ua: str | None = None,
) -> str | None:
    """
    Deterministic digest of the device-ish headers.

    Returns None when no usable header is present so
    callers can skip fingerprinting entirely.
    """

    parts = [
        part
        for part in [
            user_agent,
            accept_language,
            sec_ch_ua,
        ]
        if part
    ]

    if not parts:
        return None

    canonical = "\n".join(
        part.strip().lower()
        for part in parts
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def parse_device(
    user_agent: str | None,
) -> dict:
    """
    Lightweight UA parser returning a human summary.

    Kept dependency-free on purpose: the fields are
    only used for display and coarse classification.
    """

    ua = user_agent or ""

    os_name = "Unknown OS"

    for pattern, name in _OS_PATTERNS:

        if pattern.search(ua):
            os_name = name
            break

    browser = "Unknown"

    for pattern, name in _BROWSER_PATTERNS:

        if pattern.search(ua):
            browser = name
            break

    if any(
        marker in ua
        for marker in _TABLET_MARKERS
    ):
        device_type = "tablet"

    elif any(
        marker in ua
        for marker in _MOBILE_MARKERS
    ):
        device_type = "mobile"

    else:
        device_type = "desktop"

    return {
        "device_type": device_type,
        "os": os_name,
        "browser": browser,
    }


def device_name(
    user_agent: str | None,
) -> str | None:
    """
    Short human label for the sessions list.
    """

    parsed = parse_device(user_agent)

    label = (
        f"{parsed['browser']} on {parsed['os']}"
    )

    if (
        parsed["browser"] == "Unknown"
        and parsed["os"] == "Unknown OS"
    ):
        return None

    return label
