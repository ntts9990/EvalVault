"""Synthetic Q&A generation using LLM.

Generates question-answer pairs from documents using LLM,
with ground truth for evaluation. Critical for closed-network
environments where ground truth data is scarce.
"""

from __future__ import annotations

import json
import logging
import random
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from evalvault.domain.entities import Dataset, TestCase
from evalvault.domain.services.document_chunker import DocumentChunker

if TYPE_CHECKING:
    from evalvault.ports.outbound.llm_port import LLMPort

logger = logging.getLogger(__name__)


# Prompts for Q&A generation
_QUESTION_GENERATION_PROMPT_KO = """다음 문서 내용을 기반으로 질문을 생성해주세요.

문서 내용:
{context}

요구사항:
1. 문서 내용에서 답변할 수 있는 구체적인 질문을 {num_questions}개 생성하세요.
2. 각 질문은 문서의 다른 정보를 묻도록 하세요.
3. 질문은 사실 확인, 수치 확인, 또는 내용 요약 형태가 좋습니다.
4. 너무 일반적인 질문은 피하세요.

반드시 다음 JSON 형식으로만 응답하세요:
{{"questions": ["질문1", "질문2", ...]}}"""

_QUESTION_GENERATION_PROMPT_EN = """Generate questions based on the following document content.

Document content:
{context}

Requirements:
1. Generate {num_questions} specific questions that can be answered from the document.
2. Each question should ask about different information in the document.
3. Questions should be factual, numerical, or summary-type.
4. Avoid overly general questions.

Respond ONLY in the following JSON format:
{{"questions": ["question1", "question2", ...]}}"""

_ANSWER_GENERATION_PROMPT_KO = """다음 문서 내용을 기반으로 질문에 답변해주세요.

문서 내용:
{context}

질문: {question}

요구사항:
1. 문서 내용만을 기반으로 답변하세요.
2. 문서에 정보가 없으면 "정보 없음"이라고 답변하세요.
3. 간결하고 정확하게 답변하세요.
4. 숫자나 날짜가 포함된 경우 정확히 기재하세요.

반드시 다음 JSON 형식으로만 응답하세요:
{{"answer": "답변 내용", "confidence": "high/medium/low", "has_info": true/false}}"""

_ANSWER_GENERATION_PROMPT_EN = """Answer the question based on the following document content.

Document content:
{context}

Question: {question}

Requirements:
1. Answer based only on the document content.
2. If the information is not in the document, respond with "No information available".
3. Be concise and accurate.
4. Include exact numbers or dates if mentioned.

Respond ONLY in the following JSON format:
{{"answer": "your answer", "confidence": "high/medium/low", "has_info": true/false}}"""


@dataclass
class SyntheticQAConfig:
    """Synthetic Q&A 생성 설정."""

    num_questions: int = 10
    questions_per_chunk: int = 2
    chunk_size: int = 1000
    chunk_overlap: int = 100
    dataset_name: str = "synthetic-qa-dataset"
    dataset_version: str = "1.0.0"
    language: str = "ko"  # "ko" or "en"
    include_no_answer: bool = True  # Include some no-answer cases
    no_answer_ratio: float = 0.1  # 10% of questions should have no answer
    min_confidence: str = "medium"  # Filter out low confidence answers
    metadata: dict = field(default_factory=dict)


@dataclass
class GeneratedQA:
    """생성된 Q&A 쌍."""

    question: str
    answer: str
    context: str
    confidence: str
    has_info: bool
    source_chunk_idx: int


