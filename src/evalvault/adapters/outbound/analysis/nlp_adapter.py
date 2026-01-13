"""NLP 분석 어댑터.

하이브리드 NLP 분석 기능을 제공합니다:
- 규칙 기반: 빠른 초기 분류
- ML 기반: TF-IDF, 임베딩 기반 키워드/유사도
- LLM 기반: 복잡한 케이스 처리 (선택적)
- 형태소 분석: Kiwi 기반 한국어 토큰화 (선택적)

한국어/영어 모두 지원합니다.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import TYPE_CHECKING

from evalvault.adapters.outbound.analysis.common import BaseAnalysisAdapter
from evalvault.domain.entities.analysis import (
    KeywordInfo,
    NLPAnalysis,
    QuestionType,
    QuestionTypeStats,
    TextStats,
    TopicCluster,
)

if TYPE_CHECKING:
    from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer
    from evalvault.domain.entities import EvaluationRun
    from evalvault.ports.outbound.llm_port import LLMPort

logger = logging.getLogger(__name__)


class NLPAnalysisAdapter(BaseAnalysisAdapter):
    """하이브리드 NLP 분석 어댑터.

    NLPAnalysisPort 인터페이스를 구현합니다.
    규칙 기반 + ML + LLM을 조합하여 최적의 분석 결과를 제공합니다.
    """

    # 질문 유형 분류를 위한 패턴 (한국어/영어)
    QUESTION_PATTERNS: dict[QuestionType, list[str]] = {
        QuestionType.FACTUAL: [
            # 한국어
            r"무엇",
            r"뭐",
            r"얼마",
            r"언제",
            r"어디",
            r"누구",
            r"몇",
            # 영어
            r"\bwhat\b",
            r"\bwhen\b",
            r"\bwhere\b",
            r"\bwho\b",
            r"\bwhich\b",
            r"\bhow\s+much\b",
            r"\bhow\s+many\b",
        ],
        QuestionType.REASONING: [
            # 한국어
            r"왜",
            r"어떻게",
            r"어째서",
            r"이유",
            r"원인",
            # 영어
            r"\bwhy\b",
            r"\bhow\b(?!\s+(much|many|to))",
        ],
        QuestionType.COMPARATIVE: [
            # 한국어
            r"비교",
            r"차이",
            r"다른\s*점",
            r"vs",
            r"versus",
            # 영어
            r"\bcompare\b",
            r"\bdifference\b",
            r"\bvs\.?\b",
            r"\bversus\b",
        ],
        QuestionType.PROCEDURAL: [
            # 한국어
            r"방법",
            r"절차",
            r"단계",
            r"과정",
            r"어떻게.*하",
            # 영어
            r"\bhow\s+to\b",
            r"\bsteps?\b",
            r"\bprocess\b",
            r"\bprocedure\b",
        ],
        QuestionType.OPINION: [
            # 한국어
            r"생각",
            r"의견",
            r"평가",
            r"좋은가",
            r"어떤가",
            # 영어
            r"\bopinion\b",
            r"\bthink\b",
            r"\bbelieve\b",
            r"\bfeel\b",
        ],
    }

    # 문장 구분 패턴
    SENTENCE_PATTERN = re.compile(r"[.!?。！？]+")

    # 한국어/영어 단어 패턴
    WORD_PATTERN = re.compile(r"[가-힣a-zA-Z]+")

    def __init__(
        self,
        llm_adapter: LLMPort | None = None,
        use_embeddings: bool = True,
        use_llm_classification: bool = False,
        korean_tokenizer: KiwiTokenizer | None = None,
    ) -> None:
        """NLPAnalysisAdapter 초기화.

        Args:
            llm_adapter: LLM/임베딩 제공 어댑터 (OpenAIAdapter, OllamaAdapter 등)
            use_embeddings: 임베딩 기반 분석 사용 여부
            use_llm_classification: LLM 기반 질문 분류 사용 여부
            korean_tokenizer: 한국어 형태소 분석기 (KiwiTokenizer)
        """
        super().__init__()
        self._llm_adapter = llm_adapter
        self._use_embeddings = use_embeddings and llm_adapter is not None
        self._use_llm_classification = use_llm_classification and llm_adapter is not None
        self._korean_tokenizer = korean_tokenizer
        self._tfidf_vectorizer = None

    def analyze_text_statistics(self, run: EvaluationRun) -> NLPAnalysis:
        """텍스트 기본 통계를 분석합니다."""
        if not run.results:
            return NLPAnalysis(run_id=run.run_id)

        text_fields = self.processor.collect_text_fields(run)
        questions = text_fields["questions"]
        answers = text_fields["answers"]
        contexts = text_fields["contexts"]

        question_stats = self._calculate_text_stats(questions) if questions else None
        answer_stats = self._calculate_text_stats(answers) if answers else None
        context_stats = self._calculate_text_stats(contexts) if contexts else None

        return NLPAnalysis(
            run_id=run.run_id,
            question_stats=question_stats,
            answer_stats=answer_stats,
            context_stats=context_stats,
        )

    def classify_question_types(
        self,
        run: EvaluationRun,
    ) -> list[QuestionTypeStats]:
        """질문 유형을 분류합니다.

        하이브리드 접근:
        1. 규칙 기반으로 빠르게 초기 분류
        2. (옵션) LLM으로 애매한 케이스 재분류
        """
        if not run.results:
            return []

        # 각 질문의 유형 분류
        type_results: list[tuple[QuestionType, dict[str, float]]] = []

        for result in run.results:
            if not result.question:
                continue

            # 규칙 기반 분류
            q_type = self._classify_single_question(result.question)
            metric_scores = {m.name: m.score for m in result.metrics}
            type_results.append((q_type, metric_scores))

        if not type_results:
            return []

        # 유형별 집계
        type_counts: Counter[QuestionType] = Counter()
        type_scores: dict[QuestionType, list[dict[str, float]]] = {}

        for q_type, scores in type_results:
            type_counts[q_type] += 1
            if q_type not in type_scores:
                type_scores[q_type] = []
            type_scores[q_type].append(scores)

        total_count = sum(type_counts.values())

        # QuestionTypeStats 생성
        stats_list = []
        for q_type, count in type_counts.items():
            # 평균 점수 계산
            avg_scores: dict[str, float] = {}
            if type_scores[q_type]:
                all_metric_names = set()
                for scores in type_scores[q_type]:
                    all_metric_names.update(scores.keys())

                for metric_name in all_metric_names:
                    values = [s[metric_name] for s in type_scores[q_type] if metric_name in s]
                    if values:
                        avg_scores[metric_name] = sum(values) / len(values)

            stats_list.append(
                QuestionTypeStats(
                    question_type=q_type,
                    count=count,
                    percentage=count / total_count,
                    avg_scores=avg_scores,
                )
            )

        # count 내림차순 정렬
        stats_list.sort(key=lambda x: x.count, reverse=True)

        return stats_list

    def extract_keywords(
        self,
        run: EvaluationRun,
        *,
        top_k: int = 20,
    ) -> list[KeywordInfo]:
        """키워드를 추출합니다.

        하이브리드 접근:
        1. TF-IDF로 기본 키워드 추출
        2. (옵션) 임베딩으로 의미적 키워드 보강
        """
        if not run.results:
            return []

        # 모든 텍스트 수집
        documents = []
        for result in run.results:
            doc_parts = []
            if result.question:
                doc_parts.append(result.question)
            if result.answer:
                doc_parts.append(result.answer)
            if doc_parts:
                documents.append(" ".join(doc_parts))

        if not documents:
            return []

        # TF-IDF 기반 키워드 추출
        keywords = self._extract_keywords_tfidf(documents, top_k)

        # 임베딩 기반 보강 (옵션)
        if self._use_embeddings and self._llm_adapter is not None and keywords:
            keywords = self._enhance_keywords_with_embeddings(keywords, documents)

        return keywords

    def analyze(
        self,
        run: EvaluationRun,
        *,
        include_text_stats: bool = True,
        include_question_types: bool = True,
        include_keywords: bool = True,
        include_topic_clusters: bool = False,
        top_k_keywords: int = 20,
        min_cluster_size: int = 3,
    ) -> NLPAnalysis:
        """통합 NLP 분석을 수행합니다.

        Args:
            run: 분석할 평가 실행
            include_text_stats: 텍스트 통계 포함 여부
            include_question_types: 질문 유형 분류 포함 여부
            include_keywords: 키워드 추출 포함 여부
            include_topic_clusters: 토픽 클러스터링 포함 여부 (임베딩 필요)
            top_k_keywords: 추출할 키워드 수
            min_cluster_size: 최소 클러스터 크기
        """
        result = NLPAnalysis(run_id=run.run_id)

        if include_text_stats:
            text_analysis = self.analyze_text_statistics(run)
            result.question_stats = text_analysis.question_stats
            result.answer_stats = text_analysis.answer_stats
            result.context_stats = text_analysis.context_stats

        if include_question_types:
            result.question_types = self.classify_question_types(run)

        if include_keywords:
            result.top_keywords = self.extract_keywords(run, top_k=top_k_keywords)

        if include_topic_clusters:
            result.topic_clusters = self.cluster_topics(run, min_cluster_size=min_cluster_size)

        # 인사이트 생성
        result.insights = self._generate_insights(result)

        return result

    def _calculate_text_stats(self, texts: list[str]) -> TextStats:
        """텍스트 리스트에 대한 통계를 계산합니다.

        한국어 형태소 분석기가 설정된 경우 더 정확한 토큰화를 사용합니다.
        """
        combined_text = " ".join(texts)

        # 문자 수
        char_count = len(combined_text)

        # 단어 추출 (한국어 토크나이저 사용 여부에 따라)
        if self._korean_tokenizer and self._has_korean_text([combined_text]):
            words = self._korean_tokenizer.tokenize(combined_text)
        else:
            words = self.WORD_PATTERN.findall(combined_text)
        word_count = len(words)

        # 문장 수 (한국어 토크나이저로 더 정확한 분리)
        if self._korean_tokenizer and self._has_korean_text([combined_text]):
            sentences = self._korean_tokenizer.split_sentences(combined_text)
            if not sentences:
                sentences = [
                    s.strip() for s in self.SENTENCE_PATTERN.split(combined_text) if s.strip()
                ]
        else:
            sentences = [s.strip() for s in self.SENTENCE_PATTERN.split(combined_text) if s.strip()]
        sentence_count = max(len(sentences), 1)  # 최소 1

        # 평균 단어 길이
        avg_word_length = sum(len(w) for w in words) / word_count if word_count > 0 else 0.0

        # 어휘 다양성 (고유 단어 비율)
        unique_words = {w.lower() for w in words}
        unique_word_ratio = len(unique_words) / word_count if word_count > 0 else 0.0

        return TextStats(
            char_count=char_count,
            word_count=word_count,
            sentence_count=sentence_count,
            avg_word_length=avg_word_length,
            unique_word_ratio=unique_word_ratio,
        )

    def _classify_single_question(self, question: str) -> QuestionType:
        """단일 질문의 유형을 분류합니다 (규칙 기반)."""
        question_lower = question.lower()

        # 우선순위: PROCEDURAL > COMPARATIVE > REASONING > FACTUAL > OPINION
        priority_order = [
            QuestionType.PROCEDURAL,
            QuestionType.COMPARATIVE,
            QuestionType.REASONING,
            QuestionType.FACTUAL,
            QuestionType.OPINION,
        ]

        for q_type in priority_order:
            patterns = self.QUESTION_PATTERNS[q_type]
            for pattern in patterns:
                if re.search(pattern, question_lower, re.IGNORECASE):
                    return q_type

        # 기본값: FACTUAL
        return QuestionType.FACTUAL

    def _extract_keywords_tfidf(self, documents: list[str], top_k: int) -> list[KeywordInfo]:
        """TF-IDF 기반 키워드 추출.

        한국어 형태소 분석기가 설정된 경우 Kiwi를 사용하여
        더 정확한 키워드를 추출합니다.
        """
        # 한국어 텍스트가 포함된 경우 형태소 분석 사용
        if self._korean_tokenizer and self._has_korean_text(documents):
            return self._extract_keywords_korean(documents, top_k)

        return self._extract_keywords_tfidf_basic(documents, top_k)

    def _has_korean_text(self, documents: list[str]) -> bool:
        """문서에 한국어가 포함되어 있는지 확인합니다."""
        korean_pattern = re.compile(r"[가-힣]")
        return any(korean_pattern.search(doc) for doc in documents)

    def _extract_keywords_korean(self, documents: list[str], top_k: int) -> list[KeywordInfo]:
        """Kiwi 형태소 분석기를 사용한 한국어 키워드 추출.

        형태소 분석을 통해 명사/동사/형용사를 추출하고
        TF-IDF로 중요도를 계산합니다.
        """
        if not self._korean_tokenizer:
            return self._extract_keywords_tfidf_basic(documents, top_k)

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer

            # 각 문서에서 키워드 추출 (형태소 분석)
            tokenized_docs = []
            all_keywords: list[str] = []

            for doc in documents:
                # Kiwi로 키워드 추출 (명사, 동사, 형용사)
                keywords = self._korean_tokenizer.extract_keywords(doc)
                tokenized_docs.append(" ".join(keywords))
                all_keywords.extend(keywords)

            # 빈 문서 처리
            if not any(tokenized_docs):
                return self._extract_keywords_tfidf_basic(documents, top_k)

            # TF-IDF 계산
            vectorizer = TfidfVectorizer(
                max_features=top_k * 2,
                token_pattern=r"[가-힣a-zA-Z0-9]+",
            )
            tfidf_matrix = vectorizer.fit_transform(tokenized_docs)
            feature_names = vectorizer.get_feature_names_out()

            # 각 단어의 평균 TF-IDF 점수
            mean_tfidf = tfidf_matrix.mean(axis=0).A1

            # 단어 빈도 계산
            word_counter: Counter[str] = Counter(all_keywords)

            # KeywordInfo 생성
            keywords_info = []
            for idx, word in enumerate(feature_names):
                keywords_info.append(
                    KeywordInfo(
                        keyword=word,
                        frequency=word_counter.get(word, 0),
                        tfidf_score=float(mean_tfidf[idx]),
                    )
                )

            # TF-IDF 내림차순 정렬 및 top_k 선택
            keywords_info.sort(key=lambda x: x.tfidf_score, reverse=True)
            return keywords_info[:top_k]

        except ImportError:
            logger.warning("sklearn not available, falling back to basic extraction")
            return self._extract_keywords_tfidf_basic(documents, top_k)
        except Exception as e:
            logger.warning(f"Korean keyword extraction failed: {e}, falling back")
            return self._extract_keywords_tfidf_basic(documents, top_k)

    def _extract_keywords_tfidf_basic(self, documents: list[str], top_k: int) -> list[KeywordInfo]:
        """기본 TF-IDF 키워드 추출 (정규식 기반)."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer

            vectorizer = TfidfVectorizer(
                max_features=top_k * 2,
                token_pattern=r"[가-힣a-zA-Z]{2,}",  # 한글/영어 2글자 이상
                stop_words=None,
            )
            tfidf_matrix = vectorizer.fit_transform(documents)
            feature_names = vectorizer.get_feature_names_out()

            # 각 단어의 평균 TF-IDF 점수
            mean_tfidf = tfidf_matrix.mean(axis=0).A1

            # 단어 빈도 계산
            word_counter: Counter[str] = Counter()
            for doc in documents:
                words = self.WORD_PATTERN.findall(doc.lower())
                word_counter.update(words)

            # KeywordInfo 생성
            keywords = []
            for idx, word in enumerate(feature_names):
                keywords.append(
                    KeywordInfo(
                        keyword=word,
                        frequency=word_counter.get(word.lower(), 0),
                        tfidf_score=float(mean_tfidf[idx]),
                    )
                )

            # TF-IDF 내림차순 정렬 및 top_k 선택
            keywords.sort(key=lambda x: x.tfidf_score, reverse=True)
            return keywords[:top_k]

        except ImportError:
            logger.warning("sklearn not available, keyword extraction disabled")
            return []
        except Exception as e:
            logger.warning(f"Keyword extraction failed: {e}")
            return []

    def _enhance_keywords_with_embeddings(
        self,
        keywords: list[KeywordInfo],
        documents: list[str],
    ) -> list[KeywordInfo]:
        """임베딩을 사용하여 키워드를 보강합니다."""
        if not self._llm_adapter:
            return keywords

        try:
            # 임베딩 가져오기
            embeddings = self._llm_adapter.as_ragas_embeddings()
            if embeddings is None:
                return keywords

            # 문서 임베딩 계산 (동기 메서드 사용)
            doc_embeddings = embeddings.embed_documents(documents[:10])

            # 키워드 임베딩과 문서 임베딩의 유사도 계산
            keyword_texts = [k.keyword for k in keywords[:10]]
            keyword_embeddings = embeddings.embed_documents(keyword_texts)

            # 코사인 유사도로 키워드 점수 조정
            import numpy as np

            doc_mean = np.mean(doc_embeddings, axis=0)
            for i, kw in enumerate(keywords[:10]):
                if i < len(keyword_embeddings):
                    kw_emb = np.array(keyword_embeddings[i])
                    similarity = np.dot(kw_emb, doc_mean) / (
                        np.linalg.norm(kw_emb) * np.linalg.norm(doc_mean) + 1e-8
                    )
                    # TF-IDF와 임베딩 유사도 결합
                    keywords[i] = KeywordInfo(
                        keyword=kw.keyword,
                        frequency=kw.frequency,
                        tfidf_score=kw.tfidf_score * (1 + float(similarity)) / 2,
                        avg_metric_scores=kw.avg_metric_scores,
                    )

            # 재정렬
            keywords.sort(key=lambda x: x.tfidf_score, reverse=True)
            return keywords

        except Exception as e:
            logger.debug(f"Embedding enhancement skipped: {e}")
            return keywords

    def _generate_insights(self, analysis: NLPAnalysis) -> list[str]:
        """분석 결과에서 인사이트를 생성합니다."""
        insights = []

        # 텍스트 통계 인사이트
        if analysis.question_stats:
            q_stats = analysis.question_stats
            if q_stats.unique_word_ratio > 0.8:
                insights.append("High vocabulary diversity in questions")
            elif q_stats.unique_word_ratio < 0.5:
                insights.append(
                    "Low vocabulary diversity in questions - may have repetitive patterns"
                )

            if q_stats.avg_sentence_length > 30:
                insights.append("Questions tend to be long and complex")
            elif q_stats.avg_sentence_length < 10:
                insights.append("Questions are short and concise")

        # 질문 유형 인사이트
        if analysis.question_types:
            dominant = analysis.dominant_question_type
            if dominant:
                dominant_stats = next(
                    (s for s in analysis.question_types if s.question_type == dominant),
                    None,
                )
                if dominant_stats and dominant_stats.percentage > 0.5:
                    insights.append(
                        f"Dominant question type: {dominant.value} "
                        f"({dominant_stats.percentage:.0%})"
                    )

        # 키워드 인사이트
        if analysis.top_keywords:
            top_3 = [k.keyword for k in analysis.top_keywords[:3]]
            if top_3:
                insights.append(f"Top keywords: {', '.join(top_3)}")

        # 토픽 클러스터 인사이트
        if analysis.topic_clusters:
            insights.append(f"Found {len(analysis.topic_clusters)} topic clusters")

        return insights

    def cluster_topics(
        self,
        run: EvaluationRun,
        *,
        min_cluster_size: int = 3,
        max_clusters: int = 10,
    ) -> list[TopicCluster]:
        """질문을 토픽으로 클러스터링합니다.

        임베딩 기반 클러스터링을 수행합니다.
        LLM 어댑터가 없거나 임베딩을 사용할 수 없으면 빈 리스트를 반환합니다.

        Args:
            run: 분석할 평가 실행
            min_cluster_size: 최소 클러스터 크기
            max_clusters: 최대 클러스터 수

        Returns:
            토픽 클러스터 리스트
        """
        if not run.results:
            return []

        if not self._use_embeddings or self._llm_adapter is None:
            logger.debug("Topic clustering requires embeddings - skipping")
            return []

        questions = [r.question for r in run.results if r.question]
        if len(questions) < min_cluster_size:
            logger.debug(f"Not enough questions for clustering: {len(questions)}")
            return []

        try:
            # 임베딩 가져오기
            embeddings = self._llm_adapter.as_ragas_embeddings()
            if embeddings is None:
                logger.debug("No embeddings available for clustering")
                return []

            # 질문 임베딩 계산
            question_embeddings = embeddings.embed_documents(questions)

            # 간단한 k-means 클러스터링 (sklearn 사용)
            return self._cluster_with_kmeans(
                questions=questions,
                embeddings=question_embeddings,
                run=run,
                min_cluster_size=min_cluster_size,
                max_clusters=max_clusters,
            )

        except Exception as e:
            logger.warning(f"Topic clustering failed: {e}")
            return []

    def _cluster_with_kmeans(
        self,
        questions: list[str],
        embeddings: list[list[float]],
        run: EvaluationRun,
        min_cluster_size: int,
        max_clusters: int,
    ) -> list[TopicCluster]:
        """K-Means 클러스터링을 수행합니다."""
        try:
            import numpy as np
            from sklearn.cluster import KMeans
            from sklearn.feature_extraction.text import TfidfVectorizer

            n_samples = len(questions)
            # 클러스터 수 결정 (최소 2, 최대 max_clusters, 샘플 수의 1/3)
            n_clusters = min(max_clusters, max(2, n_samples // min_cluster_size))

            if n_clusters < 2:
                return []

            # K-Means 클러스터링
            embedding_array = np.array(embeddings)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embedding_array)

            # 클러스터별 질문 그룹화
            cluster_questions: dict[int, list[str]] = {}
            cluster_indices: dict[int, list[int]] = {}

            for idx, (question, label) in enumerate(zip(questions, labels, strict=True)):
                label_int = int(label)
                if label_int not in cluster_questions:
                    cluster_questions[label_int] = []
                    cluster_indices[label_int] = []
                cluster_questions[label_int].append(question)
                cluster_indices[label_int].append(idx)

            # 각 클러스터에서 키워드 추출
            vectorizer = TfidfVectorizer(max_features=10, token_pattern=r"[가-힣a-zA-Z]{2,}")

            # 결과 맵핑 (question -> result)
            question_to_result = {r.question: r for r in run.results if r.question}

            clusters = []
            for cluster_id in sorted(cluster_questions.keys()):
                cluster_qs = cluster_questions[cluster_id]

                # 최소 크기 미달 클러스터 제외
                if len(cluster_qs) < min_cluster_size:
                    continue

                # 클러스터 키워드 추출
                try:
                    tfidf_matrix = vectorizer.fit_transform(cluster_qs)
                    feature_names = vectorizer.get_feature_names_out()
                    scores = tfidf_matrix.sum(axis=0).A1
                    top_indices = scores.argsort()[-5:][::-1]
                    keywords = [feature_names[i] for i in top_indices]
                except Exception:
                    keywords = []

                # 클러스터 평균 점수 계산
                avg_scores: dict[str, float] = {}
                metric_values: dict[str, list[float]] = {}

                for q in cluster_qs:
                    result = question_to_result.get(q)
                    if result:
                        for m in result.metrics:
                            if m.name not in metric_values:
                                metric_values[m.name] = []
                            metric_values[m.name].append(m.score)

                for metric_name, values in metric_values.items():
                    if values:
                        avg_scores[metric_name] = sum(values) / len(values)

                representative_questions: list[str] = []
                try:
                    cluster_idx_list = cluster_indices[cluster_id]
                    cluster_vectors = embedding_array[cluster_idx_list]
                    centroid = cluster_vectors.mean(axis=0)
                    distances = np.linalg.norm(cluster_vectors - centroid, axis=1)
                    sorted_pairs = sorted(
                        zip(cluster_idx_list, distances, strict=True), key=lambda x: x[1]
                    )

                    center_indices = [idx for idx, _dist in sorted_pairs[:2]]
                    edge_far = sorted_pairs[-1][0] if sorted_pairs else None

                    worst_idx = None
                    worst_score = None
                    for idx in cluster_idx_list:
                        q = questions[idx]
                        result = question_to_result.get(q)
                        if not result or not result.metrics:
                            continue
                        avg_score = sum(m.score for m in result.metrics) / len(result.metrics)
                        if worst_score is None or avg_score < worst_score:
                            worst_score = avg_score
                            worst_idx = idx

                    edge_needed = worst_idx
                    if edge_needed is None and len(sorted_pairs) > 1:
                        edge_needed = sorted_pairs[-2][0]

                    candidate_indices: list[int] = []
                    candidate_indices.extend(center_indices)
                    if edge_far is not None:
                        candidate_indices.append(edge_far)
                    if edge_needed is not None:
                        candidate_indices.append(edge_needed)

                    seen: set[int] = set()
                    for idx in candidate_indices:
                        if idx in seen:
                            continue
                        seen.add(idx)
                        representative_questions.append(questions[idx])
                        if len(representative_questions) >= 4:
                            break
                except Exception:
                    representative_questions = cluster_qs[:4]

                clusters.append(
                    TopicCluster(
                        cluster_id=cluster_id,
                        keywords=keywords,
                        document_count=len(cluster_qs),
                        avg_scores=avg_scores,
                        representative_questions=representative_questions,
                    )
                )

            # 문서 수 기준 내림차순 정렬
            clusters.sort(key=lambda c: c.document_count, reverse=True)

            return clusters

        except ImportError as e:
            logger.debug(f"Clustering dependencies not available: {e}")
            return []
        except Exception as e:
            logger.warning(f"K-Means clustering failed: {e}")
            return []
