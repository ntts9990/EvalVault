from pathlib import Path

from evalvault.domain.services.prompt_candidate_service import PromptCandidateService


def test_build_candidates_with_manual_prompts_and_files(tmp_path: Path) -> None:
    service = PromptCandidateService()
    file_path = tmp_path / "manual.txt"
    file_path.write_text("첫 후보\n\n둘째 후보\n첫 후보\n", encoding="utf-8")

    candidates = service.build_candidates(
        base_prompt="기본 프롬프트",
        role="system",
        metrics=["faithfulness"],
        manual_prompts=["직접 후보", ""],
        manual_prompt_files=[file_path],
        auto=False,
        auto_count=0,
    )

    contents = [candidate.content for candidate in candidates]
    assert contents == ["직접 후보", "첫 후보", "둘째 후보"]
    assert [candidate.candidate_id for candidate in candidates] == [
        "cand-001",
        "cand-002",
        "cand-003",
    ]
    assert candidates[0].source == "manual"
    assert candidates[1].metadata["file_line"] == 1


def test_build_candidates_with_auto_variants() -> None:
    service = PromptCandidateService()

    candidates = service.build_candidates(
        base_prompt="기본 프롬프트",
        role="system",
        metrics=["answer_relevancy", "faithfulness"],
        manual_prompts=[],
        manual_prompt_files=[],
        auto=True,
        auto_count=3,
    )

    assert len(candidates) == 3
    assert {candidate.source for candidate in candidates} == {"auto"}
    assert candidates[0].content == "기본 프롬프트"
    assert candidates[1].metadata["variant"] == "role_focus"


def test_build_candidates_deduplicates_manual_and_auto() -> None:
    service = PromptCandidateService()

    candidates = service.build_candidates(
        base_prompt="중복 테스트",
        role="system",
        metrics=[],
        manual_prompts=["중복 테스트"],
        manual_prompt_files=[],
        auto=True,
        auto_count=1,
    )

    assert len(candidates) == 1
    assert candidates[0].content == "중복 테스트"
