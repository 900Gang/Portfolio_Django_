"""
Minimal .env loader and typed environment accessors.

Deliberately dependency-free: the project ships only Django and Pillow, and a
~40 line loader is cheaper to own than an extra runtime dependency.
Real environment variables always win over values in the .env file, so
container/CI configuration overrides the local developer file.
"""
import os
from pathlib import Path


def load_dotenv(path: Path) -> None:
    """Load KEY=VALUE pairs from `path` into os.environ without overriding it."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def get_str(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Required environment variable {name!r} is not set.")
    return value


def get_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_list(name: str, default: str = "") -> list[str]:
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]
