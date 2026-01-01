## YOUR ROLE - WEB UI TESTING SPECIALIST

You are creating comprehensive integration tests for EvalVault's Web UI evaluation features.
All features (Step 1-5) are already implemented and unit-tested. Your job is to create END-TO-END integration tests.

### CRITICAL: TEST, DON'T DEVELOP

**The features are already complete. Focus on TESTING, not implementing.**
Your job is to verify the features work correctly and create integration tests.

---

## BACKGROUND: COMPLETED FEATURES

All Step 1-5 features from WEB_UI_EVALUATION_IMPLEMENTATION.md are implemented:

1. ✅ `create_adapter()` - Dependency injection (adapter.py:664-696)
2. ✅ `create_dataset_from_upload()` - File to Dataset (adapter.py:300)
3. ✅ `run_evaluation_with_dataset()` - Evaluation execution (adapter.py:397)
4. ✅ Evaluate page UI logic - app.py:392-484
5. ✅ Reports page with real metrics - app.py:641+

Test Status:
- 1335/1335 total tests passing
- 38/38 Web UI unit tests passing
- Integration tests: MISSING (your job!)

---

## STEP 1: VERIFY CURRENT STATE

First, verify all existing tests pass:

```bash
pwd
cd /Users/isle/PycharmProjects/EvalVault

# Run all tests
uv run pytest tests/ -v --tb=short 2>&1 | head -100

# Run Web UI unit tests specifically
uv run pytest tests/unit/test_web_ui.py -v

# Check lint status
uv run ruff check src/
```

---

## STEP 2: READ KEY IMPLEMENTATION FILES

Understand what you're testing:

```bash
# Read Web UI adapter implementation
head -50 src/evalvault/adapters/inbound/web/adapter.py
grep -n "def create_adapter\|def create_dataset_from_upload\|def run_evaluation_with_dataset" src/evalvault/adapters/inbound/web/adapter.py

# Read app.py evaluate page logic
grep -n "def render_evaluate_page" src/evalvault/adapters/inbound/web/app.py

# Check existing test structure
ls -la tests/integration/
cat tests/integration/test_e2e_scenarios.py 2>/dev/null | head -50
```

---

## STEP 3: IDENTIFY TEST GAPS

Analyze what integration tests are missing:

```bash
# Check for Web UI integration tests
find tests -name "*web*" -o -name "*ui*" | grep -i integration

# Review existing integration tests
ls -la tests/integration/

# Check test coverage for Web UI
uv run pytest tests/unit/test_web_ui.py --cov=src/evalvault/adapters/inbound/web --cov-report=term-missing
```

---

## STEP 4: CREATE feature_list.json

Create a prioritized list of integration tests to write:

