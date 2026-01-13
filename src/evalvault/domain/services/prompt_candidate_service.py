"""Candidate collection service for prompt suggestions."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from evalvault.domain.entities.prompt_suggestion import PromptCandidate


class PromptCandidateService:
    """Build prompt candidates from manual and auto sources."""

    def build_candidates(
        self,
        *,
        base_prompt: str,
        role: str,
        metrics: list[str],
        manual_prompts: list[str],
        manual_prompt_files: list[Path],
        auto: bool,
        auto_count: int,
        metadata: dict[str, Any] | None = None,
    ) -> list[PromptCandidate]:
        base_metadata = metadata or {}
        candidates: list[PromptCandidate] = []
        seen: set[str] = set()

        def add_candidate(
            content: str, *, source: str, extra: dict[str, Any] | None = None
        ) -> None:
            normalized = content.strip()
            if not normalized:
                return
            if normalized in seen:
                return
            candidate_metadata = {**base_metadata, **(extra or {})}
            candidates.append(
                PromptCandidate(
                    candidate_id="",
                    source=source,
                    content=normalized,
                    metadata=candidate_metadata,
                )
            )
            seen.add(normalized)

        for index, prompt in enumerate(manual_prompts):
            add_candidate(prompt, source="manual", extra={"manual_index": index})

        for path in manual_prompt_files:
            for line_number, line in enumerate(self._read_prompt_file(path), start=1):
                add_candidate(
                    line,
                    source="manual",
                    extra={"file_path": str(path), "file_line": line_number},
                )

        if auto and auto_count > 0:
            for name, content in self._build_auto_variants(
                base_prompt=base_prompt,
                role=role,
                metrics=metrics,
                auto_count=auto_count,
            ):
                add_candidate(
                    content,
                    source="auto",
                    extra={"variant": name, "generator": "template"},
                )

        return [
            replace(candidate, candidate_id=f"cand-{index:03d}")
            for index, candidate in enumerate(candidates, start=1)
        ]

    def _read_prompt_file(self, path: Path) -> list[str]:
        lines = path.read_text(encoding="utf-8").splitlines()
        return [line.strip() for line in lines if line.strip()]

    def _build_auto_variants(
        self,
        *,
        base_prompt: str,
        role: str,
        metrics: list[str],
        auto_count: int,
    ) -> list[tuple[str, str]]:
        metrics_text = ", ".join(metrics) if metrics else "핵심 지표"
        base_prompt = base_prompt.strip() or "사용자 요청에 충실히 답변하라."
        variants = [
            ("base", base_prompt),
            (
                "role_focus",
                f"{base_prompt}\n\nRole: {role}. 이 역할에 맞는 톤을 유지하라.",
            ),
            (
                "metric_focus",
                f"{base_prompt}\n\n성과 지표({metrics_text})에 맞춰 응답 품질을 높여라.",
            ),
            (
                "concise",
                f"{base_prompt}\n\n핵심만 간결하게 답하고 필요한 경우 bullet로 정리하라.",
            ),
            (
                "assumptions",
                f"{base_prompt}\n\n불확실하면 가정과 전제를 명시하라.",
            ),
        ]
        if auto_count <= len(variants):
            return variants[:auto_count]
        extra = []
        for index in range(len(variants) + 1, auto_count + 1):
            extra.append((f"variant_{index}", f"{base_prompt}\n\n추가 후보 {index}."))
        return variants + extra
