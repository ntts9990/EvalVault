"""File upload handling components."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """파일 검증 결과."""

    is_valid: bool
    file_type: str | None = None
    row_count: int = 0
    columns: list[str] = field(default_factory=list)
    dataset_name: str | None = None
    error_message: str | None = None
    thresholds: dict[str, float] = field(default_factory=dict)


# 필수 컬럼 목록
REQUIRED_COLUMNS = ["question", "answer", "contexts"]


class FileUploadHandler:
    """파일 업로드 처리기.

    CSV, JSON, Excel 파일을 검증하고 파싱합니다.
    """

    def __init__(self):
        """핸들러 초기화."""
        self.supported_types = ["csv", "json", "xlsx"]

    def validate_file(self, filename: str, content: bytes) -> ValidationResult:
        """파일 검증.

        Args:
            filename: 파일명
            content: 파일 내용 (bytes)

        Returns:
            ValidationResult 인스턴스
        """
        # 파일 확장자 확인
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext not in self.supported_types:
            return ValidationResult(
                is_valid=False,
                error_message=f"Unsupported file type: .{ext}. Supported types: {', '.join(self.supported_types)}",
            )

        # 파일 타입별 검증
        if ext == "csv":
            return self._validate_csv(content)
        elif ext == "json":
            return self._validate_json(content)
        elif ext == "xlsx":
            return self._validate_excel(content)

        return ValidationResult(is_valid=False, error_message="Unknown error")

    def _validate_csv(self, content: bytes) -> ValidationResult:
        """CSV 파일 검증."""
        try:
            text = content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))

            # 헤더 확인
            columns = reader.fieldnames or []

            # 필수 컬럼 확인
            missing = [col for col in REQUIRED_COLUMNS if col not in columns]
            if missing:
                return ValidationResult(
                    is_valid=False,
                    file_type="csv",
                    columns=list(columns),
                    error_message=f"Missing required columns: {', '.join(missing)}",
                )

            # 행 수 확인
            rows = list(reader)
            if len(rows) == 0:
                return ValidationResult(
                    is_valid=False,
                    file_type="csv",
                    columns=list(columns),
                    error_message="CSV file is empty (no data rows)",
                )

            return ValidationResult(
                is_valid=True,
                file_type="csv",
                row_count=len(rows),
                columns=list(columns),
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                file_type="csv",
                error_message=f"Failed to parse CSV: {e!s}",
            )

    def _validate_json(self, content: bytes) -> ValidationResult:
        """JSON 파일 검증."""
        try:
            text = content.decode("utf-8")
            data = json.loads(text)

            # test_cases 배열 확인
            if "test_cases" not in data:
                return ValidationResult(
                    is_valid=False,
                    file_type="json",
                    error_message="JSON must contain 'test_cases' array",
                )

            test_cases = data["test_cases"]
            if not isinstance(test_cases, list):
                return ValidationResult(
                    is_valid=False,
                    file_type="json",
                    error_message="'test_cases' must be an array",
                )

            if len(test_cases) == 0:
                return ValidationResult(
                    is_valid=False,
                    file_type="json",
                    error_message="JSON file is empty (no test cases)",
                )

            # 첫 번째 테스트 케이스에서 필수 필드 확인
            first_case = test_cases[0]
            missing = [col for col in REQUIRED_COLUMNS if col not in first_case]
            if missing:
                return ValidationResult(
                    is_valid=False,
                    file_type="json",
                    error_message=f"Missing required fields: {', '.join(missing)}",
                )

            return ValidationResult(
                is_valid=True,
                file_type="json",
                row_count=len(test_cases),
                columns=list(first_case.keys()),
                dataset_name=data.get("name"),
                thresholds=data.get("thresholds", {}),
            )

        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                file_type="json",
                error_message=f"Invalid JSON: {e!s}",
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                file_type="json",
                error_message=f"Failed to parse JSON: {e!s}",
            )

    def _validate_excel(self, content: bytes) -> ValidationResult:
        """Excel 파일 검증 (간단한 확인만)."""
        # Excel 파싱은 pandas가 필요하므로 여기서는 기본 검증만
        if len(content) < 100:  # 너무 작으면 유효하지 않음
            return ValidationResult(
                is_valid=False,
                file_type="xlsx",
                error_message="Excel file appears to be empty or corrupted",
            )

        return ValidationResult(
            is_valid=True,
            file_type="xlsx",
            row_count=0,  # 실제 파싱 시 계산
        )

    def parse_to_test_cases(self, filename: str, content: bytes) -> list[dict]:
        """파일을 테스트 케이스 목록으로 파싱.

        Args:
            filename: 파일명
            content: 파일 내용

        Returns:
            테스트 케이스 딕셔너리 목록
        """
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext == "csv":
            return self._parse_csv(content)
        elif ext == "json":
            return self._parse_json(content)
        else:
            return []

    def _parse_csv(self, content: bytes) -> list[dict]:
        """CSV를 테스트 케이스로 파싱."""
        try:
            text = content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            return list(reader)
        except Exception:
            return []

    def _parse_json(self, content: bytes) -> list[dict]:
        """JSON을 테스트 케이스로 파싱."""
        try:
            text = content.decode("utf-8")
            data = json.loads(text)
            return data.get("test_cases", [])
        except Exception:
            return []
