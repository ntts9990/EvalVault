"""Tests for Streaming Dataset Loader."""

import json

import pytest

from evalvault.adapters.outbound.dataset.streaming_loader import (
    StreamingConfig,
    StreamingCSVLoader,
    StreamingDatasetLoader,
    StreamingJSONLoader,
    StreamingStats,
    StreamingTestCaseIterator,
    load_in_chunks,
    stream_file,
)
from evalvault.domain.entities.dataset import TestCase


class TestStreamingConfig:
    """StreamingConfig 테스트."""

    def test_default_config(self):
        """기본 설정 테스트."""
        config = StreamingConfig()

        assert config.chunk_size == 100
        assert config.skip_rows == 0
        assert config.max_rows is None
        assert config.encoding is None

    def test_custom_config(self):
        """사용자 정의 설정 테스트."""
        config = StreamingConfig(
            chunk_size=50,
            skip_rows=10,
            max_rows=100,
            encoding="utf-8",
        )

        assert config.chunk_size == 50
        assert config.skip_rows == 10
        assert config.max_rows == 100
        assert config.encoding == "utf-8"


class TestStreamingCSVLoader:
    """StreamingCSVLoader 테스트."""

    @pytest.fixture
    def csv_file(self, tmp_path):
        """테스트용 CSV 파일 생성."""
        content = """id,question,answer,contexts,ground_truth
tc-001,질문1,답변1,"[""컨텍스트1""]",정답1
tc-002,질문2,답변2,"[""컨텍스트2"",""컨텍스트3""]",정답2
tc-003,질문3,답변3,"컨텍스트4|컨텍스트5",정답3
tc-004,질문4,답변4,[],
tc-005,질문5,답변5,"[""컨텍스트6""]",정답5
"""
        file_path = tmp_path / "test.csv"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    @pytest.fixture
    def loader(self):
        """기본 로더 인스턴스."""
        return StreamingCSVLoader()

    def test_supports_csv(self, loader):
        """CSV 파일 지원 확인."""
        assert loader.supports("test.csv") is True
        assert loader.supports("test.CSV") is True
        assert loader.supports("test.json") is False

    def test_stream_all_rows(self, loader, csv_file):
        """모든 행 스트리밍."""
        iterator = loader.stream(csv_file)
        test_cases = list(iterator)

        assert len(test_cases) == 5
        assert all(isinstance(tc, TestCase) for tc in test_cases)

    def test_stream_row_content(self, loader, csv_file):
        """행 내용 확인."""
        iterator = loader.stream(csv_file)
        test_cases = list(iterator)

        assert test_cases[0].id == "tc-001"
        assert test_cases[0].question == "질문1"
        assert test_cases[0].answer == "답변1"
        assert test_cases[0].contexts == ["컨텍스트1"]
        assert test_cases[0].ground_truth == "정답1"

    def test_stream_with_skip_rows(self, csv_file):
        """행 스킵 테스트."""
        config = StreamingConfig(skip_rows=2)
        loader = StreamingCSVLoader(config=config)
        iterator = loader.stream(csv_file)
        test_cases = list(iterator)

        assert len(test_cases) == 3
        assert test_cases[0].id == "tc-003"

    def test_stream_with_max_rows(self, csv_file):
        """최대 행 제한 테스트."""
        config = StreamingConfig(max_rows=3)
        loader = StreamingCSVLoader(config=config)
        iterator = loader.stream(csv_file)
        test_cases = list(iterator)

        assert len(test_cases) == 3

    def test_stream_json_contexts(self, loader, csv_file):
        """JSON 형식 컨텍스트 파싱."""
        iterator = loader.stream(csv_file)
        test_cases = list(iterator)

        # 단일 컨텍스트
        assert test_cases[0].contexts == ["컨텍스트1"]
        # 복수 컨텍스트
        assert test_cases[1].contexts == ["컨텍스트2", "컨텍스트3"]

    def test_stream_pipe_contexts(self, loader, csv_file):
        """파이프 구분 컨텍스트 파싱."""
        iterator = loader.stream(csv_file)
        test_cases = list(iterator)

        assert test_cases[2].contexts == ["컨텍스트4", "컨텍스트5"]

    def test_stream_empty_contexts(self, loader, csv_file):
        """빈 컨텍스트 처리."""
        iterator = loader.stream(csv_file)
        test_cases = list(iterator)

        assert test_cases[3].contexts == []

    def test_stream_empty_ground_truth(self, loader, csv_file):
        """빈 ground_truth 처리."""
        iterator = loader.stream(csv_file)
        test_cases = list(iterator)

        assert test_cases[3].ground_truth is None

    def test_stream_file_not_found(self, loader):
        """존재하지 않는 파일."""
        with pytest.raises(FileNotFoundError):
            list(loader.stream("nonexistent.csv"))

    def test_stream_missing_columns(self, tmp_path):
        """필수 컬럼 누락."""
        content = """id,question,answer
tc-001,질문1,답변1
"""
        file_path = tmp_path / "missing_cols.csv"
        file_path.write_text(content, encoding="utf-8")

        loader = StreamingCSVLoader()
        with pytest.raises(ValueError, match="Missing required columns"):
            list(loader.stream(file_path))

    def test_progress_callback(self, csv_file):
        """진행 콜백 테스트."""
        progress_updates = []

        def on_progress(stats: StreamingStats):
            progress_updates.append(stats.rows_read)

        config = StreamingConfig(chunk_size=2)
        loader = StreamingCSVLoader(config=config)
        list(loader.stream(csv_file, progress_callback=on_progress))

        # 청크마다 콜백 호출
        assert len(progress_updates) >= 2


