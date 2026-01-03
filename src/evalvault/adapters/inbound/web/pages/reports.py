"""Reports page renderer for the EvalVault Streamlit app."""

from __future__ import annotations


def render_reports_page(adapter, session):
    """보고서 페이지 렌더링."""
    import streamlit as st

    from evalvault.adapters.inbound.web.components import (
        ReportConfig,
        ReportDownloader,
        ReportGenerator,
        ReportPreview,
        ReportTemplate,
        RunSelector,
        render_model_selector,
    )
    from evalvault.adapters.inbound.web.components.prompt_panel import render_prompt_panel
    from evalvault.domain.services.prompt_status import format_prompt_summary_label

    # AI 보고서 생성 다이얼로그
    @st.dialog("🤖 AI 분석 보고서 생성", width="large")
    def ai_report_dialog(run_id: str, run_name: str):
        """AI 분석 보고서 생성 모달."""
        st.markdown(f"**대상 평가:** {run_name}")
        st.divider()

        # 모델 선택
        st.subheader("분석 모델 선택")
        selected_model = render_model_selector(
            st,
            key="dialog_ai_report_model",
            label="LLM 모델",
            help_text="AI 분석 보고서 생성에 사용할 LLM 모델을 선택하세요.",
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

            with st.status("🤖 AI 분석 보고서 생성 중...", expanded=True) as status:
                try:
                    status.write(f"📊 모델: **{model_name}**")
                    status.write("🧠 LLM 분석 시작 (각 메트릭별 전문가 분석)...")
                    status.write("⏳ 약 2-3분 소요될 수 있습니다...")

                    # LLM 보고서 생성
                    llm_report = adapter.generate_llm_report(
                        run_id,
                        model_id=model_id,
                    )

                    status.update(
                        label="✅ AI 분석 보고서 생성 완료!",
                        state="complete",
                        expanded=False,
                    )

                    # 세션에 저장
                    session.llm_report = llm_report

                    st.success("✅ 보고서 생성 완료!")
                    st.info("다이얼로그를 닫으면 보고서를 확인할 수 있습니다.")

                    if st.button("📄 보고서 확인", type="primary", use_container_width=True):
                        st.rerun()

                except Exception as e:  # noqa: BLE001
                    status.update(label="❌ 생성 실패", state="error")
                    st.error(f"❌ 보고서 생성 실패: {e}")
                    import traceback

                    with st.expander("오류 상세"):
                        st.code(traceback.format_exc())

    st.header("📄 Reports")
    st.markdown("평가 보고서를 생성하고 다운로드합니다.")

    # 평가 선택
    runs = adapter.list_runs(limit=50)
    if not runs:
        st.info("보고서를 생성할 평가 결과가 없습니다.")
        return

    # 실행 선택 섹션
    st.subheader("1. 평가 선택")
    selector = RunSelector(runs=runs)
    options = selector.get_options()

    selected_option = st.selectbox(
        "평가 실행 선택",
        options=options,
        format_func=lambda x: x,
        help="보고서를 생성할 평가 실행을 선택하세요.",
    )

    # 선택된 실행 ID 추출
    selected_run_id = selected_option.split(" | ")[0] if selected_option else None
    selected_run = selector.get_by_id(selected_run_id) if selected_run_id else None

    if selected_run:
        # 선택된 평가 정보 표시
        info_col1, info_col2, info_col3, info_col4 = st.columns(4)
        with info_col1:
            st.metric("Dataset", selected_run.dataset_name)
        with info_col2:
            st.metric("Model", selected_run.model_name)
        with info_col3:
            st.metric("Pass Rate", f"{selected_run.pass_rate:.1%}")
        with info_col4:
            st.metric("Test Cases", selected_run.total_test_cases)
        phoenix_bits = []
        if selected_run.phoenix_precision is not None:
            phoenix_bits.append(f"P@K {selected_run.phoenix_precision:.2f}")
        if selected_run.phoenix_drift is not None:
            phoenix_bits.append(f"Drift {selected_run.phoenix_drift:.2f}")
        if phoenix_bits:
            st.caption("Phoenix: " + " | ".join(phoenix_bits))
        if selected_run.phoenix_experiment_url:
            st.caption(f"[Phoenix Experiment]({selected_run.phoenix_experiment_url})")
        prompt_entries = list(selected_run.phoenix_prompts or [])
        prompt_summary = format_prompt_summary_label(prompt_entries)
        with st.expander("Prompt 상태", expanded=False):
            render_prompt_panel(
                st,
                entries=prompt_entries,
                run_id=selected_run.run_id,
                summary_label=prompt_summary,
            )

    # 보고서 유형 선택
    st.divider()
    st.subheader("2. 보고서 유형 선택")

    report_type = st.radio(
        "보고서 유형",
        options=["ai_analysis", "basic"],
        format_func=lambda x: {
            "ai_analysis": "🤖 AI 분석 보고서 (권장) - LLM 기반 전문가 수준 분석",
            "basic": "📝 기본 보고서 - 템플릿 기반 요약",
        }.get(x, x),
        horizontal=False,
        help="AI 분석 보고서는 LLM을 사용하여 전문가 수준의 심층 분석을 제공합니다.",
    )

    # AI 분석 보고서
    if report_type == "ai_analysis":
        st.info(
            "💡 **AI 분석 보고서**는 각 메트릭에 대해 전문가 관점의 분석, "
            "최신 RAG 연구 기반 권장사항, 구체적인 액션 아이템을 제공합니다. "
            "(LLM API 호출로 인해 2-3분 소요될 수 있습니다)"
        )

        # 보고서 생성 버튼 - 다이얼로그 열기
        st.divider()
        st.subheader("3. AI 분석 보고서 생성")

        if adapter._llm_adapter is None:
            st.error("LLM이 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        elif selected_run is None:
            st.warning("먼저 평가를 선택해주세요.")
        else:
            if st.button(
                "🤖 AI 분석 보고서 생성",
                type="primary",
                help="클릭하면 모달 창에서 보고서를 생성합니다.",
            ):
                ai_report_dialog(
                    selected_run.run_id,
                    f"{selected_run.dataset_name} ({selected_run.run_id[:8]}...)",
                )

        # LLM 보고서 미리보기
        if hasattr(session, "llm_report") and session.llm_report:
            llm_report = session.llm_report

            st.divider()
            st.subheader("4. AI 분석 보고서 미리보기")

            # 보고서 내용 마크다운으로 표시
            report_content = llm_report.to_markdown()

            stat_col1, stat_col2 = st.columns(2)
            with stat_col1:
                st.caption(f"📄 {len(report_content):,} 문자")
            with stat_col2:
                st.caption(f"📊 {len(llm_report.metric_analyses)}개 메트릭 분석 포함")

            with st.expander("📖 보고서 전체 보기", expanded=True):
                st.markdown(report_content)

            # 다운로드 버튼
            st.divider()
            col1, col2 = st.columns([3, 1])
            with col1:
                st.download_button(
                    label="📥 마크다운 다운로드",
                    data=report_content,
                    file_name=f"ai_report_{llm_report.run_id}.md",
                    mime="text/markdown",
                    type="primary",
                    use_container_width=True,
                )
            with col2:
                if st.button("🗑️ 보고서 삭제", use_container_width=True):
                    session.llm_report = None
                    st.rerun()

    # 기본 보고서
    else:
        col1, col2 = st.columns(2)

        with col1:
            # 템플릿 선택
            templates = ReportTemplate.list_templates()
            template_descriptions = {t: ReportTemplate.get_description(t) for t in templates}

            selected_template = st.selectbox(
                "템플릿",
                options=templates,
                format_func=lambda x: f"{x.title()} - {template_descriptions.get(x, '')}",
            )

            # 출력 형식
            output_format = st.radio(
                "출력 형식",
                options=["markdown", "html"],
                format_func=lambda x: {
                    "markdown": "📝 Markdown",
                    "html": "🌐 HTML",
                }.get(x, x),
                horizontal=True,
            )

        with col2:
            # 포함 옵션
            st.caption("포함 항목")
            include_summary = st.checkbox("요약", value=True)
            include_metrics_detail = st.checkbox("메트릭 상세", value=True)

        # 보고서 생성 섹션
        st.divider()
        st.subheader("3. 기본 보고서 생성")

        # 설정 생성
        config = ReportConfig(
            output_format=output_format,
            include_summary=include_summary,
            include_metrics_detail=include_metrics_detail,
            include_charts=False,
            include_nlp_analysis=False,
            include_causal_analysis=False,
            template_name=selected_template,
        )

        generate_clicked = st.button(
            "📝 기본 보고서 생성",
            type="primary",
            disabled=selected_run is None,
        )

        # 보고서 생성 및 미리보기
        if generate_clicked and selected_run:
            with st.spinner("보고서 생성 중..."):
                # 실제 메트릭 점수 조회
                try:
                    run_details = adapter.get_run_details(selected_run.run_id)
                    metrics = {
                        m: run_details.get_avg_score(m) or 0.0
                        for m in run_details.metrics_evaluated
                    }
                except Exception as e:  # noqa: BLE001
                    st.warning(f"메트릭 점수 조회 실패: {e}. 기본값 사용.")
                    metrics = dict.fromkeys(selected_run.metrics_evaluated, 0.0)

                # 보고서 생성
                generator = ReportGenerator(config=config)
                report_result = generator.generate(run=selected_run, metrics=metrics)

                # 세션에 저장
                session.generated_report = report_result

            st.success("✅ 보고서 생성 완료!")

        # 미리보기 및 다운로드
        if hasattr(session, "generated_report") and session.generated_report:
            report_result = session.generated_report

            st.divider()
            st.subheader("4. 보고서 미리보기")

            # 통계 표시
            preview = ReportPreview(result=report_result)
            stats = preview.get_stats()

            stat_col1, stat_col2, stat_col3 = st.columns(3)
            with stat_col1:
                st.caption(f"📄 {stats['char_count']:,} 문자")
            with stat_col2:
                st.caption(f"📝 {stats['line_count']} 줄")
            with stat_col3:
                st.caption(f"📊 형식: {report_result.format.upper()}")

            # 미리보기 내용
            with st.expander("📖 미리보기", expanded=True):
                if report_result.format == "html":
                    st.components.v1.html(report_result.content, height=500, scrolling=True)
                else:
                    st.markdown(preview.get_preview())

            # 다운로드 버튼
            st.divider()
            downloader = ReportDownloader(result=report_result)
            download_data = downloader.prepare_download()

            st.download_button(
                label=f"📥 {report_result.format.upper()} 다운로드",
                data=download_data["data"],
                file_name=download_data["filename"],
                mime=download_data["mime_type"],
                type="primary",
            )
