"""Detection helper functions shared by all verifiers."""

import re

# Compiled regex patterns for performance

_SQLI_PATTERN = re.compile(
    r"('.*\b(OR|AND)\b.*--|"
    r"\bUNION\b.*\bSELECT\b|"
    r";\s*(DROP|ALTER|DELETE|INSERT|UPDATE)\b)",
    re.IGNORECASE,
)

_XSS_PATTERN = re.compile(
    r"(<script[\s>]|"
    r"\bon\w+\s*=|"
    r"javascript\s*:)",
    re.IGNORECASE,
)

_PATH_TRAVERSAL_PATTERN = re.compile(
    r"(\.\./|"
    r"\.\.\\|"
    r"^/etc/|"
    r"^/proc/|"
    r"^/dev/|"
    r"^/var/|"
    r"^/tmp/|"
    r"^/usr/|"
    r"^/bin/|"
    r"^/sbin/|"
    r"^/root|"
    r"^/home/|"
    r"^[A-Za-z]:\\)"
)

_DANGEROUS_EXTENSIONS = {
    ".php", ".phtml", ".php3", ".php4", ".php5",
    ".py", ".pl", ".rb", ".sh", ".bash",
    ".html", ".htm", ".xhtml",
    ".svg",
    ".jsp", ".jspx", ".asp", ".aspx",
    ".cgi", ".exe", ".bat", ".cmd", ".ps1",
    ".js", ".mjs",
}

_NORMALIZE_PATH_PATTERN = re.compile(
    r"/([0-9a-f]{8,}(-[0-9a-f]{4,}){3,}-[0-9a-f]{12,}|\d+)(?=/|$)"
)


def ensure_str(value) -> str:
    """Convert bytes to str if needed, returning empty string for None."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def has_sqli_indicators(text: str) -> bool:
    """Return True if text contains SQL injection indicators."""
    return bool(_SQLI_PATTERN.search(text))


def has_xss_indicators(text: str) -> bool:
    """Return True if text contains XSS indicators."""
    return bool(_XSS_PATTERN.search(text))


def has_path_traversal(text: str) -> bool:
    """Return True if text contains path traversal indicators."""
    return bool(_PATH_TRAVERSAL_PATTERN.search(text))


def is_dangerous_extension(filename: str) -> bool:
    """Return True if filename has a dangerous extension."""
    dot_idx = filename.rfind(".")
    if dot_idx == -1:
        return False
    ext = filename[dot_idx:].lower()
    return ext in _DANGEROUS_EXTENSIONS


def normalize_path(path: str) -> str:
    """Replace numeric and UUID path segments with {param}, preserving version strings like v1."""
    return _NORMALIZE_PATH_PATTERN.sub("/{param}", path)


def decode_jwt(token: str, secret: str):
    """Decode a JWT token. Try HS256 first, then none algorithm. Return None on failure."""
    import jwt as pyjwt

    if not token:
        return None

    # Try HS256 first
    try:
        return pyjwt.decode(token, secret, algorithms=["HS256"])
    except Exception:
        pass

    # Try none algorithm
    try:
        return pyjwt.decode(token, options={"verify_signature": False}, algorithms=["none"])
    except Exception:
        pass

    return None
