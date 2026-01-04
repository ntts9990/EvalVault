"""Tests for domain memory CLI commands."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from evalvault.adapters.inbound.cli import app


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_config_dir(tmp_path):
    """Temporary config directory."""
    config_dir = tmp_path / "config" / "domains"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


class TestDomainInit:
    """Tests for 'evalvault domain init' command."""

    def test_domain_init_basic(self, runner, tmp_path, monkeypatch):
        """Test basic domain initialization."""
        # Change working directory to tmp_path
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["domain", "init", "insurance"])

        assert result.exit_code == 0
        assert "Initializing domain: insurance" in result.stdout

        # Check that config directory was created
        domain_dir = tmp_path / "config" / "domains" / "insurance"
        assert domain_dir.exists()

        # Check that config file exists
        config_file = domain_dir / "config.yaml"
        assert config_file.exists()

    def test_domain_init_with_languages(self, runner, tmp_path, monkeypatch):
        """Test domain init with custom languages."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            app,
            ["domain", "init", "medical", "--languages", "en"],
        )

        assert result.exit_code == 0
        assert "Languages: en" in result.stdout

    def test_domain_init_with_description(self, runner, tmp_path, monkeypatch):
        """Test domain init with description."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            app,
            [
                "domain",
                "init",
                "insurance",
                "--description",
                "Insurance domain for RAG evaluation",
            ],
        )

        assert result.exit_code == 0
        assert "Insurance domain for RAG evaluation" in result.stdout

    def test_domain_init_existing_without_force(self, runner, tmp_path, monkeypatch):
        """Test that init fails on existing domain without --force."""
        monkeypatch.chdir(tmp_path)

        # Create domain first
        domain_dir = tmp_path / "config" / "domains" / "insurance"
        domain_dir.mkdir(parents=True, exist_ok=True)

        result = runner.invoke(app, ["domain", "init", "insurance"])

        assert result.exit_code == 1
        assert "already exists" in result.stdout

    def test_domain_init_existing_with_force(self, runner, tmp_path, monkeypatch):
        """Test that init overwrites existing domain with --force."""
        monkeypatch.chdir(tmp_path)

        # Create domain first
        domain_dir = tmp_path / "config" / "domains" / "insurance"
        domain_dir.mkdir(parents=True, exist_ok=True)

        result = runner.invoke(app, ["domain", "init", "insurance", "--force"])

        assert result.exit_code == 0


class TestDomainList:
    """Tests for 'evalvault domain list' command."""

    def test_domain_list_empty(self, runner, tmp_path, monkeypatch):
        """Test listing domains when none exist."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["domain", "list"])

        assert result.exit_code == 0
        assert "No domains found" in result.stdout or "Domain" in result.stdout

    def test_domain_list_with_domains(self, runner, tmp_path, monkeypatch):
        """Test listing existing domains."""
        monkeypatch.chdir(tmp_path)

        # Create a few domains
        config_dir = tmp_path / "config" / "domains"
        for domain in ["insurance", "medical"]:
            domain_dir = config_dir / domain
            domain_dir.mkdir(parents=True, exist_ok=True)

            # Create minimal config file
            config_file = domain_dir / "config.yaml"
            config_file.write_text(f"domain: {domain}\nversion: '1.0.0'\nlanguages: [ko, en]\n")

        result = runner.invoke(app, ["domain", "list"])

        assert result.exit_code == 0
        # Check output contains domain information
        assert "insurance" in result.stdout or "Domain" in result.stdout


class TestDomainStats:
    """Tests for 'evalvault domain stats' command."""

    @patch("evalvault.adapters.inbound.cli.commands.domain.SQLiteDomainMemoryAdapter")
    def test_domain_stats_basic(self, mock_adapter_class, runner):
        """Test domain stats display."""
        # Mock the adapter
        mock_adapter = MagicMock()
        mock_adapter.count_facts.return_value = 100
        mock_adapter.count_facts_by_type.return_value = {
            "term_definition": 50,
            "metric_constraint": 30,
            "qa_pattern": 20,
        }
        mock_adapter_class.return_value = mock_adapter

        result = runner.invoke(app, ["domain", "stats", "insurance"])

        assert result.exit_code == 0
        assert "insurance" in result.stdout.lower()

    @patch("evalvault.adapters.inbound.cli.commands.domain.SQLiteDomainMemoryAdapter")
    def test_domain_stats_with_db_path(self, mock_adapter_class, runner, tmp_path):
        """Test domain stats with custom database path."""
        mock_adapter = MagicMock()
        mock_adapter.count_facts.return_value = 0
        mock_adapter.count_facts_by_type.return_value = {}
        mock_adapter_class.return_value = mock_adapter

        db_path = tmp_path / "test.db"
        result = runner.invoke(
            app,
            ["domain", "stats", "insurance", "--memory-db", str(db_path)],
        )

        assert result.exit_code == 0


