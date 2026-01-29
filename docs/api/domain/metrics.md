# Custom Metrics

This module contains custom evaluation metrics specific to the insurance domain.

## InsuranceTermAccuracy

Custom metric for evaluating accuracy of insurance-specific terminology.

::: evalvault.domain.metrics.insurance.InsuranceTermAccuracy
    options:
      show_root_heading: true
      show_source: true

## Available Ragas Metrics

EvalVault supports all standard Ragas metrics:

- **faithfulness**: Measures how factually accurate the answer is based on the given context
- **answer_relevancy**: Evaluates how relevant the answer is to the question
- **context_precision**: Measures the precision of retrieved context chunks
- **context_recall**: Evaluates if all necessary information was retrieved
- **factual_correctness**: Compares answer against ground truth for factual accuracy
- **semantic_similarity**: Measures semantic similarity between answer and ground truth

For detailed metric descriptions, see the [Handbook](../../handbook/CHAPTERS/02_data_and_metrics.md).