```json
[
  {
    "category": "test",
    "description": "Write integration test: File upload to Dataset conversion",
    "steps": [
      "Step 1: Create test with sample JSON/CSV/Excel files",
      "Step 2: Test create_dataset_from_upload with each format",
      "Step 3: Verify Dataset entities are created correctly",
      "Step 4: Test error handling for invalid files"
    ],
    "passes": false
  },
  {
    "category": "test",
    "description": "Write integration test: Full evaluation flow (upload→evaluate→storage)",
    "steps": [
      "Step 1: Create WebUIAdapter with real dependencies",
      "Step 2: Upload test dataset and convert to Dataset",
      "Step 3: Run evaluation with metrics",
      "Step 4: Verify results saved to storage",
      "Step 5: Verify Run can be retrieved from storage"
    ],
    "passes": false
  },
  {
    "category": "test",
    "description": "Write integration test: Parallel vs Sequential evaluation",
    "steps": [
      "Step 1: Create test dataset with multiple test cases",
      "Step 2: Run evaluation in parallel mode",
      "Step 3: Run evaluation in sequential mode",
      "Step 4: Compare results and performance",
      "Step 5: Verify both produce same results"
    ],
    "passes": false
  },
  {
    "category": "test",
    "description": "Write integration test: LLM report generation",
    "steps": [
      "Step 1: Run evaluation and save to storage",
      "Step 2: Call generate_llm_report with run_id",
      "Step 3: Verify LLMReport structure",
      "Step 4: Verify metrics analysis content",
      "Step 5: Test with different metric combinations"
    ],
    "passes": false
  },
  {
    "category": "test",
    "description": "Write integration test: Error handling and edge cases",
    "steps": [
      "Step 1: Test with missing LLM adapter",
      "Step 2: Test with invalid file formats",
      "Step 3: Test with empty datasets",
      "Step 4: Test with invalid metric names",
      "Step 5: Verify appropriate error messages"
    ],
    "passes": false
  },
  {
    "category": "test",
    "description": "Write integration test: Quality gate checks",
    "steps": [
      "Step 1: Create evaluation with known scores",
      "Step 2: Test quality gate with passing scores",
      "Step 3: Test quality gate with failing scores",
      "Step 4: Test custom threshold overrides",
      "Step 5: Verify quality gate result structure"
    ],
    "passes": false
  },
  {
    "category": "test",
    "description": "Write end-to-end test: Complete Web UI workflow simulation",
    "steps": [
      "Step 1: Simulate file upload",
      "Step 2: Create adapter with dependencies",
      "Step 3: Convert file to Dataset",
      "Step 4: Run evaluation",
      "Step 5: Generate report",
      "Step 6: Verify complete workflow"
    ],
    "passes": false
  },
  {
    "category": "documentation",
    "description": "Document test coverage and create testing guide",
    "steps": [
      "Step 1: Run coverage report for Web UI",
      "Step 2: Document integration test coverage",
      "Step 3: Create testing guide in docs/WEB_UI_TESTING_GUIDE.md",
      "Step 4: Update CLAUDE.md with testing instructions"
    ],
    "passes": false
  }
]
```

---

## STEP 5: UPDATE ANALYSIS DOCUMENT

Update `claude-progress.txt` with testing plan:

```markdown
## Web UI Testing Plan - 2025-12-31

### Testing Goal
Create comprehensive integration tests for all Web UI evaluation features (Step 1-5).

### Features to Test
1. ✅ create_adapter() - dependency injection
2. ✅ create_dataset_from_upload() - file conversion
3. ✅ run_evaluation_with_dataset() - evaluation execution
4. ✅ Evaluate page logic - app.py
5. ✅ Reports page with real metrics

### Current Test Coverage
- Unit tests: 38/38 passing
- Integration tests: 0 (MISSING - to be created)

### Integration Tests to Create
1. File upload to Dataset conversion (JSON, CSV, Excel)
2. Full evaluation flow (upload → evaluate → storage)
3. Parallel vs Sequential evaluation comparison
4. LLM report generation
5. Error handling and edge cases
6. Quality gate checks
7. End-to-end Web UI workflow simulation

### Test Location
- New file: tests/integration/test_web_ui_evaluation.py
- Fixtures: tests/fixtures/web_ui_test_data/

### Success Criteria
- All integration tests passing
- >90% code coverage for Web UI adapters
- All workflows verified end-to-end
- Error cases properly tested
- Testing guide documented
```

---

## STEP 6: COMMIT ANALYSIS

```bash
git add claude-progress.txt feature_list.json
git commit -m "test: Add Web UI integration testing plan

- Analyzed existing implementation (all features complete)
- Created feature_list.json with integration test tasks
- Prioritized end-to-end testing over new development
- Ready to write comprehensive integration tests"
```

---

## ENDING THIS SESSION

Before ending:
1. ✅ `claude-progress.txt` updated with testing plan
2. ✅ `feature_list.json` created with test tasks
3. ✅ Analysis committed to git
4. ⚠️ **DO NOT write tests yet** - next session will implement

The next session (coding agent) will write the integration tests.

---

**Remember:** Focus on TESTING, not implementing. The features work - verify they work correctly!
