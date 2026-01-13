import asyncio
import logging
from unittest.mock import MagicMock

from ragas import SingleTurnSample
from ragas.metrics import AnswerRelevancy, Faithfulness

from evalvault.adapters.outbound.llm import SettingsLLMFactory
from evalvault.adapters.outbound.nlp.korean.toolkit_factory import try_create_korean_toolkit
from evalvault.config.settings import Settings
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.ports.outbound.llm_port import LLMPort

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def debug_ragas():
    print("--- Starting Ragas Debug ---")

    # Mock LLM Port - needed for Ragas metric init (though we might hit init issues if it tries real validation)
    mock_llm = MagicMock(spec=LLMPort)
    mock_llm.get_model_name.return_value = "gpt-4o"
    # Mock as_ragas_llm to return something Ragas accepts - ideally a LangChain wrapper or Ragas LLM
    # But RagasEvaluator just passes it to metric init.
    # Let's see if we can just trigger the _score_single_sample logic.

    # We need to hack RagasEvaluator to use a real metric but potentially mock the internal LLM call of the metric
    # OR just see if the argument passing logic throws a TypeError before hitting the LLM.

    # Actually, Ragas metrics execute validation on `score` or `ascore`.
    # Failing at LLM call (e.g. no auth) is different from failing at argument passing.

    settings = Settings()
    llm_factory = SettingsLLMFactory(settings)
    korean_toolkit = try_create_korean_toolkit()
    evaluator = RagasEvaluator(korean_toolkit=korean_toolkit, llm_factory=llm_factory)

    # Create sample similar to what we observed
    sample = SingleTurnSample(
        user_input="암보험 가입 시 고지 의무는 무엇인가요?",
        response="계약 전 알릴 의무를 말하며, 과거 질병 이력 등을 사실대로 알려야 합니다.",
        retrieved_contexts=[
            "암보험 가입 시 계약자는 과거 병력, 직업 등 위험 측정에 필요한 사항을 사실대로 알려야 하는 고지 의무가 있습니다."
        ],
        reference="암보험 가입 시 계약자는 과거 병력, 직업 등 위험 측정에 필요한 사항을 사실대로 알려야 하는 고지 의무가 있습니다.",
    )

    # Initialize metrics manually to avoid real LLM requirement if possible,
    # but Ragas metrics NEED a working LLM for score().
    # If we don't have a working LLM, we definitely get 0.0 or error.
    # BUT the user environment HAS OpenAI set up (presumably).

    # Let's inspect the `_score_single_sample` logic by subclassing or monkeypatching
    # to print the exception.

    fake_metrics = [
        Faithfulness(llm=MagicMock()),
        AnswerRelevancy(llm=MagicMock(), embeddings=MagicMock()),
    ]

    print(f"Metric Names: {[m.name for m in fake_metrics]}")

    # We want to run _score_single_sample and CATCH the error that is currently being swallowed.

    try:
        scores = await evaluator._score_single_sample(sample, fake_metrics)
        print("Scores:", scores)
    except Exception as e:
        print(
            f"CRITICAL ERROR in top level catch (should not happen due to internal try/except): {e}"
        )

    # To see the swallowed error, we need to modify the RagasEvaluator code slightly to log it,
    # OR replicate the logic here.

    print("\n--- Replicating Logic to Capture Error ---")
    for metric in fake_metrics:
        print(f"Testing metric: {metric.name}")
        try:
            # Logic from RagasEvaluator._score_single_sample
            if hasattr(metric, "ascore"):
                print(f"{metric.name} HAS ascore")
                all_args = {
                    "user_input": sample.user_input,
                    "response": sample.response,
                    "retrieved_contexts": sample.retrieved_contexts,
                    "reference": sample.reference,
                }
                required_args = evaluator.METRIC_ARGS.get(
                    metric.name,
                    ["user_input", "response", "retrieved_contexts"],
                )
                kwargs = {k: v for k, v in all_args.items() if k in required_args and v is not None}
                print(f"Calling {metric.name}.ascore with kwargs keys: {list(kwargs.keys())}")
                result = await metric.ascore(**kwargs)
            elif hasattr(metric, "single_turn_ascore"):
                print(f"{metric.name} HAS single_turn_ascore")
                result = await metric.single_turn_ascore(sample)
            else:
                print(f"Metric {metric.name} has neither ascore nor single_turn_ascore")
                print(f"Dir: {dir(metric)}")
                continue

            print(f"Result for {metric.name}: {result}")
            if hasattr(result, "value"):
                print(f"Value: {result.value}")
            elif hasattr(result, "score"):
                print(f"Score: {result.score}")
            else:
                print(f"Raw: {result}")

        except Exception as e:
            print(f"CAUGHT EXCEPTION for {metric.name}: {type(e).__name__}: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_ragas())
