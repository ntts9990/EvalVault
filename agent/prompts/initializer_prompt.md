## YOUR ROLE - TEST SUITE INITIALIZER

You are initializing a comprehensive integration test suite for EvalVault Web UI evaluation features.
This is the FIRST session - you'll create the test structure and initial tests.

---

## UNDERSTANDING THE CONTEXT

All Web UI evaluation features are already implemented:
- Dependency injection (create_adapter)
- File upload to Dataset conversion
- Evaluation execution
- Result storage
- Report generation

**Your job:** Create integration tests to verify these features work correctly.

---

## STEP 1: READ THE SPECIFICATION

```bash
cat prompts/app_spec.txt
cat claude-progress.txt 2>/dev/null || echo "No analysis yet"
```

---

## STEP 2: CREATE TEST STRUCTURE

Set up the integration test file:

```bash
# Create directory if needed
mkdir -p tests/integration

# Create fixtures directory
mkdir -p tests/fixtures/web_ui_test_data

# List existing tests for pattern reference
ls -la tests/integration/
```

---

## STEP 3: CREATE INITIAL TEST FILE

Create `tests/integration/test_web_ui_evaluation.py`:

```python
"""Integration tests for Web UI evaluation features.

Tests the complete Web UI evaluation workflow:
- File upload to Dataset conversion
- Evaluation execution with metrics
- Result storage and retrieval
- Report generation
"""

import json
import pytest
from pathlib import Path

from evalvault.adapters.inbound.web.adapter import WebUIAdapter, create_adapter
from evalvault.domain.entities.dataset import Dataset, TestCase
from evalvault.domain.entities.result import EvaluationRun


@pytest.fixture
def sample_json_content():
    """Sample JSON dataset content for testing."""
    return {
        "name": "test-dataset",
        "version": "1.0.0",
        "thresholds": {
            "faithfulness": 0.8,
            "answer_relevancy": 0.7
        },
        "test_cases": [
            {
                "id": "tc-001",
                "question": "What is the coverage amount?",
                "answer": "The coverage is 100M KRW.",
                "contexts": ["Life insurance coverage: 100M KRW"],
                "ground_truth": "100M KRW"
            },
            {
                "id": "tc-002",
                "question": "What is the premium?",
                "answer": "Monthly premium is 50K KRW.",
                "contexts": ["Premium payment: 50,000 KRW per month"],
                "ground_truth": "50K KRW per month"
            }
        ]
    }


@pytest.fixture
def sample_csv_content():
    """Sample CSV dataset content for testing."""
    return (
        b'id,question,answer,contexts,ground_truth\n'
        b'tc-001,"What is covered?","Insurance covers life.","[""Life insurance policy""]","Life insurance"\n'
    )


class TestDatasetConversion:
    """Test file upload to Dataset conversion."""

    def test_create_dataset_from_json_upload(self, sample_json_content):
        """Test converting JSON upload to Dataset."""
        # Arrange
        adapter = create_adapter()
        json_bytes = json.dumps(sample_json_content).encode('utf-8')

        # Act
        dataset = adapter.create_dataset_from_upload(
            "test_data.json",
            json_bytes
        )

        # Assert
        assert isinstance(dataset, Dataset)
        assert dataset.name == "test-dataset"
        assert dataset.version == "1.0.0"
        assert len(dataset.test_cases) == 2
        assert dataset.test_cases[0].id == "tc-001"
        assert dataset.thresholds["faithfulness"] == 0.8

    def test_create_dataset_from_csv_upload(self, sample_csv_content):
        """Test converting CSV upload to Dataset."""
        # Arrange
        adapter = create_adapter()

        # Act
        dataset = adapter.create_dataset_from_upload(
            "test_data.csv",
            sample_csv_content
        )

        # Assert
        assert isinstance(dataset, Dataset)
        assert len(dataset.test_cases) > 0
        assert dataset.test_cases[0].question == "What is covered?"


class TestEvaluationExecution:
    """Test evaluation execution flow."""

    @pytest.mark.requires_openai
    def test_run_evaluation_with_dataset(self, sample_json_content, tmp_path):
        """Test running evaluation with dataset."""
        # Arrange
        adapter = create_adapter()
        json_bytes = json.dumps(sample_json_content).encode('utf-8')
        dataset = adapter.create_dataset_from_upload("test.json", json_bytes)

        # Act
        result = adapter.run_evaluation_with_dataset(
            dataset=dataset,
            metrics=["faithfulness"],
            thresholds={"faithfulness": 0.7},
            parallel=False,
            batch_size=5
        )

        # Assert
        assert isinstance(result, EvaluationRun)
        assert result.total_test_cases == 2
        assert "faithfulness" in result.metrics_evaluated
        assert result.run_id is not None

    def test_run_evaluation_without_llm_raises_error(self, sample_json_content):
        """Test evaluation without LLM adapter raises error."""
        # Arrange
        adapter = WebUIAdapter(llm_adapter=None)
        json_bytes = json.dumps(sample_json_content).encode('utf-8')
        dataset = adapter.create_dataset_from_upload("test.json", json_bytes)

        # Act & Assert
        with pytest.raises(RuntimeError, match="LLM adapter not configured"):
            adapter.run_evaluation_with_dataset(
                dataset=dataset,
                metrics=["faithfulness"]
            )


# More test classes will be added by subsequent sessions
```