class SyntheticQAGenerator:
    """LLM 기반 Synthetic Q&A 생성기.

    문서에서 LLM을 사용하여 질문-답변 쌍을 자동 생성합니다.
    Ground truth를 함께 생성하여 평가용 데이터셋으로 활용 가능합니다.

    Features:
    - LLM 기반 자연스러운 질문 생성
    - 문서 기반 정확한 답변 (Ground Truth) 생성
    - 신뢰도 기반 품질 필터링
    - "정답 없음" 케이스 포함 지원
    - 한국어/영어 지원

    Example:
        >>> from evalvault.ports.outbound.llm_port import LLMPort
        >>> llm: LLMPort = ...
        >>> generator = SyntheticQAGenerator(llm)
        >>> dataset = generator.generate(documents, config)
    """

    def __init__(self, llm: LLMPort):
        """Initialize SyntheticQAGenerator.

        Args:
            llm: LLM adapter for text generation
        """
        self.llm = llm

    def _get_question_prompt(self, context: str, num_questions: int, language: str) -> str:
        """Get question generation prompt."""
        if language == "ko":
            return _QUESTION_GENERATION_PROMPT_KO.format(
                context=context, num_questions=num_questions
            )
        return _QUESTION_GENERATION_PROMPT_EN.format(context=context, num_questions=num_questions)

    def _get_answer_prompt(self, context: str, question: str, language: str) -> str:
        """Get answer generation prompt."""
        if language == "ko":
            return _ANSWER_GENERATION_PROMPT_KO.format(context=context, question=question)
        return _ANSWER_GENERATION_PROMPT_EN.format(context=context, question=question)

    def _parse_questions(self, response: str) -> list[str]:
        """Parse questions from LLM response."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                questions = data.get("questions", [])
                if isinstance(questions, list):
                    return [q.strip() for q in questions if isinstance(q, str) and q.strip()]
        except (json.JSONDecodeError, AttributeError):
            pass

        # Fallback: try to extract questions line by line
        lines = response.strip().split("\n")
        questions = []
        for line in lines:
            line = line.strip()
            # Remove common prefixes
            line = re.sub(r"^[\d]+[\.\)]\s*", "", line)
            line = re.sub(r"^[-•]\s*", "", line)
            if line and "?" in line or line.endswith("요") or line.endswith("까"):
                questions.append(line)

        return questions[:5]  # Limit to 5 questions

    def _parse_answer(self, response: str) -> dict:
        """Parse answer from LLM response."""
        try:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    "answer": str(data.get("answer", "")).strip(),
                    "confidence": str(data.get("confidence", "low")).lower(),
                    "has_info": bool(data.get("has_info", False)),
                }
        except (json.JSONDecodeError, AttributeError):
            pass

        # Fallback: use the whole response as answer
        return {
            "answer": response.strip()[:500],
            "confidence": "low",
            "has_info": bool(response.strip()),
        }

    def _generate_questions_for_chunk(
        self, chunk: str, chunk_idx: int, config: SyntheticQAConfig
    ) -> list[str]:
        """Generate questions for a single chunk."""
        prompt = self._get_question_prompt(chunk, config.questions_per_chunk, config.language)

        try:
            response = self.llm.generate_text(prompt, json_mode=True)
            questions = self._parse_questions(response)
            logger.debug("Generated %d questions for chunk %d", len(questions), chunk_idx)
            return questions
        except Exception as e:
            logger.warning("Failed to generate questions for chunk %d: %s", chunk_idx, e)
            return []

    def _generate_answer_for_question(
        self, question: str, context: str, config: SyntheticQAConfig
    ) -> dict:
        """Generate answer for a question."""
        prompt = self._get_answer_prompt(context, question, config.language)

        try:
            response = self.llm.generate_text(prompt, json_mode=True)
            return self._parse_answer(response)
        except Exception as e:
            logger.warning("Failed to generate answer: %s", e)
            return {"answer": "", "confidence": "low", "has_info": False}

    def _filter_by_confidence(
        self, qa_list: list[GeneratedQA], min_confidence: str
    ) -> list[GeneratedQA]:
        """Filter Q&A pairs by confidence level."""
        confidence_order = {"high": 3, "medium": 2, "low": 1}
        min_level = confidence_order.get(min_confidence, 1)

        filtered = []
        for qa in qa_list:
            qa_level = confidence_order.get(qa.confidence, 0)
            if qa_level >= min_level:
                filtered.append(qa)
            else:
                logger.debug("Filtered out low confidence Q&A: %s", qa.question[:50])

        return filtered

    def _generate_no_answer_cases(
        self, chunks: list[str], num_cases: int, config: SyntheticQAConfig
    ) -> list[GeneratedQA]:
        """Generate no-answer test cases.

        Creates questions about content that isn't in the provided chunks.
        """
        no_answer_questions_ko = [
            "이 문서에서 다루지 않는 다른 보험 상품의 보험료는 얼마인가요?",
            "작년 대비 올해의 가입자 증가율은 얼마인가요?",
            "이 보험의 가입 심사 기준은 무엇인가요?",
            "보험금 청구 시 필요한 서류는 무엇인가요?",
            "이 보험 상품의 출시일은 언제인가요?",
        ]
        no_answer_questions_en = [
            "What is the premium for other insurance products not covered in this document?",
            "What is the year-over-year subscriber growth rate?",
            "What are the underwriting criteria for this insurance?",
            "What documents are required for claims?",
            "When was this insurance product launched?",
        ]

        questions = no_answer_questions_ko if config.language == "ko" else no_answer_questions_en
        selected_questions = random.sample(questions, min(num_cases, len(questions)))

        no_answer_text = "정보 없음" if config.language == "ko" else "No information available"

        no_answer_cases = []
        for question in selected_questions:
            # Use a random chunk as context (but the question is about something not in it)
            context = random.choice(chunks) if chunks else ""
            no_answer_cases.append(
                GeneratedQA(
                    question=question,
                    answer=no_answer_text,
                    context=context,
                    confidence="high",
                    has_info=False,
                    source_chunk_idx=-1,  # No specific chunk
                )
            )

        return no_answer_cases

    def generate(
        self,
        documents: list[str],
        config: SyntheticQAConfig,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Dataset:
        """Generate synthetic Q&A dataset from documents.

        Args:
            documents: List of document texts
            config: Generation configuration
            progress_callback: Optional callback for progress updates (current, total)

        Returns:
            Generated Dataset with test cases including ground truth
        """
        if not documents:
            return Dataset(
                name=config.dataset_name,
                version=config.dataset_version,
                test_cases=[],
                metadata={
                    "generated_at": datetime.now().isoformat(),
                    "method": "synthetic_qa",
                    "num_source_documents": 0,
                },
            )

        # Chunk documents
        chunker = DocumentChunker(
            chunk_size=config.chunk_size,
            overlap=config.chunk_overlap,
        )

        all_chunks = []
        for doc in documents:
            chunks = chunker.chunk(doc)
            all_chunks.extend(chunks)

        if not all_chunks:
            logger.warning("No chunks generated from documents")
            return Dataset(
                name=config.dataset_name,
                version=config.dataset_version,
                test_cases=[],
                metadata={
                    "generated_at": datetime.now().isoformat(),
                    "method": "synthetic_qa",
                    "num_source_documents": len(documents),
                },
            )

        # Calculate how many chunks to process
        # Each chunk produces `questions_per_chunk` questions
        chunks_needed = (config.num_questions // config.questions_per_chunk) + 1
        chunks_to_process = (
            all_chunks[:chunks_needed] if len(all_chunks) > chunks_needed else all_chunks
        )

        # Generate Q&A pairs
        generated_qas: list[GeneratedQA] = []
        total_steps = len(chunks_to_process)

        for chunk_idx, chunk in enumerate(chunks_to_process):
            if progress_callback:
                progress_callback(chunk_idx, total_steps)

            # Generate questions for this chunk
            questions = self._generate_questions_for_chunk(chunk, chunk_idx, config)

            # Generate answers for each question
            for question in questions:
                answer_data = self._generate_answer_for_question(question, chunk, config)

                generated_qas.append(
                    GeneratedQA(
                        question=question,
                        answer=answer_data["answer"],
                        context=chunk,
                        confidence=answer_data["confidence"],
                        has_info=answer_data["has_info"],
                        source_chunk_idx=chunk_idx,
                    )
                )

                # Check if we have enough
                if len(generated_qas) >= config.num_questions:
                    break

            if len(generated_qas) >= config.num_questions:
                break

        if progress_callback:
            progress_callback(total_steps, total_steps)

        # Filter by confidence
        filtered_qas = self._filter_by_confidence(generated_qas, config.min_confidence)

        # Add no-answer cases if configured
        if config.include_no_answer and config.no_answer_ratio > 0:
            num_no_answer = max(1, int(config.num_questions * config.no_answer_ratio))
            no_answer_cases = self._generate_no_answer_cases(all_chunks, num_no_answer, config)
            filtered_qas.extend(no_answer_cases)

        # Shuffle and limit
        random.shuffle(filtered_qas)
        final_qas = filtered_qas[: config.num_questions]

        # Convert to TestCase objects
        test_cases = []
        for qa in final_qas:
            test_case = TestCase(
                id=f"syn-{uuid4().hex[:8]}",
                question=qa.question,
                answer="",  # Answer will be generated by RAG system
                contexts=[qa.context],
                ground_truth=qa.answer,  # LLM-generated answer as ground truth
                metadata={
                    "generated": True,
                    "method": "synthetic_qa",
                    "confidence": qa.confidence,
                    "has_info": qa.has_info,
                    "source_chunk_idx": qa.source_chunk_idx,
                },
            )
            test_cases.append(test_case)

        # Create dataset metadata
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "method": "synthetic_qa",
            "llm_model": self.llm.get_model_name(),
            "num_source_documents": len(documents),
            "num_chunks": len(all_chunks),
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "language": config.language,
            "include_no_answer": config.include_no_answer,
            "min_confidence": config.min_confidence,
            "questions_generated": len(generated_qas),
            "questions_filtered": len(filtered_qas),
            "questions_final": len(test_cases),
        }
        metadata.update(config.metadata)

        return Dataset(
            name=config.dataset_name,
            version=config.dataset_version,
            test_cases=test_cases,
            metadata=metadata,
        )
