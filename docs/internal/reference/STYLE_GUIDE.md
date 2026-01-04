# Documentation Style Guide

This guide ensures consistency across all EvalVault documentation.

## General Principles

1. **Clarity First**: Write for developers who are new to the project
2. **Show, Don't Just Tell**: Include code examples for all concepts
3. **Maintain Accuracy**: Keep code examples in sync with the actual codebase
4. **Bilingual Support**: Support both English and Korean where appropriate

## File Organization

### Directory Structure

```
docs/
├── INDEX.md                     # Documentation hub
├── getting-started/             # Installation & onboarding
│   └── INSTALLATION.md
├── guides/                      # User/CLI/Dev/Ops guides
│   ├── USER_GUIDE.md
│   ├── CLI_GUIDE.md
│   ├── DEV_GUIDE.md
│   └── OBSERVABILITY_PLAYBOOK.md
├── architecture/                # Architecture documentation
│   └── ARCHITECTURE.md
├── status/                      # Public status & roadmap
│   ├── STATUS.md
│   └── ROADMAP.md
├── tutorials/                   # Step-by-step tutorials
│   ├── 01-quickstart.md
│   ├── 02-basic-evaluation.md
│   └── ...
├── api/                        # Auto-generated API reference
│   ├── domain/
│   ├── ports/
│   ├── adapters/
│   └── config.md
└── internal/                   # Internal documentation
    ├── reference/
    │   ├── STYLE_GUIDE.md (this file)
    │   ├── ARCHITECTURE_C4.md
    │   └── ...
    ├── status/
    ├── reports/
    ├── plans/
    ├── guides/
    ├── logs/
    └── archive/
```

### File Naming

- Use UPPERCASE for guide filenames (e.g., `USER_GUIDE.md`, `ARCHITECTURE.md`)
- Use lowercase with hyphens for tutorials (e.g., `01-quickstart.md`)
- Use descriptive names that indicate content (e.g., `CLI_GUIDE.md`, not `GUIDE2.md`)
- Avoid `README.md` inside `docs/` to prevent confusion with the root README; use `INDEX.md` for the hub

## Markdown Formatting

### Headers

Use ATX-style headers with a single space after `#`:

```markdown
# Top Level (H1)
## Second Level (H2)
### Third Level (H3)
```

**Rules:**
- Only one H1 per document (the title)
- Don't skip header levels (H1 → H3)
- Use sentence case for headers (not Title Case)

### Code Blocks

Always specify the language for syntax highlighting:

````markdown
```python
from evalvault import Dataset

dataset = Dataset.from_csv("data.csv")
```
````

**Supported languages:**
- `python` - Python code
- `bash` - Shell commands
- `json` - JSON data
- `yaml` - YAML configuration
- `text` - Plain text

### Shell Commands

Always use `uv run` for Python commands:

```markdown
# Good
```bash
uv run evalvault run data.csv
uv run pytest tests/
```

# Bad
```bash
evalvault run data.csv  # Missing uv run
pytest tests/           # Missing uv run
```
```

### Code Examples

#### Minimal Complete Examples

Every code example should be runnable:

```python
# Good - Complete and runnable
from evalvault.config import Settings
from evalvault.domain.services import RagasEvaluator

settings = Settings()
evaluator = RagasEvaluator(settings)
```

```python
# Bad - Incomplete
evaluator = RagasEvaluator(settings)  # Where does settings come from?
```

#### Import Style

Use explicit imports:

```python
# Good
from evalvault.domain.entities import TestCase, Dataset
from evalvault.config import Settings

# Bad
from evalvault import *
```

#### Error Handling

Show realistic error handling in examples:

```python
# Good
from pathlib import Path

try:
    dataset = Dataset.from_csv("data.csv")
except FileNotFoundError:
    print("Error: Dataset file not found")
except ValueError as e:
    print(f"Error: Invalid dataset format - {e}")
```

### Tables

