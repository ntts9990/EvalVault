"""Tests for domain memory CLI commands."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from evalvault.adapters.inbound.cli import app
from evalvault.config.domain_config import (
    generate_domain_template,
    load_domain_config,
    save_domain_config,
)


def _seed_domain_config(
    base_dir: Path,
    domain: str,
    languages: list[str] | None = None,
) -> Path:
    config_dir = base_dir / "config" / "domains"
    template = generate_domain_template(domain=domain, languages=languages)
    config_path = save_domain_config(domain, template, config_dir)
    for filename in template["factual"]["glossary"].values():
        terms_path = config_path.parent / filename
        terms_path.write_text(json.dumps({"terms": {}}, indent=2), encoding="utf-8")
    return config_path


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_project(tmp_path, monkeypatch):
    """Temporary project root."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestDomainInit:
    """Tests for 'evalvault domain init' command."""

    def test_domain_init_basic(self, runner, temp_project):
        """Test basic domain initialization."""
        result = runner.invoke(app, ["domain", "init", "insurance"])

        assert result.exit_code == 0

        domain_dir = temp_project / "config" / "domains" / "insurance"
        assert (domain_dir / "memory.yaml").exists()
        assert (domain_dir / "terms_dictionary_ko.json").exists()
        assert (domain_dir / "terms_dictionary_en.json").exists()

    def test_domain_init_with_languages(self, runner, temp_project):
        """Test domain init with custom languages."""
        result = runner.invoke(
            app,
            ["domain", "init", "medical", "--languages", "en"],
        )

        assert result.exit_code == 0

        domain_dir = temp_project / "config" / "domains" / "medical"
        assert (domain_dir / "terms_dictionary_en.json").exists()
        assert not (domain_dir / "terms_dictionary_ko.json").exists()

        config = load_domain_config("medical")
        assert config.metadata.supported_languages == ["en"]

    def test_domain_init_with_description(self, runner, temp_project):
        """Test domain init with description."""
        description = "Insurance domain for RAG evaluation"
        result = runner.invoke(
            app,
            [
                "domain",
                "init",
                "insurance",
                "--description",
                description,
            ],
        )

        assert result.exit_code == 0
        config = load_domain_config("insurance")
        assert config.metadata.description == description

    def test_domain_init_existing_without_force(self, runner, temp_project):
        """Test that init fails on existing domain without --force."""
        domain_dir = temp_project / "config" / "domains" / "insurance"
        domain_dir.mkdir(parents=True, exist_ok=True)

        result = runner.invoke(app, ["domain", "init", "insurance"])

        assert result.exit_code == 1

    def test_domain_init_existing_with_force(self, runner, temp_project):
        """Test that init overwrites existing domain with --force."""
        domain_dir = temp_project / "config" / "domains" / "insurance"
        domain_dir.mkdir(parents=True, exist_ok=True)

        result = runner.invoke(app, ["domain", "init", "insurance", "--force"])

        assert result.exit_code == 0
        assert (domain_dir / "memory.yaml").exists()


class TestDomainList:
    """Tests for 'evalvault domain list' command."""

    def test_domain_list_empty(self, runner, temp_project):
        """Test listing domains when none exist."""
        result = runner.invoke(app, ["domain", "list"])

        assert result.exit_code == 0
        assert "No domains configured" in result.stdout

    def test_domain_list_with_domains(self, runner, temp_project):
        """Test listing existing domains."""
        _seed_domain_config(temp_project, "insurance")
        _seed_domain_config(temp_project, "medical", languages=["en"])

        result = runner.invoke(app, ["domain", "list"])

        assert result.exit_code == 0
        assert "insurance" in result.stdout
        assert "medical" in result.stdout


class TestDomainShow:
    """Tests for 'evalvault domain show' command."""

    def test_domain_show_missing(self, runner, temp_project):
        """Test that show fails for missing domains."""
        result = runner.invoke(app, ["domain", "show", "insurance"])

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_domain_show_success(self, runner, temp_project):
        """Test domain show for configured domain."""
        _seed_domain_config(temp_project, "insurance")

        result = runner.invoke(app, ["domain", "show", "insurance"])

        assert result.exit_code == 0
        assert "Domain Configuration: insurance" in result.stdout


class TestDomainTerms:
    """Tests for 'evalvault domain terms' command."""

    def test_domain_terms_empty(self, runner, temp_project):
        """Test terms output when glossary is empty."""
        _seed_domain_config(temp_project, "insurance")

        result = runner.invoke(app, ["domain", "terms", "insurance"])

        assert result.exit_code == 0
        assert "No terms defined" in result.stdout or "Terminology Dictionary" in result.stdout

    def test_domain_terms_language_not_supported(self, runner, temp_project):
        """Test terms for unsupported language."""
        _seed_domain_config(temp_project, "insurance", languages=["en"])

        result = runner.invoke(
            app,
            ["domain", "terms", "insurance", "--language", "ko"],
        )

        assert result.exit_code == 1
        assert "not supported" in result.stdout.lower()


class TestDomainMemoryStats:
    """Tests for 'evalvault domain memory stats' command."""

    @patch("evalvault.adapters.inbound.cli.commands.domain.build_domain_memory_adapter")
    def test_memory_stats_basic(self, mock_adapter_class, runner):
        """Test domain memory stats display."""
        mock_adapter = MagicMock()
        mock_adapter.get_statistics.return_value = {
            "facts": 2,
            "learnings": 1,
            "behaviors": 3,
            "contexts": 0,
        }
        mock_adapter_class.return_value = mock_adapter

        result = runner.invoke(app, ["domain", "memory", "stats", "--domain", "insurance"])

        assert result.exit_code == 0
        mock_adapter.get_statistics.assert_called_once_with(domain="insurance")


