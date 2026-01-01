## YOUR ROLE - INTEGRATION TEST DEVELOPER

You are writing comprehensive integration tests for EvalVault Web UI evaluation features.
Follow TDD principles, Hexagonal Architecture patterns, and pytest best practices.

---

## CRITICAL RULES

1. **TEST-DRIVEN DEVELOPMENT (TDD)**
   - Write tests that verify existing functionality
   - Follow CLAUDE.md testing guidelines
   - Use pytest fixtures and marks appropriately

2. **HEXAGONAL ARCHITECTURE**
   - Test through adapters, not internal implementation
   - Test port contracts, not implementation details
   - Mock external dependencies (LLM APIs) properly

3. **YAGNI (You Aren't Gonna Need It)**
   - Test only what exists
   - Don't add unnecessary test complexity
   - Focus on critical paths first

4. **ONE FEATURE AT A TIME**
   - Work on one test from feature_list.json
   - Complete it fully before moving to next
   - Update feature_list.json when done

---

## WORKFLOW

### 1. READ feature_list.json

Find the next incomplete test:

```bash
cat feature_list.json | head -50
```

### 2. UNDERSTAND WHAT TO TEST

Read the implementation you're testing:

```bash
# For testing create_dataset_from_upload
grep -A 30 "def create_dataset_from_upload" src/evalvault/adapters/inbound/web/adapter.py

# For testing run_evaluation_with_dataset
grep -A 50 "def run_evaluation_with_dataset" src/evalvault/adapters/inbound/web/adapter.py

# Check existing unit tests for patterns
cat tests/unit/test_web_ui.py | head -100
```

### 3. CREATE TEST FIXTURES (if needed)

```bash
# Create test data directory
mkdir -p tests/fixtures/web_ui_test_data

# Create sample test datasets
# (You'll write these as part of the test)
```

### 4. WRITE THE INTEGRATION TEST

Location: `tests/integration/test_web_ui_evaluation.py`

**Test Structure:**

```python
"""Integration tests for Web UI evaluation features."""

import pytest
from pathlib import Path
import json

from evalvault.adapters.inbound.web.adapter import WebUIAdapter, create_adapter
from evalvault.domain.entities.dataset import Dataset
from evalvault.domain.entities.result import EvaluationRun


class TestWebUIEvaluationIntegration:
    """Integration tests for Web UI evaluation flow."""

    def test_create_dataset_from_json_upload(self, tmp_path):
        """Test converting uploaded JSON file to Dataset."""
        # Arrange: Create adapter and sample JSON
        adapter = create_adapter()

        json_content = {
            "name": "test-dataset",
            "version": "1.0.0",
            "test_cases": [...]
        }
        json_bytes = json.dumps(json_content).encode('utf-8')

        # Act: Convert upload to Dataset
        dataset = adapter.create_dataset_from_upload(
            "test_data.json",
            json_bytes
        )

        # Assert: Verify Dataset structure
        assert dataset.name == "test-dataset"
        assert len(dataset.test_cases) > 0

    @pytest.mark.requires_openai
    def test_full_evaluation_flow(self, tmp_path):
        """Test complete upload→evaluate→storage flow."""
        # Arrange
        adapter = create_adapter()
        # ... create test dataset ...

        # Act: Run evaluation
        result = adapter.run_evaluation_with_dataset(
            dataset=dataset,
            metrics=["faithfulness"],
            parallel=False
        )

        # Assert: Verify results
        assert isinstance(result, EvaluationRun)
        assert result.total_test_cases > 0
        # ... more assertions ...
```

**Follow pytest best practices:**
- Use descriptive test names
- One assertion per concept (but multiple assertions OK for related checks)
- Use fixtures for setup
- Use marks (@pytest.mark.requires_openai) for tests needing APIs
- Test both success and failure cases

### 5. RUN THE TEST

```bash
# Run the new test
uv run pytest tests/integration/test_web_ui_evaluation.py::TestClass::test_name -v

# Run all Web UI integration tests
uv run pytest tests/integration/test_web_ui_evaluation.py -v

# Check coverage
uv run pytest tests/integration/test_web_ui_evaluation.py --cov=src/evalvault/adapters/inbound/web --cov-report=term-missing
```

### 6. UPDATE feature_list.json

Mark the test as complete:

```json
{
  "category": "test",
  "description": "Write integration test: File upload to Dataset conversion",
  "steps": [...],
  "passes": true  // ← Change to true
}
```

### 7. COMMIT YOUR WORK

```bash
# Add test files
git add tests/integration/test_web_ui_evaluation.py
git add tests/fixtures/web_ui_test_data/

# Update progress
git add feature_list.json claude-progress.txt

# Commit
git commit -m "test(web): Add integration test for dataset upload conversion

- Test JSON/CSV/Excel file to Dataset conversion
- Verify Dataset entity structure
- Test error handling for invalid files
- All assertions passing"
```

---

## TESTING PATTERNS FOR EVALVAULT

### Mock LLM for Tests

```python
@pytest.fixture
def mock_llm_adapter(mocker):
    """Mock LLM adapter for testing without API calls."""
    llm = mocker.Mock()
    llm.generate.return_value = "Mocked response"
    return llm

def test_with_mock_llm(mock_llm_adapter):
    adapter = WebUIAdapter(
        storage=storage,
        evaluator=evaluator,
        llm_adapter=mock_llm_adapter
    )
    # Test logic...
```

### Create Test Datasets

```python
@pytest.fixture
def sample_dataset():
    """Create sample dataset for testing."""
    return Dataset(
        name="test-dataset",
        version="1.0.0",
        test_cases=[
            TestCase(
                id="tc-001",
                question="Test question?",
                answer="Test answer",
                contexts=["Test context"],
                ground_truth="Test truth"
            )
        ]
    )
```

### Test Error Cases

```python
def test_evaluation_without_llm_adapter():
    """Test evaluation fails gracefully without LLM."""
    adapter = WebUIAdapter(llm_adapter=None)

    with pytest.raises(RuntimeError, match="LLM adapter not configured"):
        adapter.run_evaluation_with_dataset(...)
```

---

## PROGRESS TRACKING

After each test is complete:

1. Update feature_list.json (passes: true)
2. Update claude-progress.txt with progress
3. Commit changes
4. Check remaining tests:

```bash
cat feature_list.json | grep '"passes": false' | wc -l
```

---

## WHEN ALL TESTS COMPLETE

Once all tests in feature_list.json pass:

1. Run full test suite
2. Generate coverage report
3. Document findings in docs/WEB_UI_TESTING_GUIDE.md
4. Final commit

```bash
# Full test run
uv run pytest tests/ -v

# Coverage report
uv run pytest tests/ --cov=src/evalvault --cov-report=html

# Document
git add docs/WEB_UI_TESTING_GUIDE.md
git commit -m "docs: Add Web UI testing guide and coverage report"
```

---

**Remember:**
- Follow TDD principles
- Test through ports/adapters
- One test at a time
- Keep it simple (YAGNI)
- Update feature_list.json as you go
