from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evalvault.domain.entities.prompt_suggestion import (
    PromptCandidate,
    PromptCandidateSampleScore,
    PromptCandidateScore,
    PromptSuggestionResult,
)
from evalvault.ports.outbound.storage_port import StoragePort


def _serialize_sample_score(sample: PromptCandidateSampleScore) -> dict[str, Any]:
    return {
        "sample_index": sample.sample_index,
        "scores": dict(sample.scores),
        "weighted_score": sample.weighted_score,
        "responses": list(sample.responses),
    }


class PromptSuggestionReporter:
    def render_json(self, result: PromptSuggestionResult) -> dict[str, Any]:
        score_map = {score.candidate_id: score for score in result.scores}
        candidates_payload = [
            self._serialize_candidate(candidate, score_map) for candidate in result.candidates
        ]
        return {
            "run_id": result.run_id,
            "role": result.role,
            "metrics": list(result.metrics),
            "weights": dict(result.weights),
            "candidates": candidates_payload,
            "ranking": list(result.ranking),
            "holdout_ratio": result.holdout_ratio,
            "metadata": dict(result.metadata),
        }

    def render_markdown(self, result: PromptSuggestionResult) -> str:
        score_map = {score.candidate_id: score for score in result.scores}
        lines = [
            "# 프롬프트 추천 결과",
            "",
            "## 개요",
            f"- run_id: {result.run_id}",
            f"- role: {result.role}",
            f"- metrics: {', '.join(result.metrics)}",
            f"- holdout_ratio: {result.holdout_ratio:.2f}",
        ]
        if result.weights:
            weights = ", ".join(
                f"{metric}={weight:.2f}" for metric, weight in result.weights.items()
            )
            lines.append(f"- weights: {weights}")
        if result.metadata:
            lines.append(f"- metadata: {json.dumps(result.metadata, ensure_ascii=False)}")

        lines.extend(
            [
                "",
                "## 후보 순위",
                "",
                "| Rank | Candidate | Source | Score |",
                "| --- | --- | --- | --- |",
            ]
        )

        for rank, candidate_id in enumerate(result.ranking, start=1):
            candidate = next(
                (item for item in result.candidates if item.candidate_id == candidate_id), None
            )
            score = score_map.get(candidate_id)
            if candidate is None or score is None:
                continue
            preview = candidate.content.replace("\n", " ")
            if len(preview) > 80:
                preview = preview[:77] + "..."
            lines.append(
                f"| {rank} | {preview} | {candidate.source} | {score.weighted_score:.4f} |"
            )

        lines.append("")
        lines.append("## 후보 상세")
        for candidate in result.candidates:
            score = score_map.get(candidate.candidate_id)
            lines.extend(
                [
                    "",
                    f"### {candidate.candidate_id}",
                    f"- source: {candidate.source}",
                    f"- weighted_score: {score.weighted_score:.4f}" if score else "- score: -",
                ]
            )
            if score:
                lines.append(f"- selected_sample_index: {score.selected_sample_index}")
            if score and score.scores:
                lines.append("- metric_scores:")
                for metric, value in score.scores.items():
                    lines.append(f"  - {metric}: {value:.4f}")
            if score and score.sample_scores:
                lines.append("- sample_scores:")
                for sample in score.sample_scores:
                    metrics = ", ".join(
                        f"{metric}={value:.4f}" for metric, value in sample.scores.items()
                    )
                    lines.append(
                        f"  - {sample.sample_index}: {sample.weighted_score:.4f} ({metrics})"
                    )
                selected_sample = next(
                    (
                        entry
                        for entry in score.sample_scores
                        if entry.sample_index == score.selected_sample_index
                    ),
                    None,
                )
                if selected_sample:
                    lines.append(f"- selected_sample_responses: {len(selected_sample.responses)}")
                    for response in selected_sample.responses:
                        question = response.get("question") or ""
                        answer = response.get("answer") or ""
                        ground_truth = response.get("ground_truth") or ""
                        contexts = list(response.get("contexts") or [])
                        lines.extend(
                            [
                                "  - response:",
                                f"    - test_case_id: {response.get('test_case_id')}",
                                f"    - question: {question}",
                                "    - contexts:",
                            ]
                        )
                        for ctx in contexts:
                            lines.append(f"      - {ctx}")
                        lines.extend(
                            [
                                "    - answer:",
                                "      ```",
                                f"      {answer}",
                                "      ```",
                            ]
                        )
                        if ground_truth:
                            lines.extend(
                                [
                                    "    - ground_truth:",
                                    "      ```",
                                    f"      {ground_truth}",
                                    "      ```",
                                ]
                            )
            if candidate.metadata:
                lines.append(f"- metadata: {json.dumps(candidate.metadata, ensure_ascii=False)}")
            lines.extend(["", "```", candidate.content.strip(), "```"])

        return "\n".join(lines).strip() + "\n"

    def write_outputs(
        self,
        *,
        result: PromptSuggestionResult,
        output_path: Path,
        report_path: Path,
        artifacts_dir: Path,
        storage: StoragePort | None = None,
    ) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        json_payload = self.render_json(result)
        output_path.write_text(
            json.dumps(json_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        markdown_text = self.render_markdown(result)
        report_path.write_text(markdown_text, encoding="utf-8")

        artifacts_index = self._write_artifacts(result, artifacts_dir)
        index_path = artifacts_dir / "index.json"
        index_path.write_text(
            json.dumps(artifacts_index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        if storage:
            storage.save_analysis_report(
                report_id=None,
                run_id=result.run_id,
                experiment_id=None,
                report_type="prompt_suggestions",
                format="markdown",
                content=markdown_text,
                metadata={
                    "output_path": str(output_path),
                    "report_path": str(report_path),
                    "artifacts_dir": str(artifacts_dir),
                },
            )

    def _serialize_candidate(
        self,
        candidate: PromptCandidate,
        score_map: dict[str, PromptCandidateScore],
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "candidate_id": candidate.candidate_id,
            "source": candidate.source,
            "content": candidate.content,
        }
        score = score_map.get(candidate.candidate_id)
        if score:
            payload["scores"] = dict(score.scores)
            payload["weighted_score"] = score.weighted_score
            payload["selected_sample_index"] = score.selected_sample_index
            if score.sample_scores:
                payload["sample_scores"] = [
                    _serialize_sample_score(entry) for entry in score.sample_scores
                ]
        if candidate.metadata:
            payload["metadata"] = dict(candidate.metadata)
        return payload

    def _write_artifacts(
        self, result: PromptSuggestionResult, artifacts_dir: Path
    ) -> dict[str, Any]:
        candidates_payload = [
            {
                "candidate_id": candidate.candidate_id,
                "source": candidate.source,
                "content": candidate.content,
                "metadata": dict(candidate.metadata),
            }
            for candidate in result.candidates
        ]
        scores_payload = [
            {
                "candidate_id": score.candidate_id,
                "scores": dict(score.scores),
                "weighted_score": score.weighted_score,
                "selected_sample_index": score.selected_sample_index,
                "sample_scores": [
                    _serialize_sample_score(sample) for sample in score.sample_scores
                ],
            }
            for score in result.scores
        ]
        ranking_payload = list(result.ranking)

        candidates_path = artifacts_dir / "candidates.json"
        scores_path = artifacts_dir / "scores.json"
        ranking_path = artifacts_dir / "ranking.json"

        candidates_path.write_text(
            json.dumps(candidates_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        scores_path.write_text(
            json.dumps(scores_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        ranking_path.write_text(
            json.dumps(ranking_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return {
            "dir": str(artifacts_dir),
            "files": {
                "candidates": str(candidates_path),
                "scores": str(scores_path),
                "ranking": str(ranking_path),
            },
        }
