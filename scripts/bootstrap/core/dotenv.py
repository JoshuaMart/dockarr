"""Read and edit the project's .env file in place.

The bootstrap is the source of truth for optional-service choices (Kavita, VPN):
those choices are made at `make install` and stored in secrets/credentials.json.
But `make up` / `make update` run a bare `docker compose up -d` that only reads
.env, so the relevant modules mirror the choice into Compose's own variables
(COMPOSE_PROFILES, COMPOSE_FILE) here. These helpers preserve comments and
unrelated lines; core/config.py keeps its own reader for loading values into the
process environment.
"""

from pathlib import Path

ENV_PATH = Path(".env")


def _lines():
    return ENV_PATH.read_text().splitlines() if ENV_PATH.exists() else []


def _write(lines):
    ENV_PATH.write_text("\n".join(lines) + "\n")


def _key_of(line):
    s = line.strip()
    if s.startswith("#") or "=" not in s:
        return None
    return s.split("=", 1)[0].strip()


def get_var(key, default=None):
    """Return the value of an uncommented KEY=... line, or default if absent."""
    for line in _lines():
        if _key_of(line) == key:
            return line.split("=", 1)[1].strip()
    return default


def set_var(key, value):
    """Set KEY=value, replacing an existing uncommented line or appending one.
    Returns True when .env changed (no-op if .env is missing or already matches)."""
    if not ENV_PATH.exists():
        return False
    lines = _lines()
    new_line = f"{key}={value}"
    for i, line in enumerate(lines):
        if _key_of(line) == key:
            if line == new_line:
                return False
            lines[i] = new_line
            _write(lines)
            return True
    lines.append(new_line)
    _write(lines)
    return True


def unset_var(key):
    """Remove an uncommented KEY=... line. Returns True when .env changed."""
    if not ENV_PATH.exists():
        return False
    lines = _lines()
    kept = [line for line in lines if _key_of(line) != key]
    if len(kept) == len(lines):
        return False
    _write(kept)
    return True
