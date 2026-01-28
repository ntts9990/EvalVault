"""Phase 14.2: Intent Classifier Service.

사용자 쿼리에서 분석 의도를 추출하는 키워드 기반 규칙 분류기입니다.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
from evalvault.ports.outbound.intent_classifier_port import IntentClassificationResult

# =============================================================================
# IntentKeywordRegistry
# =============================================================================


@dataclass
class IntentKeywordRegistry:
    """의도별 키워드 매핑 레지스트리.

    각 분석 의도에 해당하는 키워드들을 관리합니다.
    """

    _keywords: dict[AnalysisIntent, set[str]] = field(default_factory=dict)

    def __post_init__(self):
        """기본 키워드 등록."""
        self._register_default_keywords()

    def _register_default_keywords(self):
        """의도별 기본 키워드 등록."""
        # 검증 (Verification)
        self._keywords[AnalysisIntent.VERIFY_MORPHEME] = {
            "형태소",
            "토큰",
            "토큰화",
            "tokenize",
            "tokenization",
            "morpheme",
            "품사",
            "태깅",
            "확인",
            "검증",
            "verify",
        }
        self._keywords[AnalysisIntent.VERIFY_EMBEDDING] = {
            "임베딩",
            "embedding",
            "벡터",
            "vector",
            "표현",
            "representation",
            "분포",
            "distribution",
            "품질",
            "quality",
            "확인",
            "검증",
        }
        self._keywords[AnalysisIntent.VERIFY_RETRIEVAL] = {
            "검색",
            "retrieval",
            "retrieve",
            "컨텍스트",
            "context",
            "문서",
            "document",
            "확인",
            "검증",
            "품질",
        }

        # 비교 (Comparison)
        self._keywords[AnalysisIntent.COMPARE_SEARCH_METHODS] = {
            "RRF",
            "rrf",
            "하이브리드",
            "hybrid",
            "BM25",
            "bm25",
            "검색",
            "search",
            "비교",
            "compare",
            "방식",
            "method",
            "fusion",
        }
        self._keywords[AnalysisIntent.COMPARE_MODELS] = {
            "모델",
            "model",
            "GPT",
            "gpt",
            "Claude",
            "claude",
            "LLM",
            "llm",
            "비교",
            "compare",
            "성능",
            "performance",
        }
        self._keywords[AnalysisIntent.COMPARE_RUNS] = {
            "실행",
            "run",
            "이전",
            "previous",
            "결과",
            "result",
            "비교",
            "compare",
            "차이",
            "difference",
            "평가",
            "evaluation",
        }

        # 분석 (Analysis)
        self._keywords[AnalysisIntent.ANALYZE_LOW_METRICS] = {
            "낮은",
            "low",
            "떨어",
            "drop",
            "원인",
            "cause",
            "이유",
            "reason",
            "why",
            "왜",
            "메트릭",
            "metric",
            "점수",
            "score",
            "recall",
            "faithfulness",
            "precision",
        }
        self._keywords[AnalysisIntent.ANALYZE_PATTERNS] = {
            "패턴",
            "pattern",
            "유형",
            "type",
            "분류",
            "classification",
            "카테고리",
            "category",
        }
        self._keywords[AnalysisIntent.ANALYZE_TRENDS] = {
            "추세",
            "trend",
            "트렌드",
            "시간",
            "time",
            "변화",
            "change",
            "추이",
            "history",
        }
        self._keywords[AnalysisIntent.ANALYZE_STATISTICAL] = {
            "통계",
            "statistical",
            "statistics",
            "평균",
            "mean",
            "median",
            "분산",
            "variance",
            "표준편차",
            "std",
        }
        self._keywords[AnalysisIntent.ANALYZE_NLP] = {
            "nlp",
            "언어",
            "텍스트",
            "text",
            "문장",
            "sentence",
            "키워드",
            "keyword",
            "토픽",
            "topic",
        }
        self._keywords[AnalysisIntent.ANALYZE_DATASET_FEATURES] = {
            "데이터셋",
            "dataset",
            "특성",
            "feature",
            "features",
            "분포",
            "distribution",
            "상관",
            "correlation",
            "중요도",
            "importance",
        }
        self._keywords[AnalysisIntent.ANALYZE_CAUSAL] = {
            "인과",
            "causal",
            "cause",
            "effect",
            "원인",
            "영향",
            "intervention",
        }
        self._keywords[AnalysisIntent.ANALYZE_NETWORK] = {
            "네트워크",
            "network",
            "graph",
            "그래프",
            "연결",
            "centrality",
        }
        self._keywords[AnalysisIntent.ANALYZE_PLAYBOOK] = {
            "playbook",
            "플레이북",
            "규칙",
            "rule",
            "추천",
            "recommendation",
        }
        self._keywords[AnalysisIntent.DETECT_ANOMALIES] = {
            "이상",
            "anomaly",
            "anomalies",
            "outlier",
            "이상치",
            "detect",
        }
        self._keywords[AnalysisIntent.FORECAST_PERFORMANCE] = {
            "예측",
            "forecast",
            "predict",
            "projection",
            "미래",
            "future",
        }
        self._keywords[AnalysisIntent.GENERATE_HYPOTHESES] = {
            "가설",
            "hypothesis",
            "hypotheses",
            "실험",
            "experiment",
            "검증",
        }
        self._keywords[AnalysisIntent.BENCHMARK_RETRIEVAL] = {
            "벤치마크",
            "benchmark",
            "검색 벤치마크",
            "retrieval benchmark",
            "검색 평가",
            "retrieval 평가",
            "retriever",
            "recall@k",
            "ndcg",
        }

        # 보고서 (Report) - 높은 가중치 키워드 (보고서 관련 키워드가 있으면 우선)
        self._keywords[AnalysisIntent.GENERATE_SUMMARY] = {
            "요약",
            "summary",
            "summarize",
            "간단",
            "brief",
            "정리",
            "overview",
            "요약해",
            "요약해줘",
        }
        self._keywords[AnalysisIntent.GENERATE_DETAILED] = {
            "상세",
            "detailed",
            "detail",
            "자세",
            "전체",
            "full",
            "comprehensive",
            "리포트",
            "report",
            "보고서",
        }
        self._keywords[AnalysisIntent.GENERATE_COMPARISON] = {
            "비교 보고서",
            "비교 리포트",
            "comparison report",
            "비교리포트",
            "비교보고서",
        }

    def get_keywords(self, intent: AnalysisIntent) -> set[str]:
        """의도에 대한 키워드 조회.

        Args:
            intent: 분석 의도

        Returns:
            키워드 집합
        """
        return self._keywords.get(intent, set())

    def add_keywords(self, intent: AnalysisIntent, keywords: list[str]) -> None:
        """의도에 키워드 추가.

        Args:
            intent: 분석 의도
            keywords: 추가할 키워드 목록
        """
        if intent not in self._keywords:
            self._keywords[intent] = set()
        self._keywords[intent].update(keywords)

    def match_query(self, query: str) -> list[tuple[AnalysisIntent, int]]:
        """쿼리에서 의도 매칭.

        Args:
            query: 사용자 쿼리

        Returns:
            (의도, 점수) 튜플 목록 (점수 높은 순)
        """
        query_lower = query.lower()
        matches: list[tuple[AnalysisIntent, int]] = []

        for intent, keywords in self._keywords.items():
            score = 0
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in query_lower:
                    # 긴 키워드(구)는 더 높은 점수
                    word_count = len(keyword.split())
                    score += word_count * 2
            if score > 0:
                matches.append((intent, score))

        # 점수 높은 순 정렬
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches


# =============================================================================
# KeywordIntentClassifier
# =============================================================================


@dataclass
class KeywordIntentClassifier:
    """키워드 기반 의도 분류기.

    사용자 쿼리에서 키워드를 추출하고 의도를 분류합니다.
    """

    registry: IntentKeywordRegistry = field(default_factory=IntentKeywordRegistry)
    default_intent: AnalysisIntent = AnalysisIntent.GENERATE_SUMMARY

    def classify(self, query: str) -> AnalysisIntent:
        """쿼리에서 의도 분류.

        Args:
            query: 사용자 쿼리

        Returns:
            분류된 의도
        """
        matches = self.registry.match_query(query)
        if matches:
            return matches[0][0]
        return self.default_intent

    def classify_with_confidence(self, query: str) -> IntentClassificationResult:
        """쿼리에서 의도 분류 (신뢰도 포함).

        Args:
            query: 사용자 쿼리

        Returns:
            분류 결과
        """
        matches = self.registry.match_query(query)
        keywords = self.extract_keywords(query)

        if not matches:
            return IntentClassificationResult(
                intent=self.default_intent,
                confidence=0.3,
                keywords=keywords,
                alternative_intents=[],
            )

        # 최고 점수를 기준으로 신뢰도 계산
        top_intent, top_score = matches[0]

        # 신뢰도 계산 개선: 점수와 키워드 수를 함께 고려
        # 기본 신뢰도 0.5 + 점수 보너스 (최대 0.5)
        base_confidence = 0.5
        score_bonus = min(0.5, top_score * 0.1)
        confidence = min(1.0, base_confidence + score_bonus)

        # 대안 의도 (최대 3개)
        alternatives: list[tuple[AnalysisIntent, float]] = []
        for intent, score in matches[1:4]:
            alt_confidence = 0.3 + min(0.4, score * 0.1)
            alternatives.append((intent, alt_confidence))

        return IntentClassificationResult(
            intent=top_intent,
            confidence=confidence,
            keywords=keywords,
            alternative_intents=alternatives,
        )

    def extract_keywords(self, query: str) -> list[str]:
        """쿼리에서 핵심 키워드 추출.

        Args:
            query: 사용자 쿼리

        Returns:
            키워드 목록
        """
        # 모든 의도의 키워드 합집합
        all_keywords: set[str] = set()
        for intent in AnalysisIntent:
            all_keywords.update(self.registry.get_keywords(intent))

        query_lower = query.lower()
        found_keywords: list[str] = []

        for keyword in all_keywords:
            if keyword.lower() in query_lower:
                found_keywords.append(keyword)

        return found_keywords
