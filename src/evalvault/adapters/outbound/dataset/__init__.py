"""Dataset loaders for various file formats."""

from evalvault.adapters.outbound.dataset.base import BaseDatasetLoader
from evalvault.adapters.outbound.dataset.csv_loader import CSVDatasetLoader
from evalvault.adapters.outbound.dataset.excel_loader import ExcelDatasetLoader
from evalvault.adapters.outbound.dataset.json_loader import JSONDatasetLoader
from evalvault.adapters.outbound.dataset.loader_factory import get_loader, register_loader
from evalvault.adapters.outbound.dataset.method_input_loader import MethodInputDatasetLoader
from evalvault.adapters.outbound.dataset.multiturn_json_loader import (
    MultiTurnDataset,
    load_multiturn_dataset,
)
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

__all__ = [
    "BaseDatasetLoader",
    "CSVDatasetLoader",
    "ExcelDatasetLoader",
    "JSONDatasetLoader",
    "MethodInputDatasetLoader",
    "MultiTurnDataset",
    "StreamingCSVLoader",
    "StreamingConfig",
    "StreamingDatasetLoader",
    "StreamingJSONLoader",
    "StreamingStats",
    "StreamingTestCaseIterator",
    "get_loader",
    "load_in_chunks",
    "load_multiturn_dataset",
    "register_loader",
    "stream_file",
]