class TestDomainQuery:
    """Tests for 'evalvault domain query' command."""

    @patch("evalvault.adapters.inbound.cli.commands.domain.SQLiteDomainMemoryAdapter")
    def test_domain_query_basic(self, mock_adapter_class, runner):
        """Test querying domain facts."""
        from evalvault.domain.entities.memory import Fact, FactType

        mock_adapter = MagicMock()
        mock_adapter.query_facts.return_value = [
            Fact(
                fact_type=FactType.TERM_DEFINITION,
                key="보험료",
                value="Insurance premium",
                domain="insurance",
            )
        ]
        mock_adapter_class.return_value = mock_adapter

        result = runner.invoke(
            app,
            ["domain", "query", "insurance", "--fact-type", "term_definition"],
        )

        assert result.exit_code == 0

    @patch("evalvault.adapters.inbound.cli.commands.domain.SQLiteDomainMemoryAdapter")
    def test_domain_query_with_limit(self, mock_adapter_class, runner):
        """Test querying with limit."""
        mock_adapter = MagicMock()
        mock_adapter.query_facts.return_value = []
        mock_adapter_class.return_value = mock_adapter

        result = runner.invoke(
            app,
            [
                "domain",
                "query",
                "insurance",
                "--fact-type",
                "term_definition",
                "--limit",
                "5",
            ],
        )

        assert result.exit_code == 0


class TestDomainExport:
    """Tests for 'evalvault domain export' command."""

    @patch("evalvault.adapters.inbound.cli.commands.domain.SQLiteDomainMemoryAdapter")
    def test_domain_export_json(self, mock_adapter_class, runner, tmp_path):
        """Test exporting domain to JSON."""
        from evalvault.domain.entities.memory import Fact, FactType

        mock_adapter = MagicMock()
        mock_adapter.query_facts.return_value = [
            Fact(
                fact_type=FactType.TERM_DEFINITION,
                key="보험료",
                value="Insurance premium",
                domain="insurance",
            )
        ]
        mock_adapter_class.return_value = mock_adapter

        output_file = tmp_path / "export.json"
        result = runner.invoke(
            app,
            ["domain", "export", "insurance", str(output_file)],
        )

        assert result.exit_code == 0
        assert output_file.exists()

    @patch("evalvault.adapters.inbound.cli.commands.domain.SQLiteDomainMemoryAdapter")
    def test_domain_export_csv(self, mock_adapter_class, runner, tmp_path):
        """Test exporting domain to CSV."""
        from evalvault.domain.entities.memory import Fact, FactType

        mock_adapter = MagicMock()
        mock_adapter.query_facts.return_value = [
            Fact(
                fact_type=FactType.TERM_DEFINITION,
                key="보험료",
                value="Insurance premium",
                domain="insurance",
            )
        ]
        mock_adapter_class.return_value = mock_adapter

        output_file = tmp_path / "export.csv"
        result = runner.invoke(
            app,
            ["domain", "export", "insurance", str(output_file), "--format", "csv"],
        )

        assert result.exit_code == 0
        assert output_file.exists()


class TestDomainImport:
    """Tests for 'evalvault domain import' command."""

    @patch("evalvault.adapters.inbound.cli.commands.domain.SQLiteDomainMemoryAdapter")
    def test_domain_import_json(self, mock_adapter_class, runner, tmp_path):
        """Test importing domain from JSON."""
        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        # Create sample JSON file
        import_file = tmp_path / "import.json"
        import_file.write_text(
            """[
            {
                "fact_type": "term_definition",
                "key": "보험료",
                "value": "Insurance premium",
                "domain": "insurance"
            }
        ]"""
        )

        result = runner.invoke(
            app,
            ["domain", "import", "insurance", str(import_file)],
        )

        assert result.exit_code == 0


class TestDomainLearn:
    """Tests for 'evalvault domain learn' command."""

    @patch("evalvault.adapters.inbound.cli.commands.domain.SQLiteDomainMemoryAdapter")
    @patch("evalvault.adapters.inbound.cli.commands.domain.DomainLearningHook")
    @patch("evalvault.adapters.inbound.cli.commands.domain.load_domain_config")
    def test_domain_learn_basic(
        self, mock_load_config, mock_hook_class, mock_adapter_class, runner, tmp_path
    ):
        """Test learning from evaluation run."""
        from evalvault.domain.entities import EvaluationRun

        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        mock_hook = MagicMock()
        mock_hook_class.return_value = mock_hook

        mock_config = MagicMock()
        mock_config.domain = "insurance"
        mock_config.languages = ["ko", "en"]
        mock_load_config.return_value = mock_config

        # Create a mock storage with a run
        with patch(
            "evalvault.adapters.inbound.cli.commands.domain.SQLiteStorageAdapter"
        ) as mock_storage_class:
            mock_storage = MagicMock()
            mock_storage.get_run.return_value = MagicMock(spec=EvaluationRun)
            mock_storage_class.return_value = mock_storage

            result = runner.invoke(
                app,
                ["domain", "learn", "insurance", "run-123"],
            )

            assert result.exit_code == 0


class TestDomainCluster:
    """Tests for 'evalvault domain cluster' command."""

    @patch("evalvault.adapters.inbound.cli.commands.domain.SQLiteDomainMemoryAdapter")
    @patch("evalvault.adapters.inbound.cli.commands.domain.build_cluster_facts")
    @patch("evalvault.adapters.outbound.llm.get_llm_adapter")
    def test_domain_cluster_basic(
        self, mock_get_llm, mock_build_cluster, mock_adapter_class, runner
    ):
        """Test clustering domain facts."""
        mock_adapter = MagicMock()
        mock_adapter.query_facts.return_value = []
        mock_adapter_class.return_value = mock_adapter

        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        mock_build_cluster.return_value = []

        result = runner.invoke(
            app,
            ["domain", "cluster", "insurance"],
        )

        assert result.exit_code == 0