Use GitHub Flavored Markdown tables:

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
```

**Alignment:**
- Left align text: `|----------|`
- Right align numbers: `|---------:|`
- Center align: `|:--------:|`

### Links

#### Internal Links

Use relative paths for internal documentation:

```markdown
See the [Architecture Guide](../ARCHITECTURE.md) for details.
See the [Quickstart Tutorial](tutorials/01-quickstart.md).
```

#### External Links

Use descriptive link text:

```markdown
# Good
For more information, see the [Ragas documentation](https://ragas.io).

# Bad
For more information, click [here](https://ragas.io).
```

### Admonitions

Use mkdocs-material admonitions for important notes:

```markdown
!!! note
    This is a note with important information.

!!! warning
    This is a warning about potential issues.

!!! tip
    This is a helpful tip or best practice.

!!! danger
    This is critical information about breaking changes.
```

## Content Guidelines

### Tutorial Structure

Every tutorial should follow this structure:

1. **Prerequisites** - What the reader needs to know/have
2. **Learning Objectives** - What they will learn
3. **Step-by-Step Instructions** - Numbered steps with code
4. **Verification** - How to verify it worked
5. **Next Steps** - What to learn next

Example:

```markdown
# Tutorial: Basic Evaluation

## Prerequisites

- EvalVault installed (`uv sync --extra dev`)
- OpenAI API key configured
- Basic Python knowledge

## What You'll Learn

- How to load a dataset
- How to run a basic evaluation
- How to interpret results

## Steps

### 1. Load Your Dataset

[Code example]

### 2. Configure the Evaluator

[Code example]

### 3. Run the Evaluation

[Code example]

## Verification

[How to check it worked]

## Next Steps

- Learn about [Custom Metrics](03-custom-metrics.md)
- Explore [Phoenix Integration](04-phoenix-integration.md)
```

### API Documentation

Use mkdocstrings format for API references:

```markdown
## ClassName

Brief description of the class.

::: evalvault.module.ClassName
    options:
      show_root_heading: true
      show_source: true
      docstring_style: google
```

### Code Comments

Keep code comments minimal in documentation:

```python
# Good - Explain WHY, not WHAT
settings.max_retries = 3  # Prevent infinite loops on API failures

# Bad - Obvious comments
settings.max_retries = 3  # Set max retries to 3
```

## Language Guidelines

### English Documentation

- Use American English spelling (e.g., "color" not "colour")
- Write in active voice ("Run the command" not "The command is run")
- Use present tense ("The function returns" not "The function will return")
- Be concise and direct

### Korean Documentation

- Use formal/polite tone (합니다체)
- Provide Korean translations for key technical terms when helpful
- Use Korean for user-facing guides, English for code
- Example:

```markdown
## 메트릭 설정 (Metric Configuration)

평가에 사용할 메트릭을 선택하세요:

```python
metrics = ["faithfulness", "answer_relevancy"]
```
```

### Bilingual Terms

Common terms that should remain in English:

- Technical terms: LLM, RAG, API, CLI
- Code identifiers: Dataset, TestCase, evaluate()
- Metrics: faithfulness, answer_relevancy, etc.

Terms that should be translated:

- 평가 (evaluation)
- 데이터셋 (dataset)
- 결과 (results)
- 설정 (configuration)

## Version References

### Code Examples

Always use the latest stable API:

```python
# Good - Current API
from evalvault.domain.entities import Dataset

dataset = Dataset.from_csv("data.csv")

# Bad - Deprecated API
from evalvault.loaders import CSVLoader

loader = CSVLoader()
dataset = loader.load("data.csv")
```

### Version-Specific Notes

Use admonitions for version-specific information:

```markdown
!!! info "Version 0.2.0+"
    The `parallel` parameter was added in version 0.2.0.
```

## Validation

### Before Committing

Run the validation script:

```bash
uv run python scripts/validate_tutorials.py
```

This checks:
- Python syntax in code blocks
- Import statements
- Deprecated APIs
- Shell command best practices

### Checklist

Before publishing documentation:

- [ ] All code examples are runnable
- [ ] Commands use `uv run` where appropriate
- [ ] Links are valid (internal and external)
- [ ] Spelling and grammar checked
- [ ] Tables render correctly
- [ ] Code blocks have language specified
- [ ] No deprecated APIs used
- [ ] Validation script passes

## MkDocs Integration

### Building Documentation

```bash
# Install dependencies
uv sync --extra docs

# Serve locally
uv run mkdocs serve

# Build static site
uv run mkdocs build
```

### Custom CSS

Place custom styles in `docs/stylesheets/extra.css`:

```css
/* Example custom styles */
.admonition.note {
    border-left-color: #448aff;
}
```

Reference in `mkdocs.yml`:

```yaml
extra_css:
  - stylesheets/extra.css
```

## Examples

### Good Documentation Example

```markdown
# Tutorial: Running Your First Evaluation

## Prerequisites

- EvalVault installed with dev dependencies
- OpenAI API key set in `.env` file
- Sample dataset (download from [examples/](examples/))

## What You'll Learn

In this tutorial, you'll learn how to:

1. Load a CSV dataset
2. Configure evaluation metrics
3. Run an evaluation
4. View and interpret results

## Step 1: Load the Dataset

Create a new Python file `my_evaluation.py`:

```python
from evalvault.domain.entities import Dataset

# Load dataset from CSV file
dataset = Dataset.from_csv("insurance_qa.csv")

print(f"Loaded {len(dataset.test_cases)} test cases")
```

Run it:

```bash
uv run python my_evaluation.py
```

Expected output:
```
Loaded 10 test cases
```

## Next Steps

Now that you've run your first evaluation, try:

- [Adding Custom Metrics](03-custom-metrics.md)
- [Enabling Phoenix Tracing](04-phoenix-integration.md)
```

### Bad Documentation Example

```markdown
# Evaluation

You can run evaluations.

```python
evaluator.run()
```

See other docs for more info.
```

**Problems:**
- No context or prerequisites
- Incomplete code example
- No explanation of what happens
- Vague "other docs" reference

## Continuous Improvement

This style guide is a living document. Suggestions for improvements are welcome through:

- GitHub Issues
- Pull Requests
- Team discussions

When making changes:
1. Update this guide first
2. Update affected documentation
3. Run validation scripts
4. Create PR with all changes together
