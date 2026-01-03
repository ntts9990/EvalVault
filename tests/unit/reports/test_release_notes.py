"""Tests for release notes builder."""

from evalvault.reports import build_release_notes


def test_build_release_notes_includes_phoenix_links_and_failures() -> None:
    summary = {
        "dataset_name": "insurance-qa",
        "dataset_version": "2026.01",
        "model_name": "gpt-5-nano",
        "total_test_cases": 10,
        "passed_test_cases": 8,
        "pass_rate": 0.8,
        "avg_faithfulness": 0.76,
        "results": [
            {
                "test_case_id": "tc-01",
                "all_passed": False,
                "metrics": [
                    {"name": "faithfulness", "score": 0.6, "threshold": 0.7},
                ],
            }
        ],
        "tracker_metadata": {
            "phoenix": {
                "trace_url": "http://phoenix/traces/abc",
                "dataset": {"url": "http://phoenix/datasets/id"},
                "prompts": [
                    {
                        "path": "/tmp/system.txt",
                        "status": "modified",
                        "phoenix_prompt_id": "pr-1",
                        "diff": "- hi\n+ hello",
                    }
                ],
            }
        },
    }

    markdown = build_release_notes(summary, max_failures=1, prompt_diff_lines=1)

    assert "insurance-qa" in markdown
    assert "faithfulness" in markdown
    assert "http://phoenix/traces/abc" in markdown
    assert "Phoenix & Prompt Loop" in markdown
    assert "Prompt Summary" in markdown
    assert "system.txt" in markdown
