import asyncio
import logging

from evalvault.adapters.outbound.llm import SettingsLLMFactory
from evalvault.adapters.outbound.llm.openai_adapter import OpenAIAdapter
from evalvault.adapters.outbound.nlp.korean.toolkit_factory import try_create_korean_toolkit
from evalvault.config.settings import get_settings
from evalvault.domain.entities.dataset import Dataset, TestCase
from evalvault.domain.services.evaluator import RagasEvaluator

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def debug_ragas_real():
    print("--- Starting Real Ragas Debug ---")

    settings = get_settings()
    # Ensure we use OpenAI
    settings.llm_provider = "openai"
    settings.openai_model = "gpt-4o"  # Force override to bypass .env
    # Assuming ENV vars are set for OpenAI API key. If not, this might fail on auth, which is a good test.
    # Assuming ENV vars are set for OpenAI API key. If not, this might fail on auth, which is a good test.

    print(f"Using Provider: {settings.llm_provider}")
    print(f"Using Model: {settings.openai_model}")

    llm = OpenAIAdapter(settings)
    llm_factory = SettingsLLMFactory(settings)
    korean_toolkit = try_create_korean_toolkit()
    evaluator = RagasEvaluator(korean_toolkit=korean_toolkit, llm_factory=llm_factory)

    # Manual Dataset
    test_case = TestCase(
        id="debug-tc-001",
        question="암보험 가입 시 고지 의무는 무엇인가요?",
        answer="계약 전 알릴 의무를 말하며, 과거 질병 이력 등을 사실대로 알려야 합니다.",
        contexts=[
            "암보험 가입 시 계약자는 과거 병력, 직업 등 위험 측정에 필요한 사항을 사실대로 알려야 하는 고지 의무가 있습니다."
        ],
        ground_truth="암보험 가입 시 계약자는 과거 병력, 직업 등 위험 측정에 필요한 사항을 사실대로 알려야 하는 고지 의무가 있습니다.",
    )

    dataset = Dataset(name="debug_dataset", version="v1", test_cases=[test_case])

    metrics = ["faithfulness", "answer_relevancy"]

    print("Evaluating...")
    result = await evaluator.evaluate(dataset=dataset, metrics=metrics, llm=llm)

    print("\n--- Evaluation Result ---")
    for tc_result in result.results:
        print(f"TC: {tc_result.test_case_id}")
        for metric in tc_result.metrics:
            print(f"  {metric.name}: {metric.score}")

    print(f"Run ID: {result.run_id}")
    # We need to dig into how results are stored in EvaluationRun?
    # EvaluationRun has metrics info, but the interface return type is EvaluationRun.
    # Actually, RagasEvaluator.evaluate returns EvaluationRun, but where are the individual results?
    # They are not in EvaluationRun dataclass shown in `evaluator.py`:
    # class EvaluationRun: ...
    # Ah, the evaluator.evaluate code returns `run` but where does it attach `results`?
    # I need to check `evaluator.py` again. It returns `run` but might NOT be attaching the results if the dataclass doesn't have a field for it?
    # Let's check `EvaluationRun` in `result.py` or `evaluator.py` imports.
    # Ah, in `evaluator.py`:
    # async def evaluate(...) -> EvaluationRun: ...
    # It calls _evaluate_sequential which returns `dict[str, TestCaseEvalResult]`.
    # BUT `evaluate` method just returns `run`.
    # Let's check `evaluator.py` around line 260.

    # Actually, I should just trust the logs.


if __name__ == "__main__":
    asyncio.run(debug_ragas_real())
