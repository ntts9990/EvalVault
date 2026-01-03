"""Streamlit helper for rendering prompt metadata with previews."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def render_prompt_panel(
    st, *, entries: list[dict[str, Any]], run_id: str, summary_label: str | None = None
) -> None:
    """Render prompt metadata entries with expandable previews."""

    if not entries:
        st.info("등록된 Prompt 메타데이터가 없습니다.")
        return

    if summary_label:
        st.caption(f"{summary_label} · Run {run_id[:8]}…")

    for entry in entries:
        raw_path = entry.get("path") or "prompt"
        short_path = Path(str(raw_path)).name or raw_path
        status = str(entry.get("status") or "unknown").lower()
        header = f"{short_path} — {status}"
        expanded = status not in {"synced", "unknown"}

        with st.expander(header, expanded=expanded):
            st.caption(str(raw_path))

            meta_lines: list[str] = []
            if entry.get("phoenix_prompt_id"):
                meta_lines.append(f"- **Prompt ID**: {entry['phoenix_prompt_id']}")
            if entry.get("phoenix_experiment_id"):
                meta_lines.append(f"- **Experiment ID**: {entry['phoenix_experiment_id']}")
            checksum = entry.get("current_checksum")
            if checksum:
                meta_lines.append(f"- **Checksum**: `{checksum}`")
            previous = entry.get("previous_checksum")
            if previous and previous != checksum:
                meta_lines.append(f"- **Previous**: `{previous}`")
            if entry.get("notes"):
                meta_lines.append(f"- **Notes**: {entry['notes']}")

            if meta_lines:
                st.markdown("\n".join(meta_lines))

            content_preview = entry.get("content_preview")
            if content_preview:
                st.markdown("**Prompt Preview**")
                st.code(content_preview, language="text")

            diff = entry.get("diff")
            if diff:
                st.markdown("**Diff**")
                st.code(diff, language="diff")