class TestStreamingJSONLoader:
    """StreamingJSONLoader 테스트."""

    @pytest.fixture
    def json_file_with_key(self, tmp_path):
        """test_cases 키가 있는 JSON 파일."""
        data = {
            "name": "test-dataset",
            "test_cases": [
                {
                    "id": "tc-001",
                    "question": "질문1",
                    "answer": "답변1",
                    "contexts": ["컨텍스트1"],
                    "ground_truth": "정답1",
                },
                {
                    "id": "tc-002",
                    "question": "질문2",
                    "answer": "답변2",
                    "contexts": ["컨텍스트2", "컨텍스트3"],
                    "ground_truth": "정답2",
                },
            ],
        }
        file_path = tmp_path / "test.json"
        file_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return file_path

    @pytest.fixture
    def json_file_array(self, tmp_path):
        """배열 형식 JSON 파일."""
        data = [
            {
                "id": "tc-001",
                "question": "질문1",
                "answer": "답변1",
                "contexts": ["컨텍스트1"],
            },
            {
                "id": "tc-002",
                "question": "질문2",
                "answer": "답변2",
                "contexts": ["컨텍스트2"],
            },
        ]
        file_path = tmp_path / "test_array.json"
        file_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return file_path

    @pytest.fixture
    def loader(self):
        """기본 로더 인스턴스."""
        return StreamingJSONLoader()

    def test_supports_json(self, loader):
        """JSON 파일 지원 확인."""
        assert loader.supports("test.json") is True
        assert loader.supports("test.JSON") is True
        assert loader.supports("test.csv") is False

    def test_stream_with_key(self, loader, json_file_with_key):
        """test_cases 키가 있는 JSON 스트리밍."""
        iterator = loader.stream(json_file_with_key)
        test_cases = list(iterator)

        assert len(test_cases) == 2
        assert test_cases[0].id == "tc-001"

    def test_stream_array(self, loader, json_file_array):
        """배열 형식 JSON 스트리밍."""
        iterator = loader.stream(json_file_array)
        test_cases = list(iterator)

        assert len(test_cases) == 2
        assert test_cases[0].id == "tc-001"

    def test_stream_with_skip(self, json_file_with_key):
        """스킵 테스트."""
        config = StreamingConfig(skip_rows=1)
        loader = StreamingJSONLoader(config=config)
        iterator = loader.stream(json_file_with_key)
        test_cases = list(iterator)

        assert len(test_cases) == 1
        assert test_cases[0].id == "tc-002"


class TestStreamingDatasetLoader:
    """StreamingDatasetLoader 통합 테스트."""

    @pytest.fixture
    def csv_file(self, tmp_path):
        """테스트용 CSV 파일."""
        content = """id,question,answer,contexts,ground_truth
tc-001,질문1,답변1,"[""컨텍스트1""]",정답1
tc-002,질문2,답변2,"[""컨텍스트2""]",정답2
tc-003,질문3,답변3,"[""컨텍스트3""]",정답3
tc-004,질문4,답변4,"[""컨텍스트4""]",정답4
tc-005,질문5,답변5,"[""컨텍스트5""]",정답5
"""
        file_path = tmp_path / "test.csv"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    @pytest.fixture
    def loader(self):
        """기본 로더 인스턴스."""
        return StreamingDatasetLoader()

    def test_auto_detect_csv(self, loader, csv_file):
        """CSV 자동 감지."""
        iterator = loader.stream(csv_file)
        test_cases = list(iterator)

        assert len(test_cases) == 5

    def test_load_chunked(self, csv_file):
        """청크 단위 로딩."""
        config = StreamingConfig(chunk_size=2)
        loader = StreamingDatasetLoader(config)

        chunks = list(loader.load_chunked(csv_file, chunk_size=2))

        assert len(chunks) == 3  # 5 items / 2 = 3 chunks
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 2
        assert len(chunks[2]) == 1  # 마지막 청크

    def test_load_as_dataset(self, loader, csv_file):
        """Dataset 객체로 변환."""
        dataset = loader.load_as_dataset(csv_file, name="my-dataset", version="2.0.0")

        assert dataset.name == "my-dataset"
        assert dataset.version == "2.0.0"
        assert len(dataset.test_cases) == 5

    def test_unsupported_format(self, loader, tmp_path):
        """지원하지 않는 형식."""
        file_path = tmp_path / "test.xlsx"
        file_path.touch()

        with pytest.raises(ValueError, match="Unsupported file format"):
            list(loader.stream(file_path))


