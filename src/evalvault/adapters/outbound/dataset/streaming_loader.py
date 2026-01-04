"""스트리밍 데이터셋 로더.

목표: 메모리 사용량 100MB -> 10MB (대용량 데이터셋)

특징:
- 청크 단위 로딩으로 메모리 효율적 처리
- Iterator/Generator 기반 지연 로딩
- CSV/JSON/Excel 지원
- 진행 상황 콜백 지원
"""

from __future__ import annotations

import json
from collections.abc import Callable, Generator, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evalvault.domain.entities.dataset import Dataset, TestCase


@dataclass
class StreamingConfig:
    """스트리밍 로더 설정."""

    # 청크 크기 (한 번에 읽을 행 수)
    chunk_size: int = 100
    # 스킵할 행 수 (헤더 제외)
    skip_rows: int = 0
    # 최대 행 수 (None이면 전체)
    max_rows: int | None = None
    # 인코딩 (자동 감지 시 None)
    encoding: str | None = None


@dataclass
class StreamingStats:
    """스트리밍 통계."""

    rows_read: int = 0
    chunks_processed: int = 0
    bytes_read: int = 0
    estimated_total_rows: int | None = None


class StreamingTestCaseIterator(Iterator[TestCase]):
    """테스트 케이스를 스트리밍으로 반환하는 이터레이터.

    메모리에 전체 데이터를 로드하지 않고 필요할 때마다 읽음.
    """

    def __init__(
        self,
        generator: Generator[TestCase, None, None],
        stats: StreamingStats | None = None,
    ):
        """초기화.

        Args:
            generator: 테스트 케이스 생성기
            stats: 통계 객체 (외부에서 모니터링용)
        """
        self._generator = generator
        self._stats = stats or StreamingStats()
        self._exhausted = False

    def __iter__(self) -> Iterator[TestCase]:
        return self

    def __next__(self) -> TestCase:
        if self._exhausted:
            raise StopIteration

        try:
            test_case = next(self._generator)
            self._stats.rows_read += 1
            return test_case
        except StopIteration:
            self._exhausted = True
            raise

    @property
    def stats(self) -> StreamingStats:
        """현재 통계 반환."""
        return self._stats


