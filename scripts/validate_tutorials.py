#!/usr/bin/env python3
"""
Tutorial Code Validation Script

Extracts and validates code blocks from tutorial markdown files to ensure
they remain up-to-date and functional.

Usage:
    uv run python scripts/validate_tutorials.py
    uv run python scripts/validate_tutorials.py --tutorial 01-quickstart.md
    uv run python scripts/validate_tutorials.py --fix
"""

import argparse
import ast
import re
import sys
from pathlib import Path


class CodeBlock:
    """Represents a code block extracted from markdown."""

    def __init__(
        self,
        content: str,
        language: str,
        line_number: int,
        file_path: Path,
        info: str,
    ):
        self.content = content
        self.language = language
        self.line_number = line_number
        self.file_path = file_path
        self.info = info

    def __repr__(self):
        return (
            f"CodeBlock(lang={self.language}, line={self.line_number}, file={self.file_path.name})"
        )


class TutorialValidator:
    """Validates code blocks in tutorial markdown files."""

    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir
        self.tutorials_dir = docs_dir / "tutorials"
        self.errors: list[dict[str, str]] = []
        self.warnings: list[dict[str, str]] = []

    def extract_code_blocks(self, md_file: Path) -> list[CodeBlock]:
        """Extract all code blocks from a markdown file."""
        code_blocks = []
        content = md_file.read_text(encoding="utf-8")

        # Pattern to match fenced code blocks with optional info string
        pattern = r"```([^\n]*)\n(.*?)```"

        for match in re.finditer(pattern, content, re.DOTALL):
            info = (match.group(1) or "").strip()
            language = info.split()[0] if info else "text"
            code_content = match.group(2)
            line_number = content[: match.start()].count("\n") + 1

            code_blocks.append(
                CodeBlock(
                    content=code_content,
                    language=language,
                    line_number=line_number,
                    file_path=md_file,
                    info=info,
                )
            )

        return code_blocks

    def _should_skip(self, block: CodeBlock) -> bool:
        tokens = {token.lower() for token in block.info.split()}
        return "skip" in tokens or "no-validate" in tokens or "no-check" in tokens

    def validate_python_syntax(self, block: CodeBlock) -> bool:
        """Validate Python code syntax."""
        if self._should_skip(block):
            return True
        if block.language not in ["python", "py"]:
            return True

        try:
            # Try to parse as Python AST
            ast.parse(block.content)
            return True
        except SyntaxError as e:
            self.errors.append(
                {
                    "file": str(block.file_path.relative_to(self.docs_dir)),
                    "line": block.line_number,
                    "type": "syntax_error",
                    "message": f"Python syntax error: {e.msg} at line {e.lineno}",
                }
            )
            return False

    def check_imports(self, block: CodeBlock) -> bool:
        """Check if imports reference actual modules."""
        if self._should_skip(block):
            return True
        if block.language not in ["python", "py"]:
            return True

        try:
            tree = ast.parse(block.content)
        except SyntaxError:
            return False

        valid = True
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("evalvault"):
                        # Check if module path exists
                        module_path = alias.name.replace(".", "/")
                        expected_path = self.docs_dir.parent / "src" / f"{module_path}.py"
                        expected_init = self.docs_dir.parent / "src" / module_path / "__init__.py"

                        if not expected_path.exists() and not expected_init.exists():
                            self.warnings.append(
                                {
                                    "file": str(block.file_path.relative_to(self.docs_dir)),
                                    "line": block.line_number,
                                    "type": "import_warning",
                                    "message": f"Import '{alias.name}' may not exist",
                                }
                            )
                            valid = False

            elif (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("evalvault")
            ):
                # Check if module path exists
                module_path = node.module.replace(".", "/")
                expected_path = self.docs_dir.parent / "src" / f"{module_path}.py"
                expected_init = self.docs_dir.parent / "src" / module_path / "__init__.py"

                if not expected_path.exists() and not expected_init.exists():
                    self.warnings.append(
                        {
                            "file": str(block.file_path.relative_to(self.docs_dir)),
                            "line": block.line_number,
                            "type": "import_warning",
                            "message": f"Import from '{node.module}' may not exist",
                        }
                    )
                    valid = False

        return valid

    def check_deprecated_apis(self, block: CodeBlock) -> bool:
        """Check for usage of deprecated APIs or patterns."""
        if self._should_skip(block):
            return True
        if block.language not in ["python", "py"]:
            return True

        deprecated_patterns = [
            (r"\.evaluate_single\(", "Use .evaluate() with single test case instead"),
            (r"MetricType\.", "Import specific metrics directly"),
            (r"from evalvault import \*", "Use explicit imports instead of wildcard"),
        ]

        valid = True
        for pattern, message in deprecated_patterns:
            if re.search(pattern, block.content):
                self.warnings.append(
                    {
                        "file": str(block.file_path.relative_to(self.docs_dir)),
                        "line": block.line_number,
                        "type": "deprecated_api",
                        "message": f"Deprecated pattern found: {message}",
                    }
                )
                valid = False

        return valid

    def check_bash_commands(self, block: CodeBlock) -> bool:
        """Validate bash commands for common issues."""
        if self._should_skip(block):
            return True
        if block.language not in ["bash", "sh", "shell"]:
            return True

        lines = block.content.strip().split("\n")
        valid = True

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Check if using uv run for Python commands
            if re.search(r"(^|\\s)(evalvault|pytest|python)\\b", line) and "uv run" not in line:
                self.warnings.append(
                    {
                        "file": str(block.file_path.relative_to(self.docs_dir)),
                        "line": block.line_number,
                        "type": "missing_uv_run",
                        "message": f"Command should use 'uv run': {line}",
                    }
                )
                valid = False

        return valid

    def validate_tutorial(self, md_file: Path) -> bool:
        """Validate all code blocks in a tutorial file."""
        print(f"\nValidating: {md_file.relative_to(self.docs_dir)}")

        code_blocks = self.extract_code_blocks(md_file)
        print(f"  Found {len(code_blocks)} code blocks")

        all_valid = True
        for block in code_blocks:
            if block.language in ["python", "py"]:
                syntax_valid = self.validate_python_syntax(block)
                imports_valid = self.check_imports(block)
                api_valid = self.check_deprecated_apis(block)
                all_valid = all_valid and syntax_valid and imports_valid and api_valid
            elif block.language in ["bash", "sh", "shell"]:
                bash_valid = self.check_bash_commands(block)
                all_valid = all_valid and bash_valid

        return all_valid

    def validate_all_tutorials(self) -> bool:
        """Validate all tutorial files."""
        if not self.tutorials_dir.exists():
            print(f"Error: Tutorials directory not found: {self.tutorials_dir}")
            return False

        tutorial_files = sorted(self.tutorials_dir.glob("*.md"))

        if not tutorial_files:
            print(f"Warning: No tutorial files found in {self.tutorials_dir}")
            return True

        print(f"Found {len(tutorial_files)} tutorial files")

        all_valid = True
        for tutorial_file in tutorial_files:
            valid = self.validate_tutorial(tutorial_file)
            all_valid = all_valid and valid

        return all_valid

    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 80)
        print("VALIDATION REPORT")
        print("=" * 80)

        if self.errors:
            print(f"\nERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error['file']}:{error['line']} [{error['type']}]")
                print(f"    {error['message']}")

        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning['file']}:{warning['line']} [{warning['type']}]")
                print(f"    {warning['message']}")

        if not self.errors and not self.warnings:
            print("\n✓ All tutorials validated successfully!")

        print("\n" + "=" * 80)
        print(f"Total: {len(self.errors)} errors, {len(self.warnings)} warnings")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Validate code blocks in tutorial markdown files")
    parser.add_argument(
        "--tutorial", help="Validate specific tutorial file (e.g., 01-quickstart.md)"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Attempt to auto-fix common issues (not implemented yet)"
    )

    args = parser.parse_args()

    # Find docs directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    docs_dir = project_root / "docs"

    if not docs_dir.exists():
        print(f"Error: Docs directory not found: {docs_dir}")
        sys.exit(1)

    validator = TutorialValidator(docs_dir)

    if args.tutorial:
        # Validate specific tutorial
        tutorial_path = docs_dir / "tutorials" / args.tutorial
        if not tutorial_path.exists():
            print(f"Error: Tutorial file not found: {tutorial_path}")
            sys.exit(1)

        valid = validator.validate_tutorial(tutorial_path)
    else:
        # Validate all tutorials
        valid = validator.validate_all_tutorials()

    validator.print_report()

    if args.fix:
        print("\nNote: Auto-fix is not yet implemented")

    # Exit with error code if validation failed
    sys.exit(0 if valid and not validator.errors else 1)


if __name__ == "__main__":
    main()
