# Domain Services

Core domain services that orchestrate evaluation, analysis, and domain learning.

## RagasEvaluator

Primary evaluation service using the Ragas framework.

::: evalvault.domain.services.evaluator.RagasEvaluator
    options:
      show_root_heading: true
      show_source: true

## MemoryAwareEvaluator

Evaluator with memory tracking and optimization capabilities.

::: evalvault.domain.services.memory_aware_evaluator.MemoryAwareEvaluator
    options:
      show_root_heading: true
      show_source: true

## AnalysisService

Service for query analysis and intent-based processing.

::: evalvault.domain.services.analysis_service.AnalysisService
    options:
      show_root_heading: true
      show_source: true

## MemoryBasedAnalysis

Generates trend and recommendation summaries from domain memory.

::: evalvault.domain.services.memory_based_analysis.MemoryBasedAnalysis
    options:
      show_root_heading: true
      show_source: true

## DomainLearningHook

Hooks for storing learning artifacts from evaluation runs.

::: evalvault.domain.services.domain_learning_hook.DomainLearningHook
    options:
      show_root_heading: true
      show_source: true

## ImprovementGuideService

Builds actionable improvement guidance based on evaluation outcomes.

::: evalvault.domain.services.improvement_guide_service.ImprovementGuideService
    options:
      show_root_heading: true
      show_source: true

## KoreanRAGBenchmarkRunner

Runs the curated Korean RAG benchmark suite.

::: evalvault.domain.services.benchmark_runner.KoreanRAGBenchmarkRunner
    options:
      show_root_heading: true
      show_source: true

## KnowledgeGraphGenerator

Builds knowledge graphs for GraphRAG workflows.

::: evalvault.domain.services.kg_generator.KnowledgeGraphGenerator
    options:
      show_root_heading: true
      show_source: true
