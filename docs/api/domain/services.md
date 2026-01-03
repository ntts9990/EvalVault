# Domain Services

This module contains the core business logic services that orchestrate domain operations.

## Evaluator

Base evaluator service for running RAG evaluations.

::: evalvault.domain.services.evaluator.Evaluator
    options:
      show_root_heading: true
      show_source: true

## BatchExecutor

Service for executing evaluations in batches with parallel processing.

::: evalvault.domain.services.batch_executor.BatchExecutor
    options:
      show_root_heading: true
      show_source: true

## MemoryAwareEvaluator

Evaluator with memory tracking and optimization capabilities.

::: evalvault.domain.services.memory_aware_evaluator.MemoryAwareEvaluator
    options:
      show_root_heading: true
      show_source: true

## RagasEvaluator

Concrete implementation using Ragas framework for evaluation.

::: evalvault.domain.services.ragas_evaluator.RagasEvaluator
    options:
      show_root_heading: true
      show_source: true

## TestsetGenerator

Service for generating synthetic test cases.

::: evalvault.domain.services.testset_generator.TestsetGenerator
    options:
      show_root_heading: true
      show_source: true

## KGGenerator

Service for generating knowledge graphs from documents.

::: evalvault.domain.services.kg_generator.KGGenerator
    options:
      show_root_heading: true
      show_source: true

## ExperimentManager

Service for managing A/B testing experiments.

::: evalvault.domain.services.experiment_manager.ExperimentManager
    options:
      show_root_heading: true
      show_source: true

## QueryAnalyzer

Service for analyzing and classifying queries.

::: evalvault.domain.services.query_analyzer.QueryAnalyzer
    options:
      show_root_heading: true
      show_source: true

## AnalysisPipeline

DAG-based pipeline for multi-stage query analysis.

::: evalvault.domain.services.analysis_pipeline.AnalysisPipeline
    options:
      show_root_heading: true
      show_source: true

## IntentClassifier

Service for classifying user intent from queries.

::: evalvault.domain.services.intent_classifier.IntentClassifier
    options:
      show_root_heading: true
      show_source: true
