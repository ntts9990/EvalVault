"""External command method adapter for dependency isolation."""

from __future__ import annotations

import json
import os
import subprocess
import warnings
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from evalvault.domain.entities.method import MethodInput, MethodOutput
from evalvault.ports.outbound.method_port import MethodRuntime, RagMethodPort


class ExternalCommandMethod(RagMethodPort):
    """Run a method via external command (separate env/venv/container)."""

    name = "external_command"
    version = "0.1.0"
    description = (
        "Execute a method in a separate process (shell=True requires a trusted command string)."
    )
    tags = ("external", "isolation")

    def __init__(
        self,
        *,
        command: list[str] | str,
        workdir: str | None = None,
        env: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
        shell: bool = False,
    ) -> None:
        self._command = command
        self._workdir = workdir
        self._env = env or {}
        self._timeout_seconds = timeout_seconds
        self._shell = shell

    def run(
        self,
        inputs: Sequence[MethodInput],
        *,
        runtime: MethodRuntime,
        config: dict[str, Any] | None = None,
    ) -> Sequence[MethodOutput]:
        input_path = runtime.input_path
        output_path = runtime.output_path
        if not input_path:
            raise ValueError("external command requires runtime.input_path")
        if not output_path:
            raise ValueError("external command requires runtime.output_path")

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env.update({str(k): str(v) for k, v in (self._env or {}).items()})
        env.update(
            {
                "EVALVAULT_METHOD_INPUT": str(input_path),
                "EVALVAULT_METHOD_OUTPUT": str(output_path),
                "EVALVAULT_METHOD_DOCS": runtime.docs_path or "",
                "EVALVAULT_METHOD_CONFIG": runtime.config_path or "",
                "EVALVAULT_METHOD_RUN_ID": runtime.run_id,
                "EVALVAULT_METHOD_ARTIFACTS": runtime.artifacts_dir or "",
            }
        )

        command = self._build_command(runtime)
        self._validate_shell_usage(command)
        result = subprocess.run(  # noqa: S603 - user-controlled command by design
            command,
            cwd=self._workdir,
            env=env,
            shell=self._shell,
            check=False,
            text=True,
            capture_output=True,
            timeout=self._timeout_seconds,
        )
        if result.returncode != 0:
            stderr = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(f"External method failed (code={result.returncode}): {stderr[:500]}")

        payload = self._load_payload(output_file)
        outputs = self._parse_outputs(payload)
        return outputs

    def _build_command(self, runtime: MethodRuntime) -> list[str] | str:
        replacements = {
            "input": runtime.input_path or "",
            "output": runtime.output_path or "",
            "docs": runtime.docs_path or "",
            "config": runtime.config_path or "",
            "run_id": runtime.run_id,
            "artifacts": runtime.artifacts_dir or "",
            "method": self.name,
        }

        try:
            if isinstance(self._command, str):
                return self._command.format(**replacements)

            return [str(part).format(**replacements) for part in self._command]
        except KeyError as exc:
            raise ValueError(f"Unknown command placeholder: {exc}") from exc

    def _validate_shell_usage(self, command: list[str] | str) -> None:
        if not self._shell:
            return
        if not isinstance(command, str):
            raise ValueError(
                "shell=True requires a single command string; list arguments are rejected."
            )
        if not command.strip():
            raise ValueError("shell=True requires a non-empty command string.")
        if "\n" in command or "\r" in command:
            raise ValueError("shell=True command must not contain newlines.")
        warnings.warn(
            "shell=True executes through the system shell. Use only trusted commands.",
            RuntimeWarning,
            stacklevel=2,
        )

    @staticmethod
    def _load_payload(path: Path) -> Any:
        if not path.exists():
            raise FileNotFoundError(f"External method output not found: {path}")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid external output JSON: {exc}") from exc

    def _parse_outputs(self, payload: Any) -> list[MethodOutput]:
        if isinstance(payload, dict) and "outputs" in payload:
            outputs_raw = payload.get("outputs")
        else:
            outputs_raw = payload

        if not isinstance(outputs_raw, list):
            raise ValueError("External output must be a list or contain 'outputs' list")

        outputs: list[MethodOutput] = []
        for idx, item in enumerate(outputs_raw):
            if not isinstance(item, dict):
                raise ValueError(f"Output {idx} must be an object")
            if "id" not in item or "answer" not in item:
                raise ValueError(f"Output {idx} missing required field 'id' or 'answer'")
            contexts = item.get("contexts")
            if contexts is None:
                contexts = []
            elif isinstance(contexts, str):
                contexts = [contexts]
            outputs.append(
                MethodOutput(
                    id=str(item["id"]),
                    answer=str(item["answer"]),
                    contexts=[str(c) for c in contexts],
                    metadata=item.get("metadata", {}),
                    retrieval_metadata=item.get("retrieval_metadata"),
                )
            )
        return outputs
