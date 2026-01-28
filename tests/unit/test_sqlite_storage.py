"""Unit tests for SQLite storage adapter."""

import json
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from evalvault.domain.entities import (
    EvaluationRun,
    MetricScore,
    MultiTurnConversationRecord,
    MultiTurnRunRecord,
    MultiTurnTurnResult,
    TestCaseResult,
)


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def storage_adapter(temp_db):
    """Create SQLiteStorageAdapter with temp database."""
    from evalvault.adapters.outbound.storage.sqlite_adapter import (
        SQLiteStorageAdapter,
    )

    return SQLiteStorageAdapter(db_path=temp_db)


@pytest.fixture
def sample_run():
    """Create a sample EvaluationRun for testing."""
    return EvaluationRun(
        run_id="test-run-001",
        dataset_name="insurance-qa",
        dataset_version="1.0.0",
        model_name="gpt-5-nano",
        started_at=datetime(2025, 1, 1, 10, 0, 0),
        finished_at=datetime(2025, 1, 1, 10, 5, 0),
        metrics_evaluated=["faithfulness", "answer_relevancy"],
        thresholds={"faithfulness": 0.7, "answer_relevancy": 0.7},
        total_tokens=1000,
        total_cost_usd=0.05,
        langfuse_trace_id="trace-123",
        tracker_metadata={
            "phoenix": {
                "prompts": [
                    {
                        "path": "agent/prompts/baseline.txt",
                        "status": "missing_file",
                    }
                ]
            }
        },
        results=[
            TestCaseResult(
                test_case_id="tc-001",
                metrics=[
                    MetricScore(name="faithfulness", score=0.85, threshold=0.7, reason="Good"),
                    MetricScore(
                        name="answer_relevancy",
                        score=0.90,
                        threshold=0.7,
                        reason="Excellent",
                    ),
                ],
                tokens_used=500,
                latency_ms=1200,
                cost_usd=0.025,
                trace_id="trace-tc-001",
                started_at=datetime(2025, 1, 1, 10, 0, 0),
                finished_at=datetime(2025, 1, 1, 10, 0, 1),
                question="What is the coverage amount?",
                answer="The coverage amount is 100 million won.",
                contexts=["The insurance coverage is 100 million won."],
                ground_truth="100 million won",
            ),
            TestCaseResult(
                test_case_id="tc-002",
                metrics=[
                    MetricScore(name="faithfulness", score=0.75, threshold=0.7, reason="OK"),
                    MetricScore(
                        name="answer_relevancy",
                        score=0.80,
                        threshold=0.7,
                        reason="Good",
                    ),
                ],
                tokens_used=500,
                latency_ms=1100,
                cost_usd=0.025,
                trace_id="trace-tc-002",
                started_at=datetime(2025, 1, 1, 10, 1, 0),
                finished_at=datetime(2025, 1, 1, 10, 1, 1),
                question="What is the premium?",
                answer="The monthly premium is 50,000 won.",
                contexts=["The monthly premium is 50,000 won."],
                ground_truth="50,000 won",
            ),
        ],
    )


