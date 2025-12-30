"""한국어 불용어 사전.

형태소 분석 후 불필요한 토큰을 필터링하기 위한 불용어 목록입니다.
"""

from __future__ import annotations

# 일반 한국어 불용어 (원형 기준)
KOREAN_STOPWORDS: set[str] = {
    # 대명사
    "것",
    "수",
    "등",
    "이",
    "그",
    "저",
    "누구",
    "무엇",
    "어디",
    "언제",
    # 의존명사
    "때",
    "데",
    "바",
    "뿐",
    "줄",
    "리",
    "듯",
    "셈",
    "채",
    "체",
    # 일반 동사/형용사 (맥락에 따라 의미 없는 경우)
    "있다",
    "하다",
    "되다",
    "않다",
    "없다",
    "같다",
    "보다",
    "주다",
    "받다",
    "이다",
    "아니다",
    "말다",
    # 부사
    "또",
    "더",
    "덜",
    "잘",
    "못",
    "안",
    "꼭",
    "곧",
    "늘",
    "항상",
    "매우",
    "아주",
    "정말",
    "진짜",
    "너무",
    "가장",
    "제일",
    # 접속사/연결어
    "그리고",
    "그러나",
    "그러면",
    "그래서",
    "그러므로",
    "따라서",
    "하지만",
    "그런데",
    "그렇지만",
    "또한",
    "및",
    "혹은",
    "또는",
    # 조사 (형태소 분석 후에도 남을 수 있는 경우)
    "은",
    "는",
    "가",
    "을",
    "를",
    "에",
    "에서",
    "로",
    "으로",
    "와",
    "과",
    "의",
    "도",
    "만",
    "까지",
    "부터",
}

# 보험 도메인 특화 불용어 (필요시 확장)
INSURANCE_STOPWORDS: set[str] = {
    "경우",
    "해당",
    "관련",
    "대한",
    "위한",
    "통해",
    "따라",
    "대해",
    "관하여",
    "있어서",
    "대하여",
    "바에",
    "의하여",
}

# 품사 태그 기반 불용어 (Kiwi 품사 태그)
# 참고: https://github.com/bab2min/kiwipiepy#품사-태그
STOPWORD_POS_TAGS: set[str] = {
    # 조사 (Josa)
    "JKS",  # 주격 조사 (이/가)
    "JKC",  # 보격 조사 (이/가)
    "JKG",  # 관형격 조사 (의)
    "JKO",  # 목적격 조사 (을/를)
    "JKB",  # 부사격 조사 (에/에서/로)
    "JKV",  # 호격 조사 (아/야)
    "JKQ",  # 인용격 조사 (라고/고)
    "JX",  # 보조사 (은/는/도/만)
    "JC",  # 접속 조사 (와/과)
    # 어미 (Ending)
    "EP",  # 선어말 어미 (시/었/겠)
    "EF",  # 종결 어미 (다/요/습니다)
    "EC",  # 연결 어미 (고/아서/면)
    "ETN",  # 명사형 전성 어미 (기/음)
    "ETM",  # 관형형 전성 어미 (은/는/을)
    # 기호 (Symbol)
    "SF",  # 마침표, 물음표, 느낌표
    "SP",  # 쉼표, 가운뎃점, 콜론, 빗금
    "SS",  # 따옴표, 괄호표, 줄표
    "SE",  # 줄임표
    "SO",  # 붙임표 (물결, 숨김, 빠짐)
    "SW",  # 기타 기호
    # 기타
    "SL",  # 외국어
    "SH",  # 한자
    "SN",  # 숫자 (단독으로는 의미 없는 경우)
}

# 키워드 추출에 유용한 품사 태그
KEYWORD_POS_TAGS: set[str] = {
    # 명사 (Noun)
    "NNG",  # 일반 명사
    "NNP",  # 고유 명사
    "NNB",  # 의존 명사 (일부만)
    # 동사 (Verb)
    "VV",  # 동사
    # 형용사 (Adjective)
    "VA",  # 형용사
    # 수사 (Numeral) - 도메인에 따라 포함
    # "NR",   # 수사 (하나, 둘)
    # "MM",   # 관형사
}


def is_stopword(
    token: str,
    pos_tag: str | None = None,
    include_domain_stopwords: bool = True,
) -> bool:
    """토큰이 불용어인지 확인합니다.

    Args:
        token: 확인할 토큰 (원형)
        pos_tag: Kiwi 품사 태그 (선택)
        include_domain_stopwords: 도메인 불용어 포함 여부

    Returns:
        불용어이면 True
    """
    # 품사 태그로 먼저 필터링 (더 정확)
    if pos_tag and pos_tag in STOPWORD_POS_TAGS:
        return True

    # 토큰 자체가 불용어인지 확인
    if token in KOREAN_STOPWORDS:
        return True

    # 도메인 불용어 확인
    return bool(include_domain_stopwords and token in INSURANCE_STOPWORDS)


def is_keyword_pos(pos_tag: str) -> bool:
    """키워드 추출에 유용한 품사인지 확인합니다.

    Args:
        pos_tag: Kiwi 품사 태그

    Returns:
        키워드 품사이면 True
    """
    return pos_tag in KEYWORD_POS_TAGS
