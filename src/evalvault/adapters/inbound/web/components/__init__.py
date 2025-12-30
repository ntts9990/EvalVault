"""Web UI components package."""

from evalvault.adapters.inbound.web.components.cards import MetricSummaryCard, StatCard
from evalvault.adapters.inbound.web.components.charts import (
    create_metric_breakdown_chart,
    create_pass_rate_chart,
    create_trend_chart,
)
from evalvault.adapters.inbound.web.components.evaluate import (
    EvaluationConfig,
    EvaluationResult,
)
from evalvault.adapters.inbound.web.components.lists import RecentRunsList
from evalvault.adapters.inbound.web.components.metrics import MetricSelector
from evalvault.adapters.inbound.web.components.progress import (
    EvaluationProgress,
    ProgressStep,
)
from evalvault.adapters.inbound.web.components.stats import DashboardStats
from evalvault.adapters.inbound.web.components.upload import (
    FileUploadHandler,
    ValidationResult,
)

__all__ = [
    # Cards
    "MetricSummaryCard",
    "StatCard",
    # Charts
    "create_pass_rate_chart",
    "create_metric_breakdown_chart",
    "create_trend_chart",
    # Lists
    "RecentRunsList",
    # Stats
    "DashboardStats",
    # Upload
    "FileUploadHandler",
    "ValidationResult",
    # Metrics
    "MetricSelector",
    # Progress
    "EvaluationProgress",
    "ProgressStep",
    # Evaluate
    "EvaluationConfig",
    "EvaluationResult",
]
