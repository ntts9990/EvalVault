from __future__ import annotations

import logging
import socket
import subprocess
from dataclasses import dataclass
from shutil import which
from urllib.parse import urlparse

from evalvault.config.settings import Settings, is_production_profile

logger = logging.getLogger(__name__)

_PHOENIX_CONTAINER = "evalvault-phoenix"


@dataclass(frozen=True)
class Endpoint:
    host: str
    port: int


def _is_local_host(host: str | None) -> bool:
    if not host:
        return False
    return host in {"localhost", "127.0.0.1", "0.0.0.0"}


def _port_is_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False


def _parse_http_endpoint(url: str | None, default_port: int) -> Endpoint | None:
    if not url or not isinstance(url, str):
        return None
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return None
    host = parsed.hostname or ""
    port = parsed.port or default_port
    if not host or port <= 0:
        return None
    return Endpoint(host=host, port=port)


def _start_mlflow(port: int) -> bool:
    if which("mlflow") is None:
        logger.warning("MLflow CLI not found. Install with: uv sync --extra mlflow")
        return False
    try:
        subprocess.Popen(
            ["mlflow", "server", "--host", "0.0.0.0", "--port", str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("Started MLflow server on port %s", port)
        return True
    except Exception as exc:  # pragma: no cover - safety net
        logger.warning("Failed to start MLflow server: %s", exc)
        return False


def _start_phoenix(port: int) -> bool:
    if which("docker") is None:
        logger.warning("Docker not found. Phoenix auto-start skipped.")
        return False
    try:
        start = subprocess.run(
            ["docker", "start", _PHOENIX_CONTAINER],
            check=False,
            capture_output=True,
            text=True,
        )
        if start.returncode != 0:
            subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "-p",
                    f"{port}:6006",
                    "--name",
                    _PHOENIX_CONTAINER,
                    "arizephoenix/phoenix:latest",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
        logger.info("Ensured Phoenix container is running on port %s", port)
        return True
    except Exception as exc:  # pragma: no cover - safety net
        logger.warning("Failed to start Phoenix container: %s", exc)
        return False


def ensure_local_observability(settings: Settings) -> None:
    if is_production_profile(settings.evalvault_profile):
        return

    phoenix_endpoint = _parse_http_endpoint(
        getattr(settings, "phoenix_endpoint", None) or "http://localhost:6006/v1/traces",
        6006,
    )
    if (
        phoenix_endpoint
        and _is_local_host(phoenix_endpoint.host)
        and not _port_is_open(phoenix_endpoint.host, phoenix_endpoint.port)
    ):
        _start_phoenix(phoenix_endpoint.port)

    mlflow_endpoint = _parse_http_endpoint(getattr(settings, "mlflow_tracking_uri", None), 5000)
    if (
        mlflow_endpoint
        and _is_local_host(mlflow_endpoint.host)
        and not _port_is_open(mlflow_endpoint.host, mlflow_endpoint.port)
    ):
        _start_mlflow(mlflow_endpoint.port)