class TestDomainMemorySearch:
    """Tests for 'evalvault domain memory search' command."""

    @patch("evalvault.adapters.inbound.cli.commands.domain.build_domain_memory_adapter")
    def test_memory_search_filters_by_min_score(self, mock_adapter_class, runner):
        """Test memory search filters results by min score."""
        from evalvault.domain.entities.memory import FactualFact

        mock_adapter = MagicMock()
        mock_adapter.search_facts.return_value = [
            FactualFact(
                fact_id="fact-1",
                subject="premium",
                predicate="is",
                object="price",
                domain="insurance",
                language="en",
                verification_score=0.9,
                verification_count=2,
            ),
            FactualFact(
                fact_id="fact-2",
                subject="fee",
                predicate="is",
                object="charge",
                domain="insurance",
                language="en",
                verification_score=0.2,
                verification_count=1,
            ),
        ]
        mock_adapter_class.return_value = mock_adapter

        result = runner.invoke(
            app,
            [
                "domain",
                "memory",
                "search",
                "premium",
                "--domain",
                "insurance",
                "--language",
                "en",
                "--min-score",
                "0.5",
                "--limit",
                "1",
            ],
        )

        assert result.exit_code == 0
        mock_adapter.search_facts.assert_called_once_with(
            query="premium",
            domain="insurance",
            language="en",
            limit=2,
        )
        assert "Factual Facts" in result.stdout


class TestDomainMemoryBehaviors:
    """Tests for 'evalvault domain memory behaviors' command."""

    @patch("evalvault.adapters.inbound.cli.commands.domain.build_domain_memory_adapter")
    def test_memory_behaviors_basic(self, mock_adapter_class, runner):
        """Test behaviors listing with filters."""
        from evalvault.domain.entities.memory import BehaviorEntry

        mock_adapter = MagicMock()
        mock_adapter.search_behaviors.return_value = [
            BehaviorEntry(
                behavior_id="behavior-1",
                description="Use clear bullet points",
                action_sequence=["step-1", "step-2"],
                success_rate=0.8,
                token_savings=12,
            )
        ]
        mock_adapter_class.return_value = mock_adapter

        result = runner.invoke(
            app,
            [
                "domain",
                "memory",
                "behaviors",
                "--domain",
                "insurance",
                "--language",
                "en",
                "--min-success",
                "0.5",
                "--limit",
                "1",
            ],
        )

        assert result.exit_code == 0
        mock_adapter.search_behaviors.assert_called_once_with(
            context="",
            domain="insurance",
            language="en",
            limit=3,
        )
        assert "Behavior Patterns" in result.stdout


class TestDomainMemoryLearnings:
    """Tests for 'evalvault domain memory learnings' command."""

    @patch("evalvault.adapters.inbound.cli.commands.domain.build_domain_memory_adapter")
    def test_memory_learnings_basic(self, mock_adapter_class, runner):
        """Test learnings listing."""
        from evalvault.domain.entities.memory import LearningMemory

        mock_adapter = MagicMock()
        mock_adapter.list_learnings.return_value = [
            LearningMemory(
                learning_id="learning-1",
                run_id="run-1",
                domain="insurance",
                language="en",
                successful_patterns=["pattern-a"],
                failed_patterns=["pattern-b"],
            )
        ]
        mock_adapter_class.return_value = mock_adapter

        result = runner.invoke(
            app,
            [
                "domain",
                "memory",
                "learnings",
                "--domain",
                "insurance",
                "--language",
                "en",
                "--limit",
                "1",
            ],
        )

        assert result.exit_code == 0
        mock_adapter.list_learnings.assert_called_once_with(
            domain="insurance",
            language="en",
            limit=1,
        )
        assert "Learning Memories" in result.stdout


class TestDomainMemoryEvolve:
    """Tests for 'evalvault domain memory evolve' command."""

    @patch("evalvault.adapters.inbound.cli.commands.domain.build_domain_memory_adapter")
    def test_memory_evolve_dry_run(self, mock_adapter_class, runner):
        """Test memory evolve dry run."""
        mock_adapter = MagicMock()
        mock_adapter.get_statistics.return_value = {
            "facts": 5,
            "learnings": 0,
            "behaviors": 1,
            "contexts": 0,
        }
        mock_adapter_class.return_value = mock_adapter

        result = runner.invoke(
            app,
            [
                "domain",
                "memory",
                "evolve",
                "--domain",
                "insurance",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        mock_adapter.get_statistics.assert_called_once_with(domain="insurance")
        assert "Dry run" in result.stdout

    @patch("evalvault.adapters.inbound.cli.commands.domain.DomainLearningHook")
    @patch("evalvault.adapters.inbound.cli.commands.domain.build_domain_memory_adapter")
    def test_memory_evolve_executes(self, mock_adapter_class, mock_hook_class, runner):
        """Test memory evolve execution path."""
        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        mock_hook = MagicMock()
        mock_hook.run_evolution.return_value = {
            "consolidated": 1,
            "forgotten": 2,
            "decayed": 3,
        }
        mock_hook_class.return_value = mock_hook

        result = runner.invoke(
            app,
            [
                "domain",
                "memory",
                "evolve",
                "--domain",
                "insurance",
                "--language",
                "en",
                "--yes",
            ],
        )

        assert result.exit_code == 0
        mock_hook_class.assert_called_once_with(mock_adapter)
        mock_hook.run_evolution.assert_called_once_with(domain="insurance", language="en")
        assert "completed" in result.stdout.lower()