---

## STEP 4: CREATE feature_list.json

Document remaining tests to write:

```bash
cat > feature_list.json << 'EOF'
[
  {
    "category": "test",
    "description": "Create initial integration test structure and basic tests",
    "steps": [
      "Step 1: Create tests/integration/test_web_ui_evaluation.py",
      "Step 2: Add TestDatasetConversion class with JSON/CSV tests",
      "Step 3: Add TestEvaluationExecution class with basic evaluation test",
      "Step 4: Verify tests pass"
    ],
    "passes": false
  },
  {
    "category": "test",
    "description": "Add integration test for Excel file upload",
    "steps": [
      "Step 1: Create sample Excel test file",
      "Step 2: Test create_dataset_from_upload with .xlsx",
      "Step 3: Verify Dataset conversion",
      "Step 4: Test error handling"
    ],
    "passes": false
  },
  {
    "category": "test",
    "description": "Add integration test for parallel vs sequential evaluation",
    "steps": [
      "Step 1: Create dataset with 4+ test cases",
      "Step 2: Run evaluation in parallel=True mode",
      "Step 3: Run evaluation in parallel=False mode",
      "Step 4: Compare results and verify consistency"
    ],
    "passes": false
  },
  {
    "category": "test",
    "description": "Add integration test for storage integration",
    "steps": [
      "Step 1: Run evaluation with storage",
      "Step 2: Verify result saved to database",
      "Step 3: Retrieve result by run_id",
      "Step 4: Verify retrieved data matches original"
    ],
    "passes": false
  },
  {
    "category": "test",
    "description": "Add integration test for LLM report generation",
    "steps": [
      "Step 1: Run evaluation and get run_id",
      "Step 2: Call generate_llm_report(run_id)",
      "Step 3: Verify LLMReport structure",
      "Step 4: Check metrics analysis content"
    ],
    "passes": false
  },
  {
    "category": "test",
    "description": "Add integration test for quality gate checks",
    "steps": [
      "Step 1: Run evaluation with known scores",
      "Step 2: Test quality gate with passing scores",
      "Step 3: Test quality gate with failing scores",
      "Step 4: Verify quality gate result structure"
    ],
    "passes": false
  },
  {
    "category": "test",
    "description": "Add error handling tests",
    "steps": [
      "Step 1: Test invalid file formats",
      "Step 2: Test empty datasets",
      "Step 3: Test invalid metric names",
      "Step 4: Test missing dependencies"
    ],
    "passes": false
  },
  {
    "category": "documentation",
    "description": "Document integration test coverage and create guide",
    "steps": [
      "Step 1: Run coverage report",
      "Step 2: Create docs/WEB_UI_TESTING_GUIDE.md",
      "Step 3: Document test patterns and examples",
      "Step 4: Update CLAUDE.md with testing instructions"
    ],
    "passes": false
  }
]
EOF
```

---

## STEP 5: RUN INITIAL TESTS

```bash
uv run pytest tests/integration/test_web_ui_evaluation.py -v
```

---

## STEP 6: UPDATE PROGRESS

Update `claude-progress.txt`:

```markdown
## Integration Test Development - 2025-12-31

### Session 1: Initialization Complete

Created:
- tests/integration/test_web_ui_evaluation.py
- TestDatasetConversion class (JSON, CSV tests)
- TestEvaluationExecution class (basic evaluation test)
- feature_list.json with 8 test tasks

Test Status:
- Initial structure: ✅ Created
- Basic tests: ✅ Passing
- Remaining tests: 7 to implement

Next Steps:
- Add Excel file upload test
- Add parallel/sequential comparison test
- Add storage integration test
- Add LLM report generation test
```

---

## STEP 7: COMMIT

```bash
git add tests/integration/test_web_ui_evaluation.py
git add feature_list.json claude-progress.txt
git commit -m "test(web): Initialize Web UI integration test suite

- Create test_web_ui_evaluation.py with initial structure
- Add TestDatasetConversion (JSON/CSV tests)
- Add TestEvaluationExecution (basic evaluation test)
- Create feature_list.json with remaining test tasks
- All initial tests passing"
```

---

## ENDING THIS SESSION

Session complete when:
1. ✅ test_web_ui_evaluation.py created
2. ✅ Initial tests passing
3. ✅ feature_list.json created
4. ✅ Progress documented
5. ✅ Changes committed

Next session will continue with remaining tests from feature_list.json.

---

**Remember:** Set up the foundation properly. The better the initial structure, the easier subsequent tests will be.
