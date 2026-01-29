from __future__ import annotations

from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from evalvault.adapters.outbound.storage.factory import build_storage_adapter
from evalvault.config.settings import Settings
from evalvault.domain.services.satisfaction_calibration_service import (
    SatisfactionCalibrationService,
)

from ..utils.options import db_option

_console = Console()


def register_calibrate_commands(app: typer.Typer, console: Console) -> None:
    global _console
    _console = console

    @app.command()
    def calibrate(
        run_id: str = typer.Argument(..., help="보정 대상 Run ID"),
        model: str = typer.Option(
            "both", "--model", help="모델 선택 (linear|xgb|both)", show_default=True
        ),
        write_back: bool = typer.Option(
            False,
            "--write-back",
            help="보정 결과를 메타데이터에 저장",
            show_default=True,
        ),
        db_path: Path | None = db_option(help_text="DB 경로"),
    ) -> None:
        storage = build_storage_adapter(settings=Settings(), db_path=db_path)
        try:
            run = storage.get_run(run_id)
        except KeyError:
            _console.print("[red]오류: Run을 찾을 수 없습니다.[/red]")
            raise typer.Exit(1)

        normalized_model = model.lower()
        if normalized_model not in {"linear", "xgb", "both"}:
            _console.print("[red]오류: model은 linear|xgb|both 중 하나여야 합니다.[/red]")
            raise typer.Exit(1)

        feedbacks = storage.list_feedback(run_id)
        service = SatisfactionCalibrationService()
        calibration = service.build_calibration(run, feedbacks, model=normalized_model)

        table = Table(title="보정 모델 성능 요약")
        table.add_column("모델")
        table.add_column("MAE", justify="right")
        table.add_column("Pearson", justify="right")
        table.add_column("Spearman", justify="right")

        if calibration.summary.model_metrics:
            for model_name, metrics in calibration.summary.model_metrics.items():
                table.add_row(
                    model_name,
                    _format_metric(metrics.get("mae")),
                    _format_metric(metrics.get("pearson")),
                    _format_metric(metrics.get("spearman")),
                )
        else:
            table.add_row("N/A", "-", "-", "-")

        _console.print(table)
        _console.print(
            f"평균 만족도: {calibration.summary.avg_satisfaction_score} | "
            f"Thumb Up 비율: {calibration.summary.thumb_up_rate} | "
            f"보정 비율: {calibration.summary.imputed_ratio}"
        )

        if write_back:
            metadata = run.tracker_metadata or {}
            metadata["calibration"] = {
                "updated_at": datetime.now().isoformat(),
                "model": model,
                "summary": {
                    "avg_satisfaction_score": calibration.summary.avg_satisfaction_score,
                    "thumb_up_rate": calibration.summary.thumb_up_rate,
                    "imputed_ratio": calibration.summary.imputed_ratio,
                    "model_metrics": calibration.summary.model_metrics,
                },
                "cases": {
                    case_id: {
                        "calibrated_satisfaction": case.calibrated_satisfaction,
                        "imputed": case.imputed,
                        "imputation_source": case.imputation_source,
                    }
                    for case_id, case in calibration.cases.items()
                },
            }
            storage.update_run_metadata(run_id, metadata)
            _console.print("[green]보정 결과를 메타데이터에 저장했습니다.[/green]")


def _format_metric(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.3f}"