class StreamingCSVLoader:
    """CSV 파일 스트리밍 로더.

    pandas 없이 표준 라이브러리만 사용하여 메모리 효율적으로 처리.
    """

    ENCODING_FALLBACKS = ["utf-8-sig", "utf-8", "cp949", "euc-kr", "latin-1"]

    def __init__(self, config: StreamingConfig | None = None):
        """초기화.

        Args:
            config: 스트리밍 설정
        """
        self.config = config or StreamingConfig()

    def supports(self, file_path: str | Path) -> bool:
        """CSV 파일 지원 여부 확인."""
        return Path(file_path).suffix.lower() == ".csv"

    def stream(
        self,
        file_path: str | Path,
        progress_callback: Callable[[StreamingStats], None] | None = None,
    ) -> StreamingTestCaseIterator:
        """CSV 파일을 스트리밍으로 읽기.

        Args:
            file_path: CSV 파일 경로
            progress_callback: 진행 콜백 함수

        Returns:
            테스트 케이스 이터레이터
        """
        stats = StreamingStats()
        generator = self._create_generator(file_path, stats, progress_callback)
        return StreamingTestCaseIterator(generator, stats)

    def _create_generator(
        self,
        file_path: str | Path,
        stats: StreamingStats,
        progress_callback: Callable[[StreamingStats], None] | None = None,
    ) -> Generator[TestCase, None, None]:
        """테스트 케이스 생성기.

        Args:
            file_path: CSV 파일 경로
            stats: 통계 객체
            progress_callback: 진행 콜백

        Yields:
            TestCase 객체
        """
        import csv

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # 인코딩 결정
        encoding = self.config.encoding or self._detect_encoding(path)

        rows_yielded = 0
        with open(path, encoding=encoding, newline="") as f:
            reader = csv.DictReader(f)

            # 필수 컬럼 확인
            if reader.fieldnames is None:
                raise ValueError("CSV file has no headers")

            required = {"id", "question", "answer", "contexts"}
            missing = required - set(reader.fieldnames)
            if missing:
                raise ValueError(f"Missing required columns: {missing}")

            # 스킵 행 처리
            for _ in range(self.config.skip_rows):
                try:
                    next(reader)
                except StopIteration:
                    return

            # 데이터 읽기
            for row in reader:
                # 최대 행 제한 확인
                if self.config.max_rows and rows_yielded >= self.config.max_rows:
                    break

                test_case = self._row_to_test_case(row)
                if test_case:
                    rows_yielded += 1
                    stats.rows_read = rows_yielded

                    # 청크 완료 시 콜백
                    if progress_callback and rows_yielded % self.config.chunk_size == 0:
                        stats.chunks_processed = rows_yielded // self.config.chunk_size
                        progress_callback(stats)

                    yield test_case

    def _row_to_test_case(self, row: dict[str, str]) -> TestCase | None:
        """CSV 행을 TestCase로 변환.

        Args:
            row: CSV 행 딕셔너리

        Returns:
            TestCase 또는 None (유효하지 않은 경우)
        """
        try:
            contexts = self._parse_contexts(row.get("contexts", ""))
            ground_truth = row.get("ground_truth")
            # 빈 문자열, nan, None 모두 None으로 처리
            if ground_truth is None or str(ground_truth).strip().lower() in ("nan", ""):
                ground_truth = None

            return TestCase(
                id=str(row["id"]),
                question=str(row["question"]),
                answer=str(row["answer"]),
                contexts=contexts,
                ground_truth=ground_truth,
            )
        except (KeyError, ValueError):
            return None

    def _parse_contexts(self, contexts_str: str) -> list[str]:
        """컨텍스트 문자열 파싱.

        Args:
            contexts_str: 컨텍스트 문자열 (JSON 배열 또는 파이프 구분)

        Returns:
            컨텍스트 리스트
        """
        if not contexts_str or str(contexts_str).lower() == "nan":
            return []

        contexts_str = str(contexts_str).strip()

        # JSON 형식 시도
        if contexts_str.startswith("["):
            try:
                return json.loads(contexts_str)
            except json.JSONDecodeError:
                pass

        # 파이프 구분 형식
        return [ctx.strip() for ctx in contexts_str.split("|") if ctx.strip()]

    def _detect_encoding(self, path: Path) -> str:
        """인코딩 자동 감지.

        Args:
            path: 파일 경로

        Returns:
            감지된 인코딩
        """
        for encoding in self.ENCODING_FALLBACKS:
            try:
                with open(path, encoding=encoding) as f:
                    f.read(1024)  # 일부만 읽어서 테스트
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue
        return "utf-8"


