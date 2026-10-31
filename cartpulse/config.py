"""Settings read from the environment, with .env as the local source."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]

# Scripts can run from any directory, so the path is explicit.
load_dotenv(REPO_ROOT / ".env")


def _excluded_ips():
    raw = os.getenv("CARTPULSE_EXCLUDED_IPS", "198.46.149.143")
    return frozenset(ip.strip() for ip in raw.split(",") if ip.strip())


def _env(name, default):
    return field(default_factory=lambda: os.getenv(name, default))


def _env_int(name, default):
    return field(default_factory=lambda: int(os.getenv(name, default)))


def _secret(name):
    return field(default_factory=lambda: os.environ[name])


@dataclass(frozen=True)
class Settings:
    mysql_host: str = _env("MYSQL_HOST", "127.0.0.1")
    mysql_port: int = _env_int("MYSQL_PORT", "3306")
    mysql_password: str = _secret("MYSQL_PASSWORD")
    mongo_host: str = _env("MONGO_HOST", "127.0.0.1")
    mongo_port: int = _env_int("MONGO_PORT", "27017")
    mongo_password: str = _secret("MONGO_ROOT_PASSWORD")
    postgres_host: str = _env("POSTGRES_HOST", "127.0.0.1")
    postgres_port: int = _env_int("POSTGRES_PORT", "5434")
    postgres_password: str = _secret("POSTGRES_PASSWORD")
    data_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("CARTPULSE_DATA_DIR", REPO_ROOT / "data" / "raw")
        )
    )
    watermark_lookback_seconds: int = _env_int(
        "CARTPULSE_WATERMARK_LOOKBACK_SECONDS", "300"
    )
    excluded_ips: frozenset = field(default_factory=_excluded_ips)
