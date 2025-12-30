"""EvalVault Web UI - Streamlit Application."""

from __future__ import annotations

import sys
from pathlib import Path

# Streamlit 앱 실행 시 src 경로 추가
src_path = Path(__file__).parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def create_app():
    """Streamlit 앱 생성 및 설정."""
    import streamlit as st

    from evalvault.adapters.inbound.web.adapter import create_adapter
    from evalvault.adapters.inbound.web.session import init_session

    # 페이지 설정
    st.set_page_config(
        page_title="EvalVault",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 세션 초기화
    session = init_session()

    # 어댑터 초기화 (세션에 캐시)
    if "adapter" not in st.session_state:
        st.session_state.adapter = create_adapter()

    adapter = st.session_state.adapter

    # 사이드바
    with st.sidebar:
        st.title("📊 EvalVault")
        st.caption("RAG Evaluation System")

        st.divider()

        # 네비게이션
        page = st.radio(
            "Navigation",
            options=["🏠 Home", "📊 Evaluate", "📋 History", "📄 Reports"],
            label_visibility="collapsed",
        )

        st.divider()

        # 설정 섹션
        with st.expander("⚙️ Settings", expanded=False):
            st.caption("Model Configuration")
            model = st.selectbox(
                "Default Model",
                options=["gpt-5-nano", "gpt-4", "gpt-4o", "claude-3-5-sonnet"],
                index=0,
            )
            session.selected_model = model

        # 버전 정보
        st.caption("v1.3.0 | Powered by Ragas + Langfuse")

    # 메인 컨텐츠
    if page == "🏠 Home":
        render_home_page(adapter, session)
    elif page == "📊 Evaluate":
        render_evaluate_page(adapter, session)
    elif page == "📋 History":
        render_history_page(adapter, session)
    elif page == "📄 Reports":
        render_reports_page(adapter, session)


def render_home_page(adapter, session):
    """홈 페이지 렌더링."""
    import streamlit as st

    from evalvault.adapters.inbound.web.components import (
        DashboardStats,
        MetricSummaryCard,
        RecentRunsList,
        create_pass_rate_chart,
        create_trend_chart,
    )

    st.header("Welcome to EvalVault")
    st.markdown(
        """
        EvalVault는 RAG (Retrieval-Augmented Generation) 시스템을 평가하고
        분석하기 위한 도구입니다.
        """
    )

    # 평가 데이터 조회
    runs = adapter.list_runs(limit=20)

    # 대시보드 통계 계산
    stats = DashboardStats.from_runs(runs)

    # 통계 카드 섹션
    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        card = MetricSummaryCard(
            title="Total Runs",
            value=stats.total_runs,
            format_type="number",
        )
        st.metric(label=card.title, value=card.formatted_value)

    with col2:
        card = MetricSummaryCard(
            title="Test Cases",
            value=stats.total_test_cases,
            format_type="number",
        )
        st.metric(label=card.title, value=card.formatted_value)

    with col3:
        card = MetricSummaryCard(
            title="Avg Pass Rate",
            value=stats.avg_pass_rate,
            format_type="percent",
        )
        st.metric(label=card.title, value=card.formatted_value)

    with col4:
        card = MetricSummaryCard(
            title="Total Cost",
            value=stats.total_cost,
            format_type="currency",
        )
        st.metric(label=card.title, value=card.formatted_value)

    # 차트 섹션
    st.divider()
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        pass_rate_fig = create_pass_rate_chart(runs[:10])
        st.plotly_chart(pass_rate_fig, use_container_width=True)

    with chart_col2:
        trend_fig = create_trend_chart(runs)
        st.plotly_chart(trend_fig, use_container_width=True)

    # 지원 메트릭 섹션
    st.divider()
    with st.expander("📊 지원 메트릭", expanded=False):
        metrics = adapter.get_available_metrics()
        descriptions = adapter.get_metric_descriptions()

        cols = st.columns(3)
        for i, metric in enumerate(metrics):
            with cols[i % 3]:
                st.markdown(
                    f"""
                    <div style="
                        padding: 0.75rem;
                        border-radius: 0.5rem;
                        border: 1px solid #334155;
                        margin-bottom: 0.5rem;
                    ">
                        <strong>{metric}</strong><br>
                        <small style="color: #94A3B8;">{descriptions.get(metric, "")}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # 최근 평가 목록
    st.divider()
    st.subheader("최근 평가")

    recent_list = RecentRunsList(runs=runs, max_items=5)

    if not recent_list.is_empty:
        for run in recent_list.displayed_runs:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                emoji = recent_list.get_pass_rate_emoji(run.pass_rate)
                st.text(f"{emoji} {run.dataset_name}")
            with col2:
                st.text(run.model_name)
            with col3:
                pass_rate_pct = run.pass_rate * 100
                if pass_rate_pct >= 70:
                    st.success(f"{pass_rate_pct:.1f}%")
                elif pass_rate_pct >= 50:
                    st.warning(f"{pass_rate_pct:.1f}%")
                else:
                    st.error(f"{pass_rate_pct:.1f}%")
            with col4:
                st.text(run.started_at.strftime("%m/%d"))

        if recent_list.has_more:
            st.caption(f"+{recent_list.remaining_count} more runs...")
    else:
        st.info("아직 평가 이력이 없습니다. 첫 평가를 실행해보세요!")


def render_evaluate_page(adapter, session):
    """평가 실행 페이지 렌더링."""
    import streamlit as st

    from evalvault.adapters.inbound.web.components import (
        FileUploadHandler,
        MetricSelector,
    )

    st.header("📊 Evaluate")
    st.markdown("데이터셋을 업로드하고 RAG 평가를 실행합니다.")

    # 초기화
    upload_handler = FileUploadHandler()
    metric_selector = MetricSelector()

    # 파일 업로드 섹션
    st.subheader("1. 데이터셋 업로드")

    uploaded_file = st.file_uploader(
        "데이터셋 업로드",
        type=["csv", "json", "xlsx"],
        help="CSV, JSON, 또는 Excel 형식의 데이터셋을 업로드하세요.",
    )

    validation_result = None
    if uploaded_file:
        # 파일 검증
        content = uploaded_file.read()
        uploaded_file.seek(0)  # 다시 읽을 수 있도록 리셋

        validation_result = upload_handler.validate_file(uploaded_file.name, content)

        if validation_result.is_valid:
            st.success(
                f"✅ {uploaded_file.name} ({validation_result.row_count} rows, "
                f"{validation_result.file_type.upper()})"
            )
            if validation_result.dataset_name:
                st.caption(f"Dataset: {validation_result.dataset_name}")
        else:
            st.error(f"❌ {validation_result.error_message}")

    # 메트릭 선택 섹션
    st.divider()
    st.subheader("2. 메트릭 선택")

    # 카테고리별 그룹화
    categories = metric_selector.get_metrics_by_category()

    selected_metrics = []
    for category, metrics in categories.items():
        with st.expander(f"📁 {category.title()}", expanded=category == "generation"):
            cols = st.columns(2)
            for i, metric in enumerate(metrics):
                with cols[i % 2]:
                    icon = metric_selector.get_icon(metric)
                    desc = metric_selector.get_description(metric)
                    if st.checkbox(
                        f"{icon} {metric}",
                        value=metric in metric_selector.get_default_metrics(),
                        help=desc,
                        key=f"metric_{metric}",
                    ):
                        selected_metrics.append(metric)

    session.selected_metrics = selected_metrics

    # 선택된 메트릭 표시
    if selected_metrics:
        st.caption(f"Selected: {', '.join(selected_metrics)}")

    # 고급 옵션
    st.divider()
    with st.expander("⚙️ 고급 옵션"):
        col1, col2, col3 = st.columns(3)
        with col1:
            session.selected_model = st.selectbox(
                "모델",
                options=["gpt-5-nano", "gpt-4", "gpt-4o", "claude-3-5-sonnet"],
                index=0,
            )
        with col2:
            session.langfuse_enabled = st.checkbox("Langfuse 트래킹", value=False)
        with col3:
            session.parallel_processing = st.checkbox("병렬 처리", value=True)

        # 임계값 설정
        st.caption("메트릭 임계값 (Pass/Fail 기준)")
        threshold_cols = st.columns(len(selected_metrics) if selected_metrics else 1)
        for i, metric in enumerate(selected_metrics[:4]):  # 최대 4개만 표시
            with threshold_cols[i]:
                st.number_input(
                    metric,
                    min_value=0.0,
                    max_value=1.0,
                    value=0.7,
                    step=0.1,
                    key=f"threshold_{metric}",
                )

    # 실행 버튼
    st.divider()
    can_run = (
        validation_result is not None
        and validation_result.is_valid
        and len(selected_metrics) > 0
        and not session.is_evaluating
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🚀 평가 실행", type="primary", disabled=not can_run):
            st.info("평가 실행 기능은 아직 구현 중입니다.")
            # TODO: 실제 평가 실행 로직
    with col2:
        if session.is_evaluating:
            st.warning("실행 중...")

    # 상태 메시지
    if not uploaded_file:
        st.info("💡 먼저 데이터셋 파일을 업로드하세요.")
    elif not validation_result or not validation_result.is_valid:
        st.warning("⚠️ 유효한 데이터셋 파일을 업로드하세요.")
    elif not selected_metrics:
        st.warning("⚠️ 최소 하나의 메트릭을 선택하세요.")


def render_history_page(adapter, session):
    """이력 조회 페이지 렌더링."""
    import streamlit as st

    from evalvault.adapters.inbound.web.components import (
        HistoryExporter,
        RunFilter,
        RunSearch,
        RunTable,
    )

    st.header("📋 History")
    st.markdown("이전 평가 결과를 확인합니다.")

    # 데이터 로드
    all_runs = adapter.list_runs(limit=100)

    # 검색 및 필터 섹션
    search_col, filter_col = st.columns([2, 1])

    with search_col:
        search_query = st.text_input(
            "🔍 검색",
            placeholder="데이터셋 또는 모델 이름으로 검색...",
            key="history_search",
        )

    with filter_col, st.popover("🔧 필터"):
        # 모델 필터
        model_options = ["All"] + sorted({r.model_name for r in all_runs})
        selected_model = st.selectbox("모델", options=model_options, index=0)

        # 통과율 필터
        min_pass_rate = st.slider("최소 통과율", 0.0, 1.0, 0.0, 0.1)

        # 날짜 필터 (UI만, 추후 구현)
        st.checkbox("날짜 범위 필터", disabled=True, help="추후 구현 예정")

    # 검색 적용
    search = RunSearch(query=search_query)
    runs = search.search(all_runs)

    # 필터 적용
    run_filter = RunFilter(
        model_name=selected_model if selected_model != "All" else None,
        min_pass_rate=min_pass_rate if min_pass_rate > 0 else None,
    )
    runs = run_filter.apply(runs)

    # 결과 요약
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Runs", len(runs))
    with col2:
        avg_rate = sum(r.pass_rate for r in runs) / len(runs) if runs else 0
        st.metric("Avg Pass Rate", f"{avg_rate * 100:.1f}%")
    with col3:
        total_cases = sum(r.total_test_cases for r in runs)
        st.metric("Total Test Cases", f"{total_cases:,}")

    # 테이블 및 정렬
    st.divider()

    if runs:
        # 정렬 옵션
        sort_col, export_col = st.columns([3, 1])
        with sort_col:
            sort_by = st.selectbox(
                "정렬 기준",
                options=["date", "pass_rate", "dataset", "model"],
                format_func=lambda x: {
                    "date": "📅 날짜",
                    "pass_rate": "📊 통과율",
                    "dataset": "📁 데이터셋",
                    "model": "🤖 모델",
                }.get(x, x),
                index=0,
            )
        with export_col:
            exporter = HistoryExporter(runs=runs)
            st.download_button(
                "📥 CSV 다운로드",
                data=exporter.to_csv(),
                file_name="evaluation_history.csv",
                mime="text/csv",
            )

        # 테이블 생성
        table = RunTable(runs=runs, page_size=10)
        table.sort_by(sort_by, ascending=sort_by == "dataset")

        # 테이블 헤더
        cols = st.columns([3, 2, 2, 1, 1, 1])
        cols[0].markdown("**Dataset**")
        cols[1].markdown("**Model**")
        cols[2].markdown("**Metrics**")
        cols[3].markdown("**Pass Rate**")
        cols[4].markdown("**Date**")
        cols[5].markdown("**Actions**")

        for run in table.get_current_page_runs():
            cols = st.columns([3, 2, 2, 1, 1, 1])
            cols[0].text(run.dataset_name)
            cols[1].text(run.model_name)
            cols[2].text(
                ", ".join(run.metrics_evaluated[:2])
                + ("..." if len(run.metrics_evaluated) > 2 else "")
            )

            pass_rate_pct = run.pass_rate * 100
            if pass_rate_pct >= 70:
                cols[3].success(f"{pass_rate_pct:.0f}%")
            elif pass_rate_pct >= 50:
                cols[3].warning(f"{pass_rate_pct:.0f}%")
            else:
                cols[3].error(f"{pass_rate_pct:.0f}%")

            cols[4].text(run.started_at.strftime("%m/%d"))
            if cols[5].button("👁", key=f"view_{run.run_id}", help="상세 보기"):
                session.current_run_id = run.run_id

        # 페이지네이션
        if table.total_pages > 1:
            st.divider()
            page_cols = st.columns([1, 3, 1])
            with page_cols[1]:
                st.caption(f"Page {table.page} of {table.total_pages}")
    else:
        st.info("평가 이력이 없습니다.")


def render_reports_page(adapter, session):
    """보고서 페이지 렌더링."""
    import streamlit as st

    st.header("📄 Reports")
    st.markdown("평가 보고서를 생성하고 다운로드합니다.")

    # 평가 선택
    runs = adapter.list_runs(limit=20)
    if not runs:
        st.info("보고서를 생성할 평가 결과가 없습니다.")
        return

    run_options = {
        f"{r.dataset_name} ({r.started_at.strftime('%Y-%m-%d')})": r.run_id for r in runs
    }
    selected = st.selectbox("평가 선택", options=list(run_options.keys()))
    session.selected_report_run_id = run_options.get(selected)

    # 보고서 옵션
    st.subheader("보고서 옵션")
    col1, col2 = st.columns(2)
    with col1:
        session.report_format = st.radio("출력 형식", options=["Markdown", "HTML"], horizontal=True)
    with col2:
        session.include_nlp = st.checkbox("NLP 분석 포함", value=True)
        session.include_causal = st.checkbox("인과 분석 포함", value=True)

    # 생성 버튼
    st.divider()
    if st.button("📝 보고서 생성", type="primary"):
        st.info("보고서 생성 기능은 아직 구현 중입니다.")
        # TODO: 실제 보고서 생성 로직


def main():
    """Streamlit 앱 진입점."""
    create_app()


if __name__ == "__main__":
    main()
