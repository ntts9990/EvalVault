"""Korean NLP adapters.

한국어 자연어 처리를 위한 어댑터 모듈입니다.
Kiwi 형태소 분석기를 기반으로 토큰화, 키워드 추출 등을 제공합니다.
"""

from evalvault.adapters.outbound.nlp.korean.kiwi_tokenizer import KiwiTokenizer
from evalvault.adapters.outbound.nlp.korean.korean_stopwords import (
    KOREAN_STOPWORDS,
    STOPWORD_POS_TAGS,
    is_stopword,
)

__all__ = [
    "KiwiTokenizer",
    "KOREAN_STOPWORDS",
    "STOPWORD_POS_TAGS",
    "is_stopword",
]