class StreamingJSONLoader:
    """JSON 파일 스트리밍 로더.

    대용량 JSON 배열을 스트리밍으로 처리.
    ijson이 설치된 경우 진짜 스트리밍 파싱을 사용합니다.
    """

    def __init__(self, config: StreamingConfig | None = None):
        """초기화.

        Args:
            config: 스트리밍 설정
        """
        self.config = config or StreamingConfig()

    def supports(self, file_path: str | Path) -> bool:
        """JSON 파일 지원 여부 확인."""
        return Path(file_path).suffix.lower() == ".json"

    def stream(
        self,
        file_path: str | Path,
        progress_callback: Callable[[StreamingStats], None] | None = None,
    ) -> StreamingTestCaseIterator:
        """JSON 파일을 스트리밍으로 읽기.

        Args:
            file_path: JSON 파일 경로
            progress_callback: 진행 콜백 함수

        Returns:
            테스트 케이스 이터레이터
        """
        stats = StreamingStats()
        generator = self._create_generator(file_path, stats, progress_callback)
        return StreamingTestCaseIterator(generator, stats)

    def _create_generator(
        self,
        file_path: str | Path,
        stats: StreamingStats,
        progress_callback: Callable[[StreamingStats], None] | None = None,
    ) -> Generator[TestCase, None, None]:
        """테스트 케이스 생성기.

        JSON 파일 구조:
        - {"test_cases": [...]} 형식
        - [...] 배열 형식
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if self._can_stream_json():
            yield from self._stream_with_ijson(path, stats, progress_callback)
            return

        with open(path, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON file: {e}") from e

        # test_cases 키가 있는 경우
        if isinstance(data, dict):
            test_cases = data.get("test_cases", [])
        elif isinstance(data, list):
            test_cases = data
        else:
            raise ValueError("JSON must be an array or object with 'test_cases' key")

        stats.estimated_total_rows = len(test_cases)
        rows_yielded = 0

        # 스킵 처리
        start_idx = self.config.skip_rows
        end_idx = start_idx + self.config.max_rows if self.config.max_rows else len(test_cases)

        for item in test_cases[start_idx:end_idx]:
            test_case = self._item_to_test_case(item)
            if test_case:
                rows_yielded += 1
                stats.rows_read = rows_yielded

                if progress_callback and rows_yielded % self.config.chunk_size == 0:
                    stats.chunks_processed = rows_yielded // self.config.chunk_size
                    progress_callback(stats)

                yield test_case

    def _can_stream_json(self) -> bool:
        """ijson 사용 가능 여부 확인."""
        try:
            import ijson  # noqa: F401
        except ImportError:
            return False
        return True

    def _detect_json_container(self, path: Path) -> str:
        """JSON 최상위 컨테이너 타입 감지."""
        with open(path, "rb") as f:
            while True:
                char = f.read(1)
                if not char:
                    break
                if char in b" \t\r\n":
                    continue
                if char == b"[":
                    return "array"
                if char == b"{":
                    return "object"
                break
        return "unknown"

    def _stream_with_ijson(
        self,
        path: Path,
        stats: StreamingStats,
        progress_callback: Callable[[StreamingStats], None] | None = None,
    ) -> Generator[TestCase, None, None]:
        """ijson 기반 스트리밍 파서."""
        import ijson

        container = self._detect_json_container(path)
        if container == "array":
            prefix = "item"
        elif container == "object":
            prefix = "test_cases.item"
        else:
            raise ValueError("JSON must be an array or object with 'test_cases' key")

        rows_yielded = 0
        skipped = 0
        max_rows = self.config.max_rows

        with open(path, "rb") as f:
            items = ijson.items(f, prefix)
            for item in items:
                if skipped < self.config.skip_rows:
                    skipped += 1
                    continue

                if max_rows and rows_yielded >= max_rows:
                    break

                test_case = self._item_to_test_case(item)
                if test_case:
                    rows_yielded += 1
                    stats.rows_read = rows_yielded

                    if progress_callback and rows_yielded % self.config.chunk_size == 0:
                        stats.chunks_processed = rows_yielded // self.config.chunk_size
                        stats.bytes_read = f.tell()
                        progress_callback(stats)

                    yield test_case

    def _item_to_test_case(self, item: dict[str, Any]) -> TestCase | None:
        """JSON 항목을 TestCase로 변환.

        Args:
            item: JSON 객체

        Returns:
            TestCase 또는 None
        """
        try:
            contexts = item.get("contexts", [])
            if isinstance(contexts, str):
                contexts = [contexts]

            return TestCase(
                id=str(item["id"]),
                question=str(item["question"]),
                answer=str(item["answer"]),
                contexts=contexts,
                ground_truth=item.get("ground_truth"),
            )
        except KeyError:
            return None


class StreamingDatasetLoader:
    """통합 스트리밍 데이터셋 로더.

    파일 형식에 따라 적절한 로더를 선택.
    """

    def __init__(self, config: StreamingConfig | None = None):
        """초기화.

        Args:
            config: 스트리밍 설정
        """
        self.config = config or StreamingConfig()
        self._loaders = [
            StreamingCSVLoader(self.config),
            StreamingJSONLoader(self.config),
        ]

    def stream(
        self,
        file_path: str | Path,
        progress_callback: Callable[[StreamingStats], None] | None = None,
    ) -> StreamingTestCaseIterator:
        """파일을 스트리밍으로 읽기.

        Args:
            file_path: 데이터셋 파일 경로
            progress_callback: 진행 콜백 함수

        Returns:
            테스트 케이스 이터레이터

        Raises:
            ValueError: 지원하지 않는 파일 형식
        """
        for loader in self._loaders:
            if loader.supports(file_path):
                return loader.stream(file_path, progress_callback)

        raise ValueError(f"Unsupported file format: {Path(file_path).suffix}")

    def load_chunked(
        self,
        file_path: str | Path,
        chunk_size: int | None = None,
    ) -> Generator[list[TestCase], None, None]:
        """청크 단위로 데이터를 로드.

        메모리 사용량을 제한하면서 데이터를 처리할 때 유용.

        Args:
            file_path: 데이터셋 파일 경로
            chunk_size: 청크 크기 (기본값: config.chunk_size)

        Yields:
            TestCase 리스트 (청크)

        Example:
            for chunk in loader.load_chunked("large_dataset.csv"):
                results = await evaluate_batch(chunk)
                process_results(results)
        """
        size = chunk_size or self.config.chunk_size
        iterator = self.stream(file_path)
        chunk: list[TestCase] = []

        for test_case in iterator:
            chunk.append(test_case)
            if len(chunk) >= size:
                yield chunk
                chunk = []

        # 마지막 청크
        if chunk:
            yield chunk

    def load_as_dataset(
        self,
        file_path: str | Path,
        name: str | None = None,
        version: str = "1.0.0",
    ) -> Dataset:
        """스트리밍으로 읽은 데이터를 Dataset 객체로 변환.

        주의: 전체 데이터를 메모리에 로드합니다.
        대용량 데이터셋은 load_chunked() 사용을 권장합니다.

        Args:
            file_path: 데이터셋 파일 경로
            name: 데이터셋 이름 (없으면 파일명 사용)
            version: 데이터셋 버전

        Returns:
            Dataset 객체
        """
        test_cases = list(self.stream(file_path))
        path = Path(file_path)

        return Dataset(
            name=name or path.stem,
            version=version,
            test_cases=test_cases,
            source_file=str(path),
        )


def stream_file(
    file_path: str | Path,
    chunk_size: int = 100,
) -> Generator[TestCase, None, None]:
    """파일을 스트리밍으로 읽는 간편 함수.

    Args:
        file_path: 데이터셋 파일 경로
        chunk_size: 청크 크기

    Yields:
        TestCase 객체

    Example:
        for test_case in stream_file("large_dataset.csv"):
            result = await evaluate_single(test_case)
    """
    config = StreamingConfig(chunk_size=chunk_size)
    loader = StreamingDatasetLoader(config)
    yield from loader.stream(file_path)


def load_in_chunks(
    file_path: str | Path,
    chunk_size: int = 100,
) -> Generator[list[TestCase], None, None]:
    """파일을 청크 단위로 로드하는 간편 함수.

    Args:
        file_path: 데이터셋 파일 경로
        chunk_size: 청크 크기

    Yields:
        TestCase 리스트 (청크)

    Example:
        for chunk in load_in_chunks("large_dataset.csv", chunk_size=50):
            results = await evaluate_batch(chunk)
    """
    config = StreamingConfig(chunk_size=chunk_size)
    loader = StreamingDatasetLoader(config)
    yield from loader.load_chunked(file_path, chunk_size)


__all__ = [
    "StreamingCSVLoader",
    "StreamingConfig",
    "StreamingDatasetLoader",
    "StreamingJSONLoader",
    "StreamingStats",
    "StreamingTestCaseIterator",
    "load_in_chunks",
    "stream_file",
]
