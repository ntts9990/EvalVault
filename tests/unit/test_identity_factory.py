from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from evalvault.adapters.inbound.api import main as api_main
from evalvault.adapters.outbound.storage import identity_factory
from evalvault.adapters.outbound.storage.sqlite_identity import SqliteIdentityStorageAdapter
from evalvault.config.settings import Settings


class _FakePostgresIdentityStore:
    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string


def test_identity_factory_module_import_does_not_require_psycopg(monkeypatch) -> None:
    module_name = "evalvault.adapters.outbound.storage.identity_factory"
    postgres_module_name = "evalvault.adapters.outbound.storage.postgres_identity"
    original_identity_module = sys.modules.pop(module_name, None)
    original_postgres_module = sys.modules.pop(postgres_module_name, None)
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "psycopg" or name.startswith("psycopg."):
            raise ModuleNotFoundError(name)
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    try:
        imported = importlib.import_module(module_name)
        assert hasattr(imported, "build_identity_storage_adapter")
    finally:
        sys.modules.pop(module_name, None)
        if original_identity_module is not None:
            sys.modules[module_name] = original_identity_module
        if original_postgres_module is not None:
            sys.modules[postgres_module_name] = original_postgres_module


def test_identity_factory_uses_sqlite_backend(tmp_path: Path) -> None:
    settings = Settings(db_backend="sqlite", evalvault_db_path=str(tmp_path / "identity.db"))

    store = identity_factory.build_identity_storage_adapter(settings)

    assert isinstance(store, SqliteIdentityStorageAdapter)


def test_identity_factory_sqlite_backend_does_not_touch_postgres(monkeypatch, tmp_path: Path) -> None:
    def fail_if_called(connection_string: str):
        raise AssertionError(f"unexpected postgres identity construction: {connection_string}")

    monkeypatch.setattr(identity_factory, "_build_postgres_identity_storage", fail_if_called)
    settings = Settings(db_backend="sqlite", evalvault_db_path=str(tmp_path / "identity.db"))

    store = identity_factory.build_identity_storage_adapter(settings)

    assert isinstance(store, SqliteIdentityStorageAdapter)


def test_identity_factory_uses_postgres_connection_string(monkeypatch) -> None:
    monkeypatch.setattr(identity_factory, "_build_postgres_identity_storage", _FakePostgresIdentityStore)
    settings = Settings(
        db_backend="postgres",
        postgres_connection_string="postgresql://identity",
    )

    store = identity_factory.build_identity_storage_adapter(settings)

    assert isinstance(store, _FakePostgresIdentityStore)
    assert store.connection_string == "postgresql://identity"


def test_identity_factory_builds_postgres_dsn_from_settings(monkeypatch) -> None:
    monkeypatch.setattr(identity_factory, "_build_postgres_identity_storage", _FakePostgresIdentityStore)
    monkeypatch.setenv("POSTGRES_HOST", "db.internal")
    monkeypatch.setenv("POSTGRES_PORT", "5544")
    monkeypatch.setenv("POSTGRES_DATABASE", "evalvault_identity")
    monkeypatch.setenv("POSTGRES_USER", "identity")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")
    monkeypatch.delenv("POSTGRES_CONNECTION_STRING", raising=False)
    settings = Settings(db_backend="postgres")

    store = identity_factory.build_identity_storage_adapter(settings)

    assert isinstance(store, _FakePostgresIdentityStore)
    assert store.connection_string == (
        "host=db.internal port=5544 dbname=evalvault_identity "
        "user=identity password=secret"
    )


def test_api_identity_store_lazy_builder_caches_store(monkeypatch) -> None:
    fake_store = object()
    calls = 0

    def fake_builder(settings: Settings):
        nonlocal calls
        calls += 1
        assert settings.db_backend == "sqlite"
        return fake_store

    monkeypatch.setattr(identity_factory, "build_identity_storage_adapter", fake_builder)
    monkeypatch.setattr(
        api_main,
        "get_settings",
        lambda: Settings(db_backend="sqlite", evalvault_db_path=":memory:"),
    )
    app = FastAPI()
    scope = {"type": "http", "method": "GET", "path": "/", "headers": [], "app": app}
    request = Request(scope)

    assert api_main._resolve_identity_store(request) is fake_store
    assert api_main._resolve_identity_store(request) is fake_store
    assert calls == 1


def test_invalid_bearer_token_fails_closed_when_identity_backend_unavailable(monkeypatch) -> None:
    def broken_builder(settings: Settings):
        raise RuntimeError("identity backend unavailable")

    monkeypatch.setattr(identity_factory, "build_identity_storage_adapter", broken_builder)
    monkeypatch.setattr(api_main, "get_settings", lambda: Settings(db_backend="postgres"))
    app = FastAPI()
    scope = {"type": "http", "method": "GET", "path": "/", "headers": [], "app": app}
    request = Request(scope)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-a-service-token")

    with pytest.raises(api_main.HTTPException) as exc_info:
        api_main.require_api_token(
            request,
            credentials,
            settings=Settings(api_auth_tokens="service-token"),
        )

    assert exc_info.value.status_code == 401
