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
    from evalvault.adapters.inbound.web.pages import (
        render_history_page,
        render_reports_page,
    )
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
            options=["🏠 Home", "📊 Evaluate", "📋 History", "🔧 Improve", "📄 Reports"],
            label_visibility="collapsed",
        )

        st.divider()

        # 설정 섹션
        with st.expander("⚙️ Settings", expanded=False):
            st.caption("Model Configuration")
            model = st.selectbox(
                "Default Model",
                options=[
                    "gpt-5-nano (OpenAI)",
                    "gemma3:1b (Ollama, dev)",
                    "gpt-oss-safeguard:20b (Ollama, prod)",
                ],
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
    elif page == "🔧 Improve":
        render_improvement_page(adapter, session)
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
        st.plotly_chart(pass_rate_fig, width="stretch", key="home_pass_rate_chart")

    with chart_col2:
        trend_fig = create_trend_chart(runs)
        st.plotly_chart(trend_fig, width="stretch", key="home_trend_chart")

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

    # 품질 게이트 및 개선 제안 섹션
    st.divider()
    st.subheader("품질 현황 및 개선 제안")

    if runs:
        # 가장 최근 실행의 품질 게이트 표시
        latest_run = runs[0]
        try:
            gate_report = adapter.check_quality_gate(latest_run.run_id)

            gate_col1, gate_col2 = st.columns([1, 2])

            with gate_col1:
                # 품질 게이트 상태
                if gate_report.overall_passed:
                    st.success("✅ 품질 게이트 PASS")
                else:
                    st.error("❌ 품질 게이트 FAIL")

                st.caption(f"최근 평가: {latest_run.run_id[:12]}...")

            with gate_col2:
                # 메트릭별 상태 (실패 메트릭 강조)
                failed_metrics = [r for r in gate_report.results if not r.passed]
                passed_metrics = [r for r in gate_report.results if r.passed]

                if failed_metrics:
                    st.markdown("**개선 필요 메트릭:**")
                    for result in failed_metrics[:3]:  # 상위 3개만
                        gap_pct = abs(result.gap) * 100
                        st.markdown(
                            f"- 🔴 **{result.metric}**: {result.score:.2f} / {result.threshold:.2f} "
                            f"(갭: -{gap_pct:.1f}%)"
                        )

                if passed_metrics:
                    with st.expander(f"✅ 통과 메트릭 ({len(passed_metrics)}개)"):
                        for result in passed_metrics:
                            st.markdown(
                                f"- {result.metric}: {result.score:.2f} / {result.threshold:.2f}"
                            )

            # 빠른 개선 제안 링크
            if failed_metrics:
                st.markdown("---")
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.info(
                        f"💡 {len(failed_metrics)}개 메트릭이 임계값 미달입니다. "
                        "개선 가이드를 확인하세요."
                    )
                with col2:
                    if st.button("🔧 개선 가이드", key="home_improve_btn"):
                        session.current_run_id = latest_run.run_id

        except Exception as e:
            st.warning(f"품질 게이트 정보를 가져오는 데 실패했습니다: {e}")
    else:
        st.info("아직 평가 결과가 없습니다.")

    # 최근 평가 목록
    st.divider()
    st.subheader("최근 평가")

    recent_list = RecentRunsList(runs=runs, max_items=5)

    if not recent_list.is_empty:
        for run in recent_list.displayed_runs:
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            with col1:
                emoji = recent_list.get_pass_rate_emoji(run.pass_rate)
                st.text(f"{emoji} {run.dataset_name}")
                extra_bits: list[str] = []
                if run.phoenix_precision is not None:
                    extra_bits.append(f"P@K {run.phoenix_precision:.2f}")
                if run.phoenix_drift is not None:
                    extra_bits.append(f"Drift {run.phoenix_drift:.2f}")
                if extra_bits:
                    st.caption(" | ".join(extra_bits))
                if run.phoenix_experiment_url:
                    st.caption(f"[Phoenix Experiment]({run.phoenix_experiment_url})")
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
            with col5:
                if st.button("🔧", key=f"improve_{run.run_id}", help="개선 가이드"):
                    session.current_run_id = run.run_id

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
    st.markdown(
        """
        <style>
        .mode-pill {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
            color: white;
        }
        .mode-pill.simple { background: #0ea5e9; }
        .mode-pill.full { background: #7c3aed; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("0. 실행 모드 선택")
    mode_label = st.radio(
        "모드",
        options=["Simple", "Full"],
        horizontal=True,
        index=0 if session.selected_run_mode == "simple" else 1,
        help="Simple은 기본 메트릭/트래커를 고정하고 Full은 모든 고급 옵션을 노출합니다.",
    )
    session.selected_run_mode = "simple" if mode_label == "Simple" else "full"
    simple_mode_active = session.selected_run_mode == "simple"
    pill_class = "simple" if simple_mode_active else "full"
    st.markdown(
        f"<span class='mode-pill {pill_class}'>Mode · {mode_label}</span>",
        unsafe_allow_html=True,
    )
    if simple_mode_active:
        st.info("심플 모드는 faithfulness/answer_relevancy + Phoenix tracker를 고정합니다.")
    else:
        st.caption(
            "전체 모드: Domain Memory·Prompt·Phoenix dataset/experiment 옵션을 사용할 수 있습니다."
        )

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
            # 임계값 정보 표시
            if validation_result.thresholds:
                threshold_str = ", ".join(
                    f"{k}: {v:.2f}" for k, v in validation_result.thresholds.items()
                )
                st.caption(f"📏 임계값: {threshold_str}")
            else:
                st.caption("📏 임계값: 기본값 0.7 적용 (JSON에 thresholds 미지정)")
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
                    default_selected = metric in metric_selector.get_default_metrics()
                    checkbox_disabled = simple_mode_active
                    checked = st.checkbox(
                        f"{icon} {metric}",
                        value=default_selected,
                        help=desc,
                        disabled=checkbox_disabled,
                        key=f"metric_{metric}",
                    )
                    if checked:
                        selected_metrics.append(metric)

    if simple_mode_active:
        selected_metrics = metric_selector.get_default_metrics()

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
                options=[
                    "gpt-5-nano (OpenAI)",
                    "gemma3:1b (Ollama, dev)",
                    "gpt-oss-safeguard:20b (Ollama, prod)",
                ],
                index=0,
            )
        with col2:
            session.langfuse_enabled = st.checkbox("Langfuse 트래킹", value=False)
        with col3:
            session.parallel_processing = st.checkbox("병렬 처리", value=True)

        # 임계값 안내 (데이터셋에서 로드됨)
        st.caption(
            "💡 메트릭 임계값은 데이터셋 JSON의 `thresholds`에서 로드됩니다. "
            "미지정 시 기본값 0.7 적용."
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
            # LLM 설정 확인
            if adapter._llm_adapter is None:
                st.error("LLM이 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
            else:
                try:
                    # 평가 시작 상태 설정
                    session.is_evaluating = True

                    # 파일 내용 읽기
                    file_content = uploaded_file.getvalue()

                    # st.status를 사용하여 진행 상태 표시
                    with st.status("🔄 평가 진행 중...", expanded=True) as status:
                        # Dataset 생성
                        status.write("📂 데이터셋 파싱 중...")
                        dataset = adapter.create_dataset_from_upload(
                            uploaded_file.name,
                            file_content,
                        )
                        status.write(f"✅ 데이터셋 로드 완료: {len(dataset.test_cases)}개 케이스")

                        # 데이터셋에서 Threshold 로드 (미지정 시 기본값 0.7)
                        thresholds = dataset.thresholds or {}
                        if thresholds:
                            status.write(f"📏 임계값 로드: {thresholds}")
                        else:
                            status.write("📏 임계값: 기본값 0.7 적용")

                        # 메트릭 정보 표시
                        status.write(f"📊 평가 메트릭: {', '.join(selected_metrics)}")
                        status.write("⏳ LLM API 호출 중... (1-2분 소요될 수 있습니다)")

                        # 평가 실행
                        import time

                        start_time = time.time()
                        parallel_mode = session.parallel_processing
                        mode_str = "병렬" if parallel_mode else "순차"
                        status.write(f"⚡ 실행 모드: {mode_str} 처리")

                        result = adapter.run_evaluation_with_dataset(
                            dataset=dataset,
                            metrics=selected_metrics,
                            thresholds=thresholds,
                            parallel=parallel_mode,
                            batch_size=5,
                            run_mode=session.selected_run_mode,
                        )
                        elapsed = time.time() - start_time

                        # 완료 상태로 업데이트
                        status.update(label="✅ 평가 완료!", state="complete", expanded=False)
                        status.write(f"⏱️ 소요 시간: {elapsed:.1f}초")

                    # 결과 표시
                    st.success(f"✅ 평가 완료! (Run ID: `{result.run_id}`)")

                    # 요약 메트릭
                    result_cols = st.columns(4)
                    with result_cols[0]:
                        st.metric("통과율", f"{result.pass_rate:.1%}")
                    with result_cols[1]:
                        st.metric("테스트 케이스", result.total_test_cases)
                    with result_cols[2]:
                        passed = result.passed_test_cases
                        st.metric("통과", f"{passed}/{result.total_test_cases}")
                    with result_cols[3]:
                        duration = result.duration_seconds or 0
                        st.metric("소요 시간", f"{duration:.1f}s")

                    # 메트릭별 점수
                    st.subheader("📊 메트릭별 결과")
                    metric_results = []
                    for metric in result.metrics_evaluated:
                        score = result.get_avg_score(metric)
                        threshold = thresholds.get(metric, 0.7)
                        passed = score >= threshold if score else False
                        metric_results.append(
                            {
                                "메트릭": metric,
                                "점수": f"{score:.3f}" if score else "N/A",
                                "임계값": f"{threshold:.2f}",
                                "결과": "✅ Pass" if passed else "❌ Fail",
                            }
                        )

                    st.dataframe(metric_results, width="stretch")

                    # 세션 상태 업데이트
                    session.current_run_id = result.run_id

                    # History 페이지 이동 안내
                    st.info(
                        f"📋 History 페이지에서 상세 결과를 확인할 수 있습니다. "
                        f"(Mode: {session.selected_run_mode.capitalize()})"
                    )

                except Exception as e:
                    st.error(f"❌ 평가 실패: {e}")
                    import traceback

                    st.code(traceback.format_exc())
                finally:
                    session.is_evaluating = False

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
    elif adapter._llm_adapter is None:
        st.warning("⚠️ LLM이 설정되지 않았습니다. .env에 OPENAI_API_KEY를 설정하세요.")


def render_improvement_page(adapter, session):
    """개선 가이드 페이지 렌더링."""
    import streamlit as st

    from evalvault.adapters.inbound.web.components import RunSelector, render_model_selector

    # LLM 분석 다이얼로그
    @st.dialog("🔧 LLM 개선 가이드 생성", width="large")
    def llm_improvement_dialog(run_id: str, run_name: str):
        """LLM 개선 가이드 생성 모달."""
        st.markdown(f"**대상 평가:** {run_name}")
        st.divider()

        # 모델 선택
        st.subheader("분석 모델 선택")
        selected_model = render_model_selector(
            st,
            key="dialog_improve_model",
            label="LLM 모델",
            help_text="개선 가이드 생성에 사용할 LLM 모델을 선택하세요.",
        )

        col1, col2 = st.columns([3, 1])
        with col1:
            generate_clicked = st.button(
                "🚀 분석 시작",
                type="primary",
                use_container_width=True,
            )
        with col2:
            if st.button("취소", use_container_width=True):
                st.rerun()

        if generate_clicked:
            model_id = selected_model.id if selected_model else None
            model_name = selected_model.display_name if selected_model else "기본 모델"

            with st.status("🔧 LLM 개선 가이드 생성 중...", expanded=True) as status:
                try:
                    status.write(f"📊 모델: **{model_name}**")
                    status.write("🧠 LLM 분석 시작...")
                    status.write("⏳ 약 1-2분 소요될 수 있습니다...")

                    # LLM 개선 가이드 생성
                    report = adapter.get_improvement_guide(
                        run_id,
                        include_llm=True,
                        model_id=model_id,
                    )

                    status.update(
                        label="✅ LLM 개선 가이드 생성 완료!",
                        state="complete",
                        expanded=False,
                    )

                    # 세션에 저장
                    session.improvement_report = report
                    st.session_state.last_improve_options = {
                        "run_id": run_id,
                        "include_llm": True,
                        "model_id": model_id,
                    }

                    st.success("✅ 개선 가이드 생성 완료!")
                    st.info("다이얼로그를 닫으면 결과를 확인할 수 있습니다.")

                    if st.button("📄 결과 확인", type="primary", use_container_width=True):
                        st.rerun()

                except Exception as e:  # noqa: BLE001
                    status.update(label="❌ 생성 실패", state="error")
                    st.error(f"❌ 개선 가이드 생성 실패: {e}")
                    import traceback

                    with st.expander("오류 상세"):
                        st.code(traceback.format_exc())

    st.header("🔧 개선 가이드")
    st.markdown("평가 결과를 분석하여 RAG 시스템 개선 방안을 제안합니다.")

    # 평가 결과 조회
    runs = adapter.list_runs(limit=50)

    if not runs:
        st.info("분석할 평가 결과가 없습니다. 먼저 평가를 실행해주세요.")
        return

    # 실행 선택 섹션
    st.subheader("1. 평가 선택")
    selector = RunSelector(runs=runs)
    options = selector.get_options()

    selected_option = st.selectbox(
        "분석할 평가 실행 선택",
        options=options,
        format_func=lambda x: x,
        help="개선 가이드를 생성할 평가 실행을 선택하세요.",
    )

    # 선택된 실행 ID 추출
    selected_run_id = selected_option.split(" | ")[0] if selected_option else None
    selected_run = selector.get_by_id(selected_run_id) if selected_run_id else None

    if not selected_run:
        return

    # 선택된 평가 정보 및 품질 게이트
    st.divider()
    st.subheader("2. 품질 현황")

    # 품질 게이트 체크
    try:
        gate_report = adapter.check_quality_gate(selected_run_id)

        # 전체 상태 표시
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("전체 통과율", f"{selected_run.pass_rate:.1%}")
        with col2:
            if gate_report.overall_passed:
                st.success("✅ 품질 게이트 PASS")
            else:
                st.error("❌ 품질 게이트 FAIL")
        with col3:
            st.metric("테스트 케이스", selected_run.total_test_cases)

        # 메트릭별 현황
        st.markdown("**메트릭별 현황**")
        for result in gate_report.results:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                # 프로그레스 바
                st.progress(result.score, text=result.metric)
            with col2:
                st.text(f"{result.score:.2f}")
            with col3:
                st.text(f"/ {result.threshold:.2f}")
            with col4:
                if result.passed:
                    st.success("✅")
                else:
                    st.error("❌")

    except Exception as e:
        st.warning(f"품질 게이트 정보를 가져오는 데 실패했습니다: {e}")

    # 개선 가이드 생성 옵션
    st.divider()
    st.subheader("3. 개선 가이드 생성")

    analysis_type = st.radio(
        "분석 유형",
        options=["llm_analysis", "basic"],
        format_func=lambda x: {
            "llm_analysis": "🤖 LLM 분석 (권장) - AI 기반 심층 분석",
            "basic": "📝 기본 분석 - 규칙 기반 패턴 분석",
        }.get(x, x),
        horizontal=False,
        help="LLM 분석은 더 상세한 개선 제안을 제공합니다.",
    )

    # LLM 분석 선택 시
    if analysis_type == "llm_analysis":
        st.info(
            "💡 **LLM 분석**은 AI를 활용하여 실패 원인을 심층 분석하고 "
            "구체적인 개선 방안을 제안합니다. (LLM API 호출로 인해 1-2분 소요될 수 있습니다)"
        )

        if adapter._llm_adapter is None:
            st.error("LLM이 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        elif selected_run is None:
            st.warning("먼저 평가를 선택해주세요.")
        else:
            if st.button(
                "🤖 LLM 분석 시작",
                type="primary",
                help="클릭하면 모달 창에서 분석을 수행합니다.",
            ):
                llm_improvement_dialog(
                    selected_run.run_id,
                    f"{selected_run.dataset_name} ({selected_run.run_id[:8]}...)",
                )

    # 기본 분석 선택 시
    else:
        if st.button("🔍 기본 분석 시작", type="primary"):
            with st.spinner("개선 가이드 생성 중..."):
                try:
                    report = adapter.get_improvement_guide(
                        selected_run_id,
                        include_llm=False,
                        model_id=None,
                    )

                    # 세션에 저장
                    session.improvement_report = report
                    st.session_state.last_improve_options = {
                        "run_id": selected_run_id,
                        "include_llm": False,
                        "model_id": None,
                    }
                    st.success("✅ 기본 분석 완료!")

                except Exception as e:
                    st.error(f"개선 가이드 생성 실패: {e}")
                    return

    # 옵션 변경 시 이전 결과 무효화
    if "last_improve_options" not in st.session_state:
        st.session_state.last_improve_options = {
            "run_id": None,
            "include_llm": False,
            "model_id": None,
        }

    options_changed = st.session_state.last_improve_options["run_id"] != selected_run_id

    if options_changed and hasattr(session, "improvement_report") and session.improvement_report:
        # 평가가 변경되면 이전 결과 무효화
        session.improvement_report = None

    # 개선 가이드 표시
    if hasattr(session, "improvement_report") and session.improvement_report:
        report = session.improvement_report

        st.divider()
        st.subheader("4. 개선 가이드")

        # 요약
        st.markdown(
            f"""
        **분석 요약**
        - 분석 대상: {report.run_id}
        - 테스트 케이스: {report.total_test_cases}개
        - 실패 케이스: {report.failed_test_cases}개
        - 통과율: {report.pass_rate:.1%}
        """
        )

        # 가이드 목록
        if report.guides:
            for i, guide in enumerate(report.guides, 1):
                priority_colors = {
                    "P0_CRITICAL": "🔴",
                    "P1_HIGH": "🟠",
                    "P2_MEDIUM": "🟡",
                    "P3_LOW": "🟢",
                }
                priority_icon = priority_colors.get(guide.priority.name, "⚪")

                with st.expander(
                    f"{priority_icon} {i}. {guide.component.value.title()} 개선 "
                    f"(예상 +{guide.total_expected_improvement:.0%})",
                    expanded=i == 1,
                ):
                    # 대상 메트릭
                    st.markdown(f"**대상 메트릭**: {', '.join(guide.target_metrics)}")

                    # 증거 데이터
                    if guide.evidence:
                        st.markdown("**증거 데이터**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("실패 케이스", guide.evidence.total_failures)
                        with col2:
                            if guide.evidence.avg_score_failures:
                                st.metric(
                                    "실패 평균 점수",
                                    f"{guide.evidence.avg_score_failures:.2f}",
                                )
                        with col3:
                            if guide.evidence.avg_score_passes:
                                st.metric(
                                    "통과 평균 점수",
                                    f"{guide.evidence.avg_score_passes:.2f}",
                                )

                    # 개선 액션
                    st.markdown("**권장 액션**")
                    for j, action in enumerate(guide.actions, 1):
                        effort_icons = {"low": "🟢", "medium": "🟡", "high": "🔴"}
                        effort_icon = effort_icons.get(action.effort.value, "⚪")

                        st.markdown(
                            f"{j}. **{action.title}** {effort_icon} "
                            f"(예상 +{action.expected_improvement:.0%})"
                        )
                        st.caption(action.description)

                        if action.implementation_hint:
                            st.code(action.implementation_hint, language="python")

                    # 검증 방법
                    if guide.verification_command:
                        st.markdown("**검증 방법**")
                        st.code(guide.verification_command, language="bash")
        else:
            st.info("탐지된 개선 패턴이 없습니다. 현재 시스템이 양호한 상태입니다.")

        # 마크다운 다운로드
        st.divider()
        if hasattr(report, "to_markdown"):
            st.download_button(
                "📥 마크다운 다운로드",
                data=report.to_markdown(),
                file_name=f"improvement_guide_{report.run_id}.md",
                mime="text/markdown",
            )


def main():
    """Streamlit 앱 진입점."""
    create_app()


if __name__ == "__main__":
    main()
