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

    st.header("📊 Evaluate")
    st.markdown("데이터셋을 업로드하고 RAG 평가를 실행합니다.")

    # 파일 업로드
    uploaded_file = st.file_uploader(
        "데이터셋 업로드",
        type=["csv", "json", "xlsx"],
        help="CSV, JSON, 또는 Excel 형식의 데이터셋을 업로드하세요.",
    )

    if uploaded_file:
        st.success(f"✅ {uploaded_file.name} 업로드됨")

    # 메트릭 선택
    st.subheader("메트릭 선택")
    available_metrics = adapter.get_available_metrics()
    descriptions = adapter.get_metric_descriptions()

    selected_metrics = []
    cols = st.columns(2)
    for i, metric in enumerate(available_metrics):
        with cols[i % 2]:
            if st.checkbox(
                f"{metric}",
                value=metric in ["faithfulness", "answer_relevancy"],
                help=descriptions.get(metric, ""),
            ):
                selected_metrics.append(metric)

    session.selected_metrics = selected_metrics

    # 고급 옵션
    with st.expander("고급 옵션"):
        col1, col2 = st.columns(2)
        with col1:
            session.langfuse_enabled = st.checkbox("Langfuse 트래킹 활성화", value=False)
        with col2:
            session.parallel_processing = st.checkbox("병렬 처리", value=True)

    # 실행 버튼
    st.divider()
    if st.button(
        "🚀 평가 실행", type="primary", disabled=not uploaded_file or not selected_metrics
    ):
        if session.is_evaluating:
            st.warning("평가가 이미 실행 중입니다.")
        else:
            st.info("평가 실행 기능은 아직 구현 중입니다.")
            # TODO: 실제 평가 실행 로직


def render_history_page(adapter, session):
    """이력 조회 페이지 렌더링."""
    import streamlit as st

    st.header("📋 History")
    st.markdown("이전 평가 결과를 확인합니다.")

    # 필터
    col1, col2, col3 = st.columns(3)
    with col1:
        session.filter_dataset = st.text_input("데이터셋 이름", placeholder="필터...")
    with col2:
        session.filter_model = st.selectbox(
            "모델", options=["All", "gpt-5-nano", "gpt-4", "gpt-4o"], index=0
        )
    with col3:
        session.filter_pass_rate = st.slider("최소 통과율", 0.0, 1.0, 0.0, 0.1)

    # 평가 목록
    st.divider()
    runs = adapter.list_runs(limit=50)

    if runs:
        # 테이블 헤더
        cols = st.columns([3, 2, 2, 1, 1, 1])
        cols[0].markdown("**Dataset**")
        cols[1].markdown("**Model**")
        cols[2].markdown("**Metrics**")
        cols[3].markdown("**Pass Rate**")
        cols[4].markdown("**Date**")
        cols[5].markdown("**Actions**")

        for run in runs:
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
