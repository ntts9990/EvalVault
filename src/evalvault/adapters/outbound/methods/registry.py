"""Registry for method plugins (internal config + entry points)."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from importlib.metadata import EntryPoint, entry_points
from pathlib import Path
from typing import Any

import yaml

from evalvault.ports.outbound.method_port import RagMethodPort

ENTRYPOINT_GROUP = "evalvault.methods"


@dataclass
class MethodSpec:
    """Descriptor for a method plugin."""

    name: str
    source: str
    class_path: str | None = None
    entry_point: str | None = None
    description: str | None = None
    version: str | None = None
    tags: list[str] = field(default_factory=list)
    default_config: dict[str, Any] | None = None
    runner: str | None = None
    command: list[str] | str | None = None
    workdir: str | None = None
    env: dict[str, str] | None = None
    timeout_seconds: int | None = None
    shell: bool = False
    error: str | None = None


class MethodRegistry:
    """Discover and load method plugins from config and entry points."""

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or Path.cwd() / "config" / "methods.yaml"
        self._internal_specs = self._load_internal_specs()
        self._entry_points = self._load_entry_points()

    def list_methods(self, *, load_details: bool = True) -> list[MethodSpec]:
        specs: dict[str, MethodSpec] = {}

        for name, spec in self._internal_specs.items():
            specs[name] = self._hydrate_spec(spec, load_details=load_details)

        for name, entry_point in self._entry_points.items():
            if name in specs:
                continue
            spec = MethodSpec(
                name=name,
                source="entry_point",
                entry_point=entry_point.value,
            )
            specs[name] = self._hydrate_spec(spec, load_details=load_details)

        return [specs[name] for name in sorted(specs)]

    def get_spec(self, name: str, *, load_details: bool = True) -> MethodSpec:
        name = name.strip()
        if not name:
            raise ValueError("method name is required")

        if name in self._internal_specs:
            return self._hydrate_spec(self._internal_specs[name], load_details=load_details)

        entry_point = self._entry_points.get(name)
        if entry_point is None:
            raise KeyError(f"Method not found: {name}")

        spec = MethodSpec(
            name=name,
            source="entry_point",
            entry_point=entry_point.value,
        )
        return self._hydrate_spec(spec, load_details=load_details)

    def get_method(self, name: str) -> RagMethodPort:
        spec = self.get_spec(name, load_details=False)

        if spec.source == "internal":
            if not spec.class_path:
                raise ValueError(f"Internal method '{name}' missing class_path")
            symbol = self._load_symbol(spec.class_path)
            return self._instantiate(symbol)

        entry_point = self._entry_points.get(name)
        if entry_point is None:
            raise KeyError(f"Method not found: {name}")
        symbol = entry_point.load()
        return self._instantiate(symbol)

    def _hydrate_spec(self, spec: MethodSpec, *, load_details: bool) -> MethodSpec:
        if not load_details or spec.error:
            return spec

        try:
            if spec.source == "internal" and spec.class_path:
                symbol = self._load_symbol(spec.class_path)
            elif spec.source == "entry_point":
                entry_point = self._entry_points.get(spec.name)
                if entry_point is None:
                    return spec
                symbol = entry_point.load()
            else:
                return spec

            instance = self._instantiate(symbol)
            spec.description = spec.description or getattr(instance, "description", None)
            spec.version = spec.version or getattr(instance, "version", None)
            tags = getattr(instance, "tags", None)
            if tags:
                spec.tags = list(tags)
            return spec
        except Exception as exc:  # pragma: no cover - best effort listing
            spec.error = self._summarize_error(exc)
            return spec

    def _load_internal_specs(self) -> dict[str, MethodSpec]:
        if not self._config_path.exists():
            return {}

        try:
            data = yaml.safe_load(self._config_path.read_text(encoding="utf-8")) or {}
        except Exception:
            return {}

        raw_methods = data.get("methods", {})
        items: list[dict[str, Any]] = []
        if isinstance(raw_methods, list):
            items = raw_methods
        elif isinstance(raw_methods, dict):
            for name, payload in raw_methods.items():
                entry = {"name": name}
                if isinstance(payload, dict):
                    entry.update(payload)
                items.append(entry)

        specs: dict[str, MethodSpec] = {}
        for item in items:
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            if item.get("enabled") is False:
                continue
            class_path = item.get("class_path") or item.get("class")
            spec = MethodSpec(
                name=name,
                source="internal",
                class_path=str(class_path) if class_path else None,
                description=item.get("description"),
                version=item.get("version"),
                tags=list(item.get("tags") or []),
                default_config=item.get("default_config"),
                runner=item.get("runner"),
                command=item.get("command"),
                workdir=item.get("workdir"),
                env=item.get("env"),
                timeout_seconds=item.get("timeout_seconds"),
                shell=bool(item.get("shell", False)),
            )
            if not spec.class_path and not spec.command:
                spec.error = "class_path or command is required"
            specs[name] = spec

        return specs

    @staticmethod
    def _load_entry_points() -> dict[str, EntryPoint]:
        eps = entry_points()
        if hasattr(eps, "select"):
            selected = eps.select(group=ENTRYPOINT_GROUP)
        else:  # pragma: no cover - legacy importlib.metadata
            selected = eps.get(ENTRYPOINT_GROUP, [])
        return {ep.name: ep for ep in selected}

    @staticmethod
    def _load_symbol(path: str) -> Any:
        if ":" in path:
            module_name, attr = path.split(":", 1)
        else:
            module_name, attr = path.rsplit(".", 1)
        module = import_module(module_name)
        return getattr(module, attr)

    @staticmethod
    def _instantiate(symbol: Any) -> RagMethodPort:
        if isinstance(symbol, RagMethodPort):
            return symbol
        if isinstance(symbol, type) and issubclass(symbol, RagMethodPort):
            return symbol()
        if callable(symbol):
            instance = symbol()
            if isinstance(instance, RagMethodPort):
                return instance
        raise TypeError("Method entry point must return a RagMethodPort instance")

    @staticmethod
    def _summarize_error(exc: Exception) -> str:
        message = str(exc).strip()
        if not message:
            return exc.__class__.__name__
        first_line = message.splitlines()[0]
        if len(first_line) > 200:
            first_line = f"{first_line[:200]}..."
        return f"{exc.__class__.__name__}: {first_line}"