class TestStreamingTestCaseIterator:
    """StreamingTestCaseIterator 테스트."""

    def test_iterator_protocol(self):
        """이터레이터 프로토콜 확인."""

        def gen():
            yield TestCase(id="1", question="Q", answer="A", contexts=[])
            yield TestCase(id="2", question="Q", answer="A", contexts=[])

        iterator = StreamingTestCaseIterator(gen())

        assert iter(iterator) is iterator
        assert next(iterator).id == "1"
        assert next(iterator).id == "2"

        with pytest.raises(StopIteration):
            next(iterator)

    def test_stats_updated(self):
        """통계 업데이트 확인."""

        def gen():
            yield TestCase(id="1", question="Q", answer="A", contexts=[])
            yield TestCase(id="2", question="Q", answer="A", contexts=[])

        iterator = StreamingTestCaseIterator(gen())
        list(iterator)

        assert iterator.stats.rows_read == 2


class TestConvenienceFunctions:
    """간편 함수 테스트."""

    @pytest.fixture
    def csv_file(self, tmp_path):
        """테스트용 CSV 파일."""
        content = """id,question,answer,contexts,ground_truth
tc-001,질문1,답변1,"[""컨텍스트1""]",정답1
tc-002,질문2,답변2,"[""컨텍스트2""]",정답2
tc-003,질문3,답변3,"[""컨텍스트3""]",정답3
"""
        file_path = tmp_path / "test.csv"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def test_stream_file(self, csv_file):
        """stream_file 함수."""
        test_cases = list(stream_file(csv_file))

        assert len(test_cases) == 3
        assert all(isinstance(tc, TestCase) for tc in test_cases)

    def test_load_in_chunks(self, csv_file):
        """load_in_chunks 함수."""
        chunks = list(load_in_chunks(csv_file, chunk_size=2))

        assert len(chunks) == 2
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 1


class TestEncodingHandling:
    """인코딩 처리 테스트."""

    def test_utf8_bom(self, tmp_path):
        """UTF-8 BOM 처리."""
        # utf-8-sig 인코딩으로 저장 (BOM 자동 추가)
        content = "id,question,answer,contexts,ground_truth\ntc-001,질문,답변,[],\n"
        file_path = tmp_path / "bom.csv"
        file_path.write_text(content, encoding="utf-8-sig")

        # utf-8-sig로 읽으면 BOM이 자동으로 처리됨
        config = StreamingConfig(encoding="utf-8-sig")
        loader = StreamingCSVLoader(config=config)
        test_cases = list(loader.stream(file_path))

        assert len(test_cases) == 1
        assert test_cases[0].id == "tc-001"

    def test_explicit_encoding(self, tmp_path):
        """명시적 인코딩 지정."""
        content = "id,question,answer,contexts,ground_truth\ntc-001,질문,답변,[],\n"
        file_path = tmp_path / "explicit.csv"
        file_path.write_text(content, encoding="utf-8")

        config = StreamingConfig(encoding="utf-8")
        loader = StreamingCSVLoader(config=config)
        test_cases = list(loader.stream(file_path))

        assert len(test_cases) == 1


class TestLargeDatasetSimulation:
    """대용량 데이터셋 시뮬레이션 테스트."""

    def test_memory_efficient_iteration(self, tmp_path):
        """메모리 효율적 반복 테스트."""
        # 1000개 행 생성
        rows = ["id,question,answer,contexts,ground_truth"]
        for i in range(1000):
            rows.append(f'tc-{i:04d},Q{i},A{i},"[]",GT{i}')

        content = "\n".join(rows)
        file_path = tmp_path / "large.csv"
        file_path.write_text(content, encoding="utf-8")

        # 스트리밍으로 읽기
        loader = StreamingDatasetLoader()
        count = 0
        for tc in loader.stream(file_path):
            count += 1
            # 각 항목을 처리하고 버림 (메모리 해제)
            assert tc.id.startswith("tc-")

        assert count == 1000

    def test_chunked_processing(self, tmp_path):
        """청크 단위 처리 테스트."""
        # 100개 행 생성
        rows = ["id,question,answer,contexts,ground_truth"]
        for i in range(100):
            rows.append(f'tc-{i:04d},Q{i},A{i},"[]",GT{i}')

        content = "\n".join(rows)
        file_path = tmp_path / "chunked.csv"
        file_path.write_text(content, encoding="utf-8")

        loader = StreamingDatasetLoader()
        total_processed = 0
        chunk_sizes = []

        for chunk in loader.load_chunked(file_path, chunk_size=30):
            chunk_sizes.append(len(chunk))
            total_processed += len(chunk)

        assert total_processed == 100
        assert chunk_sizes == [30, 30, 30, 10]