class TestSQLiteStorageAdapter:
    """Test suite for SQLiteStorageAdapter."""

    def test_initialization_creates_tables(self, temp_db):
        """Test that initialization creates database and tables."""
        from evalvault.adapters.outbound.storage.sqlite_adapter import (
            SQLiteStorageAdapter,
        )

        SQLiteStorageAdapter(db_path=temp_db)

        # Verify tables exist
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "evaluation_runs" in tables
        assert "test_case_results" in tables
        assert "metric_scores" in tables
        assert "multiturn_runs" in tables
        assert "multiturn_conversations" in tables
        assert "multiturn_turn_results" in tables
        assert "multiturn_metric_scores" in tables

    def test_save_run_returns_run_id(self, storage_adapter, sample_run):
        """Test that save_run stores data and returns run_id."""
        run_id = storage_adapter.save_run(sample_run)
        assert run_id == "test-run-001"

    def test_save_run_stores_evaluation_run(self, storage_adapter, sample_run, temp_db):
        """Test that save_run correctly stores evaluation run data."""
        storage_adapter.save_run(sample_run)

        # Verify data in database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evaluation_runs WHERE run_id = ?", ("test-run-001",))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "test-run-001"  # run_id
        assert row[1] == "insurance-qa"  # dataset_name
        assert row[2] == "1.0.0"  # dataset_version
        assert row[3] == "gpt-5-nano"  # model_name
        assert row[6] == 1000  # total_tokens
        assert row[7] == 0.05  # total_cost_usd

    def test_save_run_stores_tracker_metadata(self, storage_adapter, sample_run, temp_db):
        """Ensure tracker metadata is persisted for prompt diff rendering."""
        storage_adapter.save_run(sample_run)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT metadata FROM evaluation_runs WHERE run_id = ?",
            ("test-run-001",),
        )
        raw_metadata = cursor.fetchone()[0]
        conn.close()

        assert raw_metadata is not None
        metadata = json.loads(raw_metadata)
        assert metadata["phoenix"]["prompts"][0]["status"] == "missing_file"

    def test_save_run_stores_retrieval_metadata(self, storage_adapter, temp_db):
        """Ensure retrieval metadata is persisted for later analysis."""
        run = EvaluationRun(
            run_id="retrieval-meta-001",
            dataset_name="insurance-qa",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 1, 10, 0, 0),
            retrieval_metadata={
                "tc-1": {"doc_ids": ["doc-1"], "top_k": 1, "scores": [0.9]},
            },
        )

        storage_adapter.save_run(run)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT retrieval_metadata FROM evaluation_runs WHERE run_id = ?",
            (run.run_id,),
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        raw_metadata = row[0]
        assert raw_metadata is not None
        stored = json.loads(raw_metadata)
        assert stored["tc-1"]["doc_ids"] == ["doc-1"]

    def test_save_multiturn_run_stores_records(self, storage_adapter, temp_db):
        run_record = MultiTurnRunRecord(
            run_id="mt-run-001",
            dataset_name="multiturn-qa",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 1, 10, 0, 0),
            finished_at=datetime(2025, 1, 1, 10, 5, 0),
            conversation_count=1,
            turn_count=2,
            metrics_evaluated=["turn_faithfulness"],
            drift_threshold=0.1,
            summary={"turn_faithfulness": 0.8},
        )
        conversations = [
            MultiTurnConversationRecord(
                run_id="mt-run-001",
                conversation_id="conv-001",
                turn_count=2,
                drift_score=0.2,
                drift_threshold=0.1,
                drift_detected=True,
                summary={"drift_score": 0.2},
            )
        ]
        turn_results = [
            MultiTurnTurnResult(
                conversation_id="conv-001",
                turn_id="t01",
                turn_index=1,
                role="assistant",
                metrics={"turn_faithfulness": 0.8},
                passed=True,
                latency_ms=1200,
            )
        ]

        storage_adapter.save_multiturn_run(run_record, conversations, turn_results)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM multiturn_runs")
        assert cursor.fetchone()[0] == 1
        cursor.execute("SELECT COUNT(*) FROM multiturn_conversations")
        assert cursor.fetchone()[0] == 1
        cursor.execute("SELECT COUNT(*) FROM multiturn_turn_results")
        assert cursor.fetchone()[0] == 1
        cursor.execute("SELECT COUNT(*) FROM multiturn_metric_scores")
        assert cursor.fetchone()[0] == 1
        conn.close()

    def test_save_run_stores_test_case_results(self, storage_adapter, sample_run, temp_db):
        """Test that save_run stores test case results."""
        storage_adapter.save_run(sample_run)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM test_case_results WHERE run_id = ?",
            ("test-run-001",),
        )
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2

    def test_save_run_stores_metric_scores(self, storage_adapter, sample_run, temp_db):
        """Test that save_run stores metric scores."""
        storage_adapter.save_run(sample_run)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM metric_scores ms
            JOIN test_case_results tcr ON ms.result_id = tcr.id
            WHERE tcr.run_id = ?
            """,
            ("test-run-001",),
        )
        count = cursor.fetchone()[0]
        conn.close()

        # 2 test cases × 2 metrics = 4 scores
        assert count == 4

    def test_get_run_returns_stored_run(self, storage_adapter, sample_run):
        """Test that get_run retrieves stored EvaluationRun."""
        storage_adapter.save_run(sample_run)
        retrieved_run = storage_adapter.get_run("test-run-001")

        assert retrieved_run.run_id == sample_run.run_id
        assert retrieved_run.dataset_name == sample_run.dataset_name
        assert retrieved_run.model_name == sample_run.model_name
        assert retrieved_run.total_tokens == sample_run.total_tokens
        assert len(retrieved_run.results) == 2
        assert retrieved_run.tracker_metadata == sample_run.tracker_metadata

    def test_get_run_raises_key_error_for_nonexistent_run(self, storage_adapter):
        """Test that get_run raises KeyError for non-existent run_id."""
        with pytest.raises(KeyError, match="Run not found: nonexistent-run"):
            storage_adapter.get_run("nonexistent-run")

    def test_get_run_reconstructs_test_case_results(self, storage_adapter, sample_run):
        """Test that get_run correctly reconstructs TestCaseResult objects."""
        storage_adapter.save_run(sample_run)
        retrieved_run = storage_adapter.get_run("test-run-001")

        result = retrieved_run.results[0]
        assert result.test_case_id == "tc-001"
        assert result.tokens_used == 500
        assert result.latency_ms == 1200
        assert result.cost_usd == 0.025
        assert result.question == "What is the coverage amount?"
        assert len(result.contexts) == 1

    def test_get_run_reconstructs_metric_scores(self, storage_adapter, sample_run):
        """Test that get_run correctly reconstructs MetricScore objects."""
        storage_adapter.save_run(sample_run)
        retrieved_run = storage_adapter.get_run("test-run-001")

        result = retrieved_run.results[0]
        assert len(result.metrics) == 2

        faithfulness = result.get_metric("faithfulness")
        assert faithfulness is not None
        assert faithfulness.score == 0.85
        assert faithfulness.threshold == 0.7
        assert faithfulness.reason == "Good"

    def test_list_runs_returns_all_runs(self, storage_adapter, sample_run):
        """Test that list_runs returns all stored runs."""
        # Create multiple runs
        run1 = sample_run
        run2 = EvaluationRun(
            run_id="test-run-002",
            dataset_name="insurance-qa",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 2, 10, 0, 0),
        )

        storage_adapter.save_run(run1)
        storage_adapter.save_run(run2)

        runs = storage_adapter.list_runs()
        assert len(runs) == 2

    def test_list_runs_filters_by_dataset_name(self, storage_adapter, sample_run):
        """Test that list_runs filters by dataset_name."""
        run1 = sample_run
        run2 = EvaluationRun(
            run_id="test-run-002",
            dataset_name="medical-qa",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 2, 10, 0, 0),
        )

        storage_adapter.save_run(run1)
        storage_adapter.save_run(run2)

        runs = storage_adapter.list_runs(dataset_name="insurance-qa")
        assert len(runs) == 1
        assert runs[0].dataset_name == "insurance-qa"

    def test_list_runs_filters_by_model_name(self, storage_adapter, sample_run):
        """Test that list_runs filters by model_name."""
        run1 = sample_run
        run2 = EvaluationRun(
            run_id="test-run-002",
            dataset_name="insurance-qa",
            dataset_version="1.0.0",
            model_name="gpt-4",
            started_at=datetime(2025, 1, 2, 10, 0, 0),
        )

        storage_adapter.save_run(run1)
        storage_adapter.save_run(run2)

        runs = storage_adapter.list_runs(model_name="gpt-5-nano")
        assert len(runs) == 1
        assert runs[0].model_name == "gpt-5-nano"

    def test_list_runs_respects_limit(self, storage_adapter):
        """Test that list_runs respects the limit parameter."""
        for i in range(5):
            run = EvaluationRun(
                run_id=f"test-run-{i:03d}",
                dataset_name="insurance-qa",
                dataset_version="1.0.0",
                model_name="gpt-5-nano",
                started_at=datetime(2025, 1, i + 1, 10, 0, 0),
            )
            storage_adapter.save_run(run)

        runs = storage_adapter.list_runs(limit=3)
        assert len(runs) == 3

    def test_list_runs_returns_latest_first(self, storage_adapter):
        """Test that list_runs returns runs in descending order by started_at."""
        run1 = EvaluationRun(
            run_id="test-run-001",
            dataset_name="insurance-qa",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 1, 10, 0, 0),
        )
        run2 = EvaluationRun(
            run_id="test-run-002",
            dataset_name="insurance-qa",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 2, 10, 0, 0),
        )

        storage_adapter.save_run(run1)
        storage_adapter.save_run(run2)

        runs = storage_adapter.list_runs()
        assert runs[0].run_id == "test-run-002"  # Latest first
        assert runs[1].run_id == "test-run-001"

    def test_delete_run_removes_run(self, storage_adapter, sample_run, temp_db):
        """Test that delete_run removes run and related data."""
        storage_adapter.save_run(sample_run)
        result = storage_adapter.delete_run("test-run-001")

        assert result is True

        # Verify run is deleted
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM evaluation_runs WHERE run_id = ?", ("test-run-001",))
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 0

    def test_delete_run_cascades_to_results(self, storage_adapter, sample_run, temp_db):
        """Test that delete_run cascades to test_case_results."""
        storage_adapter.save_run(sample_run)
        storage_adapter.delete_run("test-run-001")

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM test_case_results WHERE run_id = ?",
            ("test-run-001",),
        )
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 0

    def test_delete_run_returns_false_for_nonexistent_run(self, storage_adapter):
        """Test that delete_run returns False for non-existent run."""
        result = storage_adapter.delete_run("nonexistent-run")
        assert result is False

    def test_save_run_with_no_results(self, storage_adapter):
        """Test saving a run with no test case results."""
        run = EvaluationRun(
            run_id="test-run-003",
            dataset_name="insurance-qa",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 1, 10, 0, 0),
            results=[],
        )

        run_id = storage_adapter.save_run(run)
        assert run_id == "test-run-003"

        retrieved_run = storage_adapter.get_run("test-run-003")
        assert len(retrieved_run.results) == 0


class TestSQLiteStorageNLPAnalysis:
    """NLP 분석 결과 저장 테스트."""

    @pytest.fixture
    def sample_run_for_analysis(self, storage_adapter):
        """NLP 분석 테스트를 위한 샘플 run 생성."""
        run = EvaluationRun(
            run_id="test-run-001",
            dataset_name="test-dataset",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 1, 10, 0, 0),
        )
        storage_adapter.save_run(run)
        return run

    @pytest.fixture
    def sample_nlp_analysis(self, sample_run_for_analysis):
        """테스트용 NLP 분석 결과."""
        from evalvault.domain.entities.analysis import (
            KeywordInfo,
            NLPAnalysis,
            QuestionType,
            QuestionTypeStats,
            TextStats,
            TopicCluster,
        )

        return NLPAnalysis(
            run_id=sample_run_for_analysis.run_id,
            question_stats=TextStats(
                char_count=100,
                word_count=20,
                sentence_count=2,
                avg_word_length=4.5,
                unique_word_ratio=0.9,
            ),
            answer_stats=TextStats(
                char_count=200,
                word_count=40,
                sentence_count=4,
                avg_word_length=4.0,
                unique_word_ratio=0.85,
            ),
            question_types=[
                QuestionTypeStats(
                    question_type=QuestionType.FACTUAL,
                    count=5,
                    percentage=0.5,
                    avg_scores={"faithfulness": 0.85},
                ),
                QuestionTypeStats(
                    question_type=QuestionType.REASONING,
                    count=3,
                    percentage=0.3,
                    avg_scores={"faithfulness": 0.75},
                ),
            ],
            top_keywords=[
                KeywordInfo(keyword="보험", frequency=5, tfidf_score=0.8),
                KeywordInfo(keyword="보장금액", frequency=3, tfidf_score=0.6),
            ],
            topic_clusters=[
                TopicCluster(
                    cluster_id=0,
                    keywords=["보험", "갱신"],
                    document_count=4,
                    avg_scores={"faithfulness": 0.7},
                    representative_questions=["보험 갱신 주기를 알려줘"],
                )
            ],
            insights=["High vocabulary diversity", "Questions are well-formed"],
        )

    def test_save_nlp_analysis_returns_id(self, storage_adapter, sample_nlp_analysis):
        """NLP 분석 저장 시 ID 반환."""
        analysis_id = storage_adapter.save_nlp_analysis(sample_nlp_analysis)

        assert analysis_id is not None
        assert analysis_id.startswith("nlp-test-run-001-")

    def test_get_nlp_analysis_retrieves_stored_data(self, storage_adapter, sample_nlp_analysis):
        """저장된 NLP 분석 결과 조회."""
        analysis_id = storage_adapter.save_nlp_analysis(sample_nlp_analysis)
        retrieved = storage_adapter.get_nlp_analysis(analysis_id)

        assert retrieved.run_id == sample_nlp_analysis.run_id
        assert retrieved.question_stats.char_count == 100
        assert retrieved.question_stats.word_count == 20
        assert retrieved.answer_stats.char_count == 200

    def test_get_nlp_analysis_reconstructs_question_types(
        self, storage_adapter, sample_nlp_analysis
    ):
        """QuestionTypeStats 복원 확인."""
        from evalvault.domain.entities.analysis import QuestionType

        analysis_id = storage_adapter.save_nlp_analysis(sample_nlp_analysis)
        retrieved = storage_adapter.get_nlp_analysis(analysis_id)

        assert len(retrieved.question_types) == 2
        assert retrieved.question_types[0].question_type == QuestionType.FACTUAL
        assert retrieved.question_types[0].count == 5
        assert retrieved.question_types[0].avg_scores["faithfulness"] == 0.85

    def test_get_nlp_analysis_reconstructs_keywords(self, storage_adapter, sample_nlp_analysis):
        """KeywordInfo 복원 확인."""
        analysis_id = storage_adapter.save_nlp_analysis(sample_nlp_analysis)
        retrieved = storage_adapter.get_nlp_analysis(analysis_id)

        assert len(retrieved.top_keywords) == 2
        assert retrieved.top_keywords[0].keyword == "보험"
        assert retrieved.top_keywords[0].frequency == 5
        assert retrieved.top_keywords[0].tfidf_score == 0.8

    def test_get_nlp_analysis_reconstructs_insights(self, storage_adapter, sample_nlp_analysis):
        """인사이트 복원 확인."""
        analysis_id = storage_adapter.save_nlp_analysis(sample_nlp_analysis)
        retrieved = storage_adapter.get_nlp_analysis(analysis_id)

        assert len(retrieved.insights) == 2
        assert "High vocabulary diversity" in retrieved.insights

    def test_get_nlp_analysis_reconstructs_topic_clusters(
        self, storage_adapter, sample_nlp_analysis
    ):
        """TopicCluster 복원 확인."""
        analysis_id = storage_adapter.save_nlp_analysis(sample_nlp_analysis)
        retrieved = storage_adapter.get_nlp_analysis(analysis_id)

        assert len(retrieved.topic_clusters) == 1
        cluster = retrieved.topic_clusters[0]
        assert cluster.keywords == ["보험", "갱신"]
        assert cluster.avg_scores["faithfulness"] == 0.7
        assert cluster.representative_questions[0].startswith("보험 갱신")

    def test_get_nlp_analysis_raises_key_error(self, storage_adapter):
        """존재하지 않는 분석 조회 시 KeyError."""
        with pytest.raises(KeyError, match="NLP Analysis not found"):
            storage_adapter.get_nlp_analysis("nonexistent-id")

    def test_get_nlp_analysis_by_run_returns_latest(self, storage_adapter, sample_nlp_analysis):
        """run_id로 최신 NLP 분석 조회."""
        # 두 개의 분석 저장
        storage_adapter.save_nlp_analysis(sample_nlp_analysis)
        storage_adapter.save_nlp_analysis(sample_nlp_analysis)

        retrieved = storage_adapter.get_nlp_analysis_by_run("test-run-001")

        assert retrieved is not None
        assert retrieved.run_id == "test-run-001"

    def test_get_nlp_analysis_by_run_returns_none(self, storage_adapter):
        """분석 없는 run_id 조회 시 None 반환."""
        retrieved = storage_adapter.get_nlp_analysis_by_run("nonexistent-run")
        assert retrieved is None

    def test_save_nlp_analysis_with_minimal_data(self, storage_adapter):
        """최소 데이터로 NLP 분석 저장."""
        from evalvault.domain.entities.analysis import NLPAnalysis

        # 먼저 run 생성
        run = EvaluationRun(
            run_id="test-run-002",
            dataset_name="test-dataset",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 1, 10, 0, 0),
        )
        storage_adapter.save_run(run)

        analysis = NLPAnalysis(run_id="test-run-002")

        analysis_id = storage_adapter.save_nlp_analysis(analysis)
        retrieved = storage_adapter.get_nlp_analysis(analysis_id)

        assert retrieved.run_id == "test-run-002"
        assert retrieved.question_stats is None
        assert retrieved.answer_stats is None
        assert len(retrieved.question_types) == 0
        assert len(retrieved.top_keywords) == 0

    def test_feedback_roundtrip(self, storage_adapter, sample_run):
        storage_adapter.save_run(sample_run)

        from evalvault.domain.entities import SatisfactionFeedback

        feedback = SatisfactionFeedback(
            feedback_id="",
            run_id=sample_run.run_id,
            test_case_id="tc-001",
            satisfaction_score=4.0,
            thumb_feedback="up",
            comment="좋아요",
            rater_id="user-1",
        )

        feedback_id = storage_adapter.save_feedback(feedback)
        feedbacks = storage_adapter.list_feedback(sample_run.run_id)

        assert feedbacks
        assert feedbacks[0].feedback_id == str(feedback_id)
        assert feedbacks[0].satisfaction_score == 4.0
        assert feedbacks[0].thumb_feedback == "up"

        summary = storage_adapter.get_feedback_summary(sample_run.run_id)
        assert summary.total_feedback == 1
        assert summary.avg_satisfaction_score == 4.0
        assert summary.thumb_up_rate == 1.0

    def test_feedback_summary_uses_latest(self, storage_adapter, sample_run):
        storage_adapter.save_run(sample_run)

        from evalvault.domain.entities import SatisfactionFeedback

        base_time = datetime.now()
        feedback = SatisfactionFeedback(
            feedback_id="",
            run_id=sample_run.run_id,
            test_case_id="tc-001",
            satisfaction_score=None,
            thumb_feedback="up",
            comment=None,
            rater_id="user-1",
            created_at=base_time,
        )
        storage_adapter.save_feedback(feedback)

        cancel = SatisfactionFeedback(
            feedback_id="",
            run_id=sample_run.run_id,
            test_case_id="tc-001",
            satisfaction_score=None,
            thumb_feedback=None,
            comment=None,
            rater_id="user-1",
            created_at=base_time + timedelta(seconds=1),
        )
        storage_adapter.save_feedback(cancel)

        summary = storage_adapter.get_feedback_summary(sample_run.run_id)
        assert summary.total_feedback == 0
        assert summary.avg_satisfaction_score is None
        assert summary.thumb_up_rate is None


class TestSQLiteStorageRegressionBaseline:
    def test_set_and_get_regression_baseline(self, storage_adapter, sample_run):
        storage_adapter.save_run(sample_run)

        storage_adapter.set_regression_baseline(
            "default",
            sample_run.run_id,
            dataset_name="insurance-qa",
            branch="main",
            commit_sha="abc123",
            metadata={"ci": True},
        )

        baseline = storage_adapter.get_regression_baseline("default")

        assert baseline is not None
        assert baseline["baseline_key"] == "default"
        assert baseline["run_id"] == sample_run.run_id
        assert baseline["dataset_name"] == "insurance-qa"
        assert baseline["branch"] == "main"
        assert baseline["commit_sha"] == "abc123"
        assert baseline["metadata"] == {"ci": True}
        assert baseline["created_at"] is not None
        assert baseline["updated_at"] is not None

    def test_get_regression_baseline_not_found(self, storage_adapter):
        baseline = storage_adapter.get_regression_baseline("nonexistent")
        assert baseline is None

    def test_set_regression_baseline_updates_existing(self, storage_adapter, sample_run):
        storage_adapter.save_run(sample_run)

        storage_adapter.set_regression_baseline(
            "default",
            sample_run.run_id,
            branch="feature-1",
        )

        run2 = EvaluationRun(
            run_id="test-run-002",
            dataset_name="insurance-qa",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 2, 10, 0, 0),
        )
        storage_adapter.save_run(run2)

        storage_adapter.set_regression_baseline(
            "default",
            run2.run_id,
            branch="main",
        )

        baseline = storage_adapter.get_regression_baseline("default")

        assert baseline is not None
        assert baseline["run_id"] == run2.run_id
        assert baseline["branch"] == "main"

    def test_multiple_baseline_keys(self, storage_adapter, sample_run):
        storage_adapter.save_run(sample_run)

        run2 = EvaluationRun(
            run_id="test-run-002",
            dataset_name="medical-qa",
            dataset_version="1.0.0",
            model_name="gpt-5-nano",
            started_at=datetime(2025, 1, 2, 10, 0, 0),
        )
        storage_adapter.save_run(run2)

        storage_adapter.set_regression_baseline(
            "insurance",
            sample_run.run_id,
            dataset_name="insurance-qa",
        )
        storage_adapter.set_regression_baseline(
            "medical",
            run2.run_id,
            dataset_name="medical-qa",
        )

        baseline1 = storage_adapter.get_regression_baseline("insurance")
        baseline2 = storage_adapter.get_regression_baseline("medical")

        assert baseline1["run_id"] == sample_run.run_id
        assert baseline1["dataset_name"] == "insurance-qa"
        assert baseline2["run_id"] == run2.run_id
        assert baseline2["dataset_name"] == "medical-qa"

    def test_set_regression_baseline_minimal(self, storage_adapter, sample_run):
        storage_adapter.save_run(sample_run)

        storage_adapter.set_regression_baseline("minimal", sample_run.run_id)

        baseline = storage_adapter.get_regression_baseline("minimal")

        assert baseline is not None
        assert baseline["run_id"] == sample_run.run_id
        assert baseline["dataset_name"] is None
        assert baseline["branch"] is None
        assert baseline["commit_sha"] is None
        assert baseline["metadata"] is None
