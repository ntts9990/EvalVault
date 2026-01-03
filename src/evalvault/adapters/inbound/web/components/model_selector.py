"""Model selector component for per-feature LLM model selection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class ModelOption:
    """UI-friendly model option."""

    id: str  # e.g., "openai/gpt-5-nano"
    display_name: str  # e.g., "gpt-5-nano (OpenAI)"
    provider: str  # e.g., "openai"
    model_name: str  # e.g., "gpt-5-nano"

    @classmethod
    def from_profile(cls, profile_name: str, profile_data: dict) -> ModelOption | None:
        """Create ModelOption from a models.yaml profile entry."""
        llm_config = profile_data.get("llm", {})
        provider = llm_config.get("provider")
        model = llm_config.get("model")

        if not provider or not model:
            return None

        return cls(
            id=f"{provider}/{model}",
            display_name=f"{model} ({provider.title()})",
            provider=provider,
            model_name=model,
        )


def get_available_models() -> list[ModelOption]:
    """Get available models from config/models.yaml profiles.

    Returns:
        List of ModelOption objects
    """
    models: list[ModelOption] = []
    seen_ids: set[str] = set()

    # Load from config/models.yaml (project root)
    # __file__ is in src/evalvault/adapters/inbound/web/components/
    # Need to go up 7 levels to reach project root
    config_path = (
        Path(__file__).parent.parent.parent.parent.parent.parent.parent / "config" / "models.yaml"
    )

    if config_path.exists():
        try:
            import yaml

            with open(config_path) as f:
                config = yaml.safe_load(f)

            profiles = config.get("profiles", {})
            for profile_name, profile_data in profiles.items():
                option = ModelOption.from_profile(profile_name, profile_data)
                if option and option.id not in seen_ids:
                    models.append(option)
                    seen_ids.add(option.id)
        except Exception:
            pass

    # Add defaults if nothing loaded
    if not models:
        models = [
            ModelOption(
                id="openai/gpt-5-nano",
                display_name="gpt-5-nano (OpenAI)",
                provider="openai",
                model_name="gpt-5-nano",
            ),
            ModelOption(
                id="ollama/gemma3:1b",
                display_name="gemma3:1b (Ollama, dev)",
                provider="ollama",
                model_name="gemma3:1b",
            ),
        ]

    return models


def render_model_selector(
    st_module,
    key: str,
    *,
    label: str = "LLM Model",
    help_text: str | None = None,
    default_index: int = 0,
) -> ModelOption | None:
    """Render model selection dropdown.

    Args:
        st_module: Streamlit module (st)
        key: Unique key for the widget
        label: Label for the selectbox
        help_text: Optional help text
        default_index: Default selected index

    Returns:
        Selected ModelOption or None if no models available
    """
    models = get_available_models()

    if not models:
        st_module.warning("No LLM models available")
        return None

    options = [m.display_name for m in models]

    selected_display = st_module.selectbox(
        label,
        options=options,
        index=min(default_index, len(options) - 1),
        key=key,
        help=help_text or "Select the LLM model for this operation",
    )

    # Find the selected model
    for model in models:
        if model.display_name == selected_display:
            return model

    return models[0] if models else None


def get_model_by_id(model_id: str) -> ModelOption | None:
    """Get ModelOption by its ID.

    Args:
        model_id: Model ID in format "provider/model_name"

    Returns:
        ModelOption if found, None otherwise
    """
    models = get_available_models()
    for model in models:
        if model.id == model_id:
            return model
    return None
