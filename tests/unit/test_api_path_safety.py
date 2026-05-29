"""Security regression tests for the web API path-safety helpers.

These cover the path-traversal fixes for the upload sinks
(``save_dataset_file`` / ``save_retriever_docs_file`` / knowledge upload) and
the request-supplied path inputs (``dataset_path`` / retriever ``docs_path``).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from evalvault.adapters.inbound.api.path_safety import (
    UnsafePathError,
    allowed_roots,
    ensure_within_allowed,
    resolve_user_path,
    safe_upload_filename,
)


class TestSafeUploadFilename:
    def test_accepts_plain_basename(self) -> None:
        assert safe_upload_filename("insurance-qa.json") == "insurance-qa.json"

    @pytest.mark.parametrize(
        "bad",
        [
            None,
            "",
            ".",
            "..",
            "../evil.json",
            "../../evil.py",
            "a/b.json",
            "sub/dir/x.txt",
            "..\\evil.json",
            "C:\\Windows\\evil.json",
            "/etc/cron.d/evil",
            "evil\x00.json",
        ],
    )
    def test_rejects_traversal_and_separators(self, bad) -> None:
        with pytest.raises(UnsafePathError):
            safe_upload_filename(bad)


class TestResolveUserPath:
    def test_rejects_absolute_path_outside_roots(self) -> None:
        with pytest.raises(UnsafePathError):
            resolve_user_path("/etc/passwd", must_exist=False)

    def test_rejects_relative_traversal_escaping_roots(self) -> None:
        with pytest.raises(UnsafePathError):
            resolve_user_path("../../../../etc/passwd", must_exist=False)

    def test_allows_path_inside_data_root(self) -> None:
        resolved = resolve_user_path("data/datasets/example.json", must_exist=False)
        data_root = next(r for r in allowed_roots() if r.name == "data")
        assert resolved.is_relative_to(data_root)

    def test_must_exist_rejects_missing_in_tree_file(self) -> None:
        with pytest.raises(UnsafePathError):
            resolve_user_path("data/datasets/__does_not_exist__.json", must_exist=True)

    def test_empty_is_rejected(self) -> None:
        with pytest.raises(UnsafePathError):
            resolve_user_path("", must_exist=False)


class TestAllowedRoots:
    def test_includes_data_fixtures_reports(self) -> None:
        names = {r.name for r in allowed_roots()}
        assert {"data", "fixtures", "reports"}.issubset(names)

    def test_ensure_within_allowed_blocks_outside(self) -> None:
        with pytest.raises(UnsafePathError):
            ensure_within_allowed(Path("/etc").resolve())


class TestUploadSinksRejectTraversal:
    """``WebUIAdapter`` upload sinks must not write outside their dir."""

    def _adapter(self):
        from evalvault.adapters.inbound.api.adapter import WebUIAdapter

        return WebUIAdapter(storage=MagicMock())

    def test_save_dataset_file_rejects_traversal(self, monkeypatch, tmp_path) -> None:
        monkeypatch.chdir(tmp_path)
        adapter = self._adapter()
        with pytest.raises(UnsafePathError):
            adapter.save_dataset_file("../../escaped.json", b"pwned")
        # The escaped target must not have been written.
        assert not (tmp_path.parent / "escaped.json").exists()

    def test_save_dataset_file_allows_plain_name(self, monkeypatch, tmp_path) -> None:
        monkeypatch.chdir(tmp_path)
        adapter = self._adapter()
        saved = adapter.save_dataset_file("ok.json", b"hello")
        saved_path = Path(saved)
        assert saved_path.read_bytes() == b"hello"
        assert saved_path.parent == (tmp_path / "data" / "datasets").resolve()

    def test_save_retriever_docs_file_rejects_traversal(self, monkeypatch, tmp_path) -> None:
        monkeypatch.chdir(tmp_path)
        adapter = self._adapter()
        with pytest.raises(UnsafePathError):
            adapter.save_retriever_docs_file("../../escaped.txt", b"pwned")
        assert not (tmp_path.parent / "escaped.txt").exists()


class TestFailClosedNetworkBind:
    """EvalVault Auth P1.0: refuse non-loopback bind without authentication."""

    def _settings(self, tokens):
        from evalvault.config.settings import Settings

        return Settings(api_auth_tokens=tokens)

    def test_is_loopback_host(self) -> None:
        from evalvault.adapters.inbound.api.main import is_loopback_host

        assert is_loopback_host("127.0.0.1")
        assert is_loopback_host("localhost")
        assert is_loopback_host("::1")
        assert not is_loopback_host("0.0.0.0")
        assert not is_loopback_host("192.168.1.10")

    def test_loopback_without_auth_is_allowed(self, monkeypatch) -> None:
        from evalvault.adapters.inbound.api.main import ensure_safe_network_bind

        monkeypatch.delenv("EVALVAULT_ALLOW_INSECURE_NETWORK", raising=False)
        ensure_safe_network_bind("127.0.0.1", self._settings(None))  # no raise

    def test_non_loopback_without_auth_is_refused(self, monkeypatch) -> None:
        from evalvault.adapters.inbound.api.main import ensure_safe_network_bind

        monkeypatch.delenv("EVALVAULT_ALLOW_INSECURE_NETWORK", raising=False)
        with pytest.raises(RuntimeError):
            ensure_safe_network_bind("0.0.0.0", self._settings(None))

    def test_non_loopback_with_token_is_allowed(self, monkeypatch) -> None:
        from evalvault.adapters.inbound.api.main import ensure_safe_network_bind

        monkeypatch.delenv("EVALVAULT_ALLOW_INSECURE_NETWORK", raising=False)
        ensure_safe_network_bind("0.0.0.0", self._settings("secret-token"))  # no raise

    def test_override_env_allows_insecure_bind(self, monkeypatch) -> None:
        from evalvault.adapters.inbound.api.main import ensure_safe_network_bind

        monkeypatch.setenv("EVALVAULT_ALLOW_INSECURE_NETWORK", "1")
        ensure_safe_network_bind("0.0.0.0", self._settings(None))  # no raise
