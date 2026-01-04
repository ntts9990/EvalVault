"""Unit tests for Web UI History page components."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from evalvault.ports.inbound.web_port import RunFilters, RunSummary
from tests.optional_deps import skip_if_missing_web

if TYPE_CHECKING:
    pass

skip_if_missing_web()


PROMPT_SAMPLE = [
    {
        "path": "/tmp/system.txt",
        "status": "modified",
        "phoenix_prompt_id": "pr-1",
        "diff": "- hi\n+ hello",
    }
]


def create_sample_run(
    run_id: str = "run-1",
    dataset_name: str = "test-dataset",
    model_name: str = "gpt-5-nano",
    pass_rate: float = 0.85,
    days_ago: int = 0,
    prompts: list[dict[str, str]] | None = None,
    run_mode: str | None = None,
) -> RunSummary:
    """테스트용 RunSummary 생성."""
    started_at = datetime.now() - timedelta(days=days_ago)
    return RunSummary(
        run_id=run_id,
        dataset_name=dataset_name,
        model_name=model_name,
        pass_rate=pass_rate,
        total_test_cases=100,
        started_at=started_at,
        finished_at=started_at + timedelta(minutes=5),
        metrics_evaluated=["faithfulness", "answer_relevancy"],
        run_mode=run_mode,
        total_tokens=1000,
        total_cost_usd=0.10,
        phoenix_prompts=prompts or [],
    )


class TestRunFilter:
    """RunFilter 컴포넌트 테스트."""

    def test_filter_can_be_imported(self):
        """필터 임포트 확인."""
        from evalvault.adapters.inbound.web.components.history import RunFilter

        assert RunFilter is not None

    def test_create_empty_filter(self):
        """빈 필터 생성."""
        from evalvault.adapters.inbound.web.components.history import RunFilter

        filter_component = RunFilter()

        assert filter_component.dataset_name is None
        assert filter_component.model_name is None
        assert filter_component.min_pass_rate is None

    def test_apply_dataset_filter(self):
        """데이터셋 이름 필터 적용."""
        from evalvault.adapters.inbound.web.components.history import RunFilter

        runs = [
            create_sample_run(run_id="1", dataset_name="insurance-qa"),
            create_sample_run(run_id="2", dataset_name="medical-qa"),
            create_sample_run(run_id="3", dataset_name="insurance-qa"),
        ]

        filter_component = RunFilter(dataset_name="insurance-qa")
        filtered = filter_component.apply(runs)

        assert len(filtered) == 2
        assert all(r.dataset_name == "insurance-qa" for r in filtered)

    def test_apply_model_filter(self):
        """모델 필터 적용."""
        from evalvault.adapters.inbound.web.components.history import RunFilter

        runs = [
            create_sample_run(run_id="1", model_name="gpt-5-nano"),
            create_sample_run(run_id="2", model_name="gpt-4"),
            create_sample_run(run_id="3", model_name="gpt-5-nano"),
        ]

        filter_component = RunFilter(model_name="gpt-4")
        filtered = filter_component.apply(runs)

        assert len(filtered) == 1
        assert filtered[0].model_name == "gpt-4"

    def test_apply_pass_rate_filter(self):
        """통과율 필터 적용."""
        from evalvault.adapters.inbound.web.components.history import RunFilter

        runs = [
            create_sample_run(run_id="1", pass_rate=0.9),
            create_sample_run(run_id="2", pass_rate=0.5),
            create_sample_run(run_id="3", pass_rate=0.7),
        ]

        filter_component = RunFilter(min_pass_rate=0.7)
        filtered = filter_component.apply(runs)

        assert len(filtered) == 2
        assert all(r.pass_rate >= 0.7 for r in filtered)

    def test_apply_date_range_filter(self):
        """날짜 범위 필터 적용."""
        from evalvault.adapters.inbound.web.components.history import RunFilter

        runs = [
            create_sample_run(run_id="1", days_ago=1),
            create_sample_run(run_id="2", days_ago=5),
            create_sample_run(run_id="3", days_ago=10),
        ]

        filter_component = RunFilter(
            date_from=datetime.now() - timedelta(days=7),
            date_to=datetime.now(),
        )
        filtered = filter_component.apply(runs)

        assert len(filtered) == 2

    def test_apply_multiple_filters(self):
        """복합 필터 적용."""
        from evalvault.adapters.inbound.web.components.history import RunFilter

        runs = [
            create_sample_run(
                run_id="1", dataset_name="qa", model_name="gpt-5-nano", pass_rate=0.9
            ),
            create_sample_run(run_id="2", dataset_name="qa", model_name="gpt-4", pass_rate=0.8),
            create_sample_run(
                run_id="3", dataset_name="test", model_name="gpt-5-nano", pass_rate=0.9
            ),
        ]

        filter_component = RunFilter(
            dataset_name="qa",
            model_name="gpt-5-nano",
            min_pass_rate=0.8,
        )
        filtered = filter_component.apply(runs)

        assert len(filtered) == 1
        assert filtered[0].run_id == "1"

    def test_apply_run_mode_filter(self):
        """실행 모드 필터 적용."""
        from evalvault.adapters.inbound.web.components.history import RunFilter

        runs = [
            create_sample_run(run_id="1", run_mode="simple"),
            create_sample_run(run_id="2", run_mode="full"),
            create_sample_run(run_id="3", run_mode="simple"),
        ]
        filter_component = RunFilter(run_mode="simple")
        filtered = filter_component.apply(runs)

        assert len(filtered) == 2
        assert all(r.run_mode == "simple" for r in filtered)

    def test_to_run_filters(self):
        """RunFilters로 변환."""
        from evalvault.adapters.inbound.web.components.history import RunFilter

        filter_component = RunFilter(
            dataset_name="test",
            model_name="gpt-4",
            min_pass_rate=0.7,
            run_mode="simple",
        )

        run_filters = filter_component.to_run_filters()

        assert isinstance(run_filters, RunFilters)
        assert run_filters.dataset_name == "test"
        assert run_filters.model_name == "gpt-4"
        assert run_filters.min_pass_rate == 0.7
        assert run_filters.run_mode == "simple"


class TestRunTable:
    """RunTable 컴포넌트 테스트."""

    def test_table_can_be_imported(self):
        """테이블 임포트 확인."""
        from evalvault.adapters.inbound.web.components.history import RunTable

        assert RunTable is not None

    def test_create_table(self):
        """테이블 생성."""
        from evalvault.adapters.inbound.web.components.history import RunTable

        runs = [create_sample_run(run_id=f"run-{i}") for i in range(5)]
        table = RunTable(runs=runs)

        assert len(table.runs) == 5
        assert table.page == 1
        assert table.page_size == 10

    def test_get_current_page_runs(self):
        """현재 페이지 실행 목록."""
        from evalvault.adapters.inbound.web.components.history import RunTable

        runs = [create_sample_run(run_id=f"run-{i}") for i in range(25)]
        table = RunTable(runs=runs, page_size=10)

        # 첫 페이지
        page_runs = table.get_current_page_runs()
        assert len(page_runs) == 10

        # 두 번째 페이지
        table.page = 2
        page_runs = table.get_current_page_runs()
        assert len(page_runs) == 10

        # 세 번째 페이지 (마지막)
        table.page = 3
        page_runs = table.get_current_page_runs()
        assert len(page_runs) == 5

    def test_total_pages(self):
        """총 페이지 수."""
        from evalvault.adapters.inbound.web.components.history import RunTable

        runs = [create_sample_run(run_id=f"run-{i}") for i in range(25)]
        table = RunTable(runs=runs, page_size=10)

        assert table.total_pages == 3

    def test_sort_by_date(self):
        """날짜순 정렬."""
        from evalvault.adapters.inbound.web.components.history import RunTable

        runs = [
            create_sample_run(run_id="1", days_ago=5),
            create_sample_run(run_id="2", days_ago=1),
            create_sample_run(run_id="3", days_ago=10),
        ]
        table = RunTable(runs=runs)

        sorted_runs = table.sort_by("date", ascending=False)

        assert sorted_runs[0].run_id == "2"  # 가장 최근
        assert sorted_runs[2].run_id == "3"  # 가장 오래됨

    def test_sort_by_pass_rate(self):
        """통과율순 정렬."""
        from evalvault.adapters.inbound.web.components.history import RunTable

        runs = [
            create_sample_run(run_id="1", pass_rate=0.7),
            create_sample_run(run_id="2", pass_rate=0.9),
            create_sample_run(run_id="3", pass_rate=0.5),
        ]
        table = RunTable(runs=runs)

        sorted_runs = table.sort_by("pass_rate", ascending=False)

        assert sorted_runs[0].run_id == "2"  # 가장 높음
        assert sorted_runs[2].run_id == "3"  # 가장 낮음

    def test_to_dataframe(self):
        """DataFrame으로 변환."""
        from evalvault.adapters.inbound.web.components.history import RunTable

        runs = [create_sample_run(run_id=f"run-{i}") for i in range(3)]
        table = RunTable(runs=runs)

        df = table.to_dataframe()

        assert len(df) == 3
        assert "dataset_name" in df.columns
        assert "pass_rate" in df.columns


class TestRunDetailPanel:
    """RunDetailPanel 컴포넌트 테스트."""

    def test_panel_can_be_imported(self):
        """패널 임포트 확인."""
        from evalvault.adapters.inbound.web.components.history import RunDetailPanel

        assert RunDetailPanel is not None

    def test_create_panel(self):
        """패널 생성."""
        from evalvault.adapters.inbound.web.components.history import RunDetailPanel

        run = create_sample_run()
        panel = RunDetailPanel(run=run)

        assert panel.run == run

    def test_get_summary_stats(self):
        """요약 통계."""
        from evalvault.adapters.inbound.web.components.history import RunDetailPanel

        run = create_sample_run(pass_rate=0.85)
        panel = RunDetailPanel(run=run)

        stats = panel.get_summary_stats()

        assert "pass_rate" in stats
        assert stats["pass_rate"] == 0.85
        assert "total_test_cases" in stats
        assert "duration" in stats

    def test_get_metrics_breakdown(self):
        """메트릭 분석."""
        from evalvault.adapters.inbound.web.components.history import RunDetailPanel

        run = create_sample_run()
        panel = RunDetailPanel(run=run)

        breakdown = panel.get_metrics_breakdown()

        assert "faithfulness" in breakdown
        assert "answer_relevancy" in breakdown

    def test_format_duration(self):
        """소요 시간 포맷."""
        from evalvault.adapters.inbound.web.components.history import RunDetailPanel

        run = create_sample_run()
        panel = RunDetailPanel(run=run)

        duration = panel.format_duration()

        assert "m" in duration or "s" in duration  # 분 또는 초 포함

    def test_get_prompt_entries(self):
        """Prompt 메타데이터 조회."""
        from evalvault.adapters.inbound.web.components.history import RunDetailPanel

        run = create_sample_run(prompts=PROMPT_SAMPLE)
        panel = RunDetailPanel(run=run)

        entries = panel.get_prompt_entries()

        assert len(entries) == 1
        assert entries[0]["status"] == "modified"


class TestHistoryExport:
    """History 내보내기 테스트."""

    def test_export_can_be_imported(self):
        """내보내기 임포트 확인."""
        from evalvault.adapters.inbound.web.components.history import HistoryExporter

        assert HistoryExporter is not None

    def test_export_to_csv(self):
        """CSV 내보내기."""
        from evalvault.adapters.inbound.web.components.history import HistoryExporter

        runs = [
            create_sample_run(run_id="run-0", prompts=PROMPT_SAMPLE, run_mode="simple"),
            create_sample_run(run_id="run-1", run_mode="full"),
            create_sample_run(run_id="run-2"),
        ]
        exporter = HistoryExporter(runs=runs)

        csv_content = exporter.to_csv()

        assert "run_id" in csv_content
        assert "dataset_name" in csv_content
        assert "phoenix_precision" in csv_content
        assert "run_mode" in csv_content
        assert "simple" in csv_content
        assert "phoenix_prompt_summary" in csv_content
        assert "1 drift" in csv_content
        assert "system.txt" in csv_content
        assert "run-0" in csv_content

    def test_export_to_json(self):
        """JSON 내보내기."""
        import json

        from evalvault.adapters.inbound.web.components.history import HistoryExporter

        runs = [
            create_sample_run(run_id="run-0", prompts=PROMPT_SAMPLE, run_mode="simple"),
            create_sample_run(run_id="run-1", run_mode="full"),
            create_sample_run(run_id="run-2"),
        ]
        exporter = HistoryExporter(runs=runs)

        json_content = exporter.to_json()
        data = json.loads(json_content)

        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["run_id"] == "run-0"
        assert "phoenix_precision" in data[0]
        assert data[0]["phoenix_prompts"]
        assert data[0]["phoenix_prompt_summary"] is not None
        assert data[0]["run_mode"] == "simple"


class TestSearchComponent:
    """검색 컴포넌트 테스트."""

    def test_search_can_be_imported(self):
        """검색 임포트 확인."""
        from evalvault.adapters.inbound.web.components.history import RunSearch

        assert RunSearch is not None

    def test_search_by_dataset_name(self):
        """데이터셋 이름으로 검색."""
        from evalvault.adapters.inbound.web.components.history import RunSearch

        runs = [
            create_sample_run(run_id="1", dataset_name="insurance-qa-v1"),
            create_sample_run(run_id="2", dataset_name="medical-qa"),
            create_sample_run(run_id="3", dataset_name="insurance-qa-v2"),
        ]

        search = RunSearch(query="insurance")
        results = search.search(runs)

        assert len(results) == 2
        assert all("insurance" in r.dataset_name for r in results)

    def test_search_case_insensitive(self):
        """대소문자 구분 없는 검색."""
        from evalvault.adapters.inbound.web.components.history import RunSearch

        runs = [
            create_sample_run(run_id="1", dataset_name="Insurance-QA"),
            create_sample_run(run_id="2", dataset_name="INSURANCE-test"),
        ]

        search = RunSearch(query="insurance")
        results = search.search(runs)

        assert len(results) == 2

    def test_empty_search(self):
        """빈 검색어."""
        from evalvault.adapters.inbound.web.components.history import RunSearch

        runs = [create_sample_run(run_id=f"run-{i}") for i in range(3)]

        search = RunSearch(query="")
        results = search.search(runs)

        assert len(results) == 3  # 필터링 없이 전체 반환
