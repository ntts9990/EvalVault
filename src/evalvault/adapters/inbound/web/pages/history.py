"""History page renderer for the EvalVault Streamlit app."""

from __future__ import annotations


def render_history_page(adapter, session):
    """이력 조회 페이지 렌더링."""
    import streamlit as st

    from evalvault.adapters.inbound.web.components import (
        HistoryExporter,
        RunFilter,
        RunSearch,
        RunTable,
    )
    from evalvault.adapters.inbound.web.components.prompt_panel import render_prompt_panel
    from evalvault.domain.services.prompt_status import format_prompt_summary_label

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

        mode_values = sorted({r.run_mode for r in all_runs if r.run_mode})
        mode_options = ["All"] + mode_values
        selected_mode = st.selectbox(
            "실행 모드",
            options=mode_options,
            format_func=lambda x: "전체" if x == "All" else x.capitalize(),
            index=0,
        )

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
        run_mode=selected_mode if selected_mode != "All" else None,
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

        show_phoenix_column = any(
            r.phoenix_precision is not None or r.phoenix_drift is not None for r in runs
        )
        column_config = [3, 1, 2, 2, 1, 1]
        if show_phoenix_column:
            column_config.append(1)
        column_config.append(1)

        header_labels = ["Dataset", "Mode", "Model", "Metrics", "Pass Rate", "Date"]
        if show_phoenix_column:
            header_labels.append("Phoenix")
        header_labels.append("Actions")

        header_cols = st.columns(column_config)
        for col, label in zip(header_cols, header_labels, strict=True):
            col.markdown(f"**{label}**")

        for run in table.get_current_page_runs():
            row_cols = st.columns(column_config)
            idx = 0
            dataset_col = row_cols[idx]
            dataset_col.text(run.dataset_name)
            prompt_summary = format_prompt_summary_label(run.phoenix_prompts)
            if prompt_summary:
                dataset_col.caption(f"Prompt: {prompt_summary}")
            idx += 1
            row_cols[idx].text((run.run_mode or "-").capitalize())
            idx += 1
            row_cols[idx].text(run.model_name)
            idx += 1
            row_cols[idx].text(
                ", ".join(run.metrics_evaluated[:2])
                + ("..." if len(run.metrics_evaluated) > 2 else "")
            )
            idx += 1

            pass_rate_pct = run.pass_rate * 100
            if pass_rate_pct >= 70:
                row_cols[idx].success(f"{pass_rate_pct:.0f}%")
            elif pass_rate_pct >= 50:
                row_cols[idx].warning(f"{pass_rate_pct:.0f}%")
            else:
                row_cols[idx].error(f"{pass_rate_pct:.0f}%")
            idx += 1

            row_cols[idx].text(run.started_at.strftime("%m/%d"))
            idx += 1

            if show_phoenix_column:
                phoenix_bits: list[str] = []
                if run.phoenix_precision is not None:
                    phoenix_bits.append(f"P@K {run.phoenix_precision:.2f}")
                if run.phoenix_drift is not None:
                    phoenix_bits.append(f"Drift {run.phoenix_drift:.2f}")
                if run.phoenix_experiment_url:
                    phoenix_bits.append(f"[Open]({run.phoenix_experiment_url})")
                if phoenix_bits:
                    row_cols[idx].markdown(" | ".join(phoenix_bits))
                else:
                    row_cols[idx].text("-")
                idx += 1

            if row_cols[-1].button("👁", key=f"view_{run.run_id}", help="상세 보기"):
                session.current_run_id = run.run_id

        # 페이지네이션
        if table.total_pages > 1:
            st.divider()
            page_cols = st.columns([1, 3, 1])
            with page_cols[1]:
                st.caption(f"Page {table.page} of {table.total_pages}")

        selected_run = None
        if session.current_run_id:
            selected_run = next((r for r in runs if r.run_id == session.current_run_id), None)
        if selected_run is None and runs:
            selected_run = runs[0]
        if selected_run:
            st.divider()
            st.subheader("Prompt 상태")
            entries = list(selected_run.phoenix_prompts or [])
            summary = format_prompt_summary_label(entries)
            render_prompt_panel(
                st,
                entries=entries,
                run_id=selected_run.run_id,
                summary_label=summary,
            )
    else:
        st.info("평가 이력이 없습니다.")
