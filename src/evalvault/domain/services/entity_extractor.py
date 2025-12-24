"""Entity and relation extraction for knowledge graph construction."""

import re
from dataclasses import dataclass


@dataclass
class Entity:
    """지식 그래프 엔티티."""

    name: str
    entity_type: str  # organization, product, money, period, coverage, etc.
    attributes: dict[str, str]


@dataclass
class Relation:
    """엔티티 간 관계."""

    source: str
    target: str
    relation_type: str  # provides, has_coverage, has_amount, has_period, etc.


class EntityExtractor:
    """문서에서 엔티티 및 관계 추출.

    보험 도메인에 특화된 패턴 매칭 기반 추출기.
    정규표현식과 규칙 기반으로 엔티티와 관계를 추출합니다.
    """

    # 보험사 패턴 (일반적인 생명보험사 및 손해보험사)
    ORGANIZATION_PATTERNS = [
        r"삼성생명",
        r"한화생명",
        r"교보생명",
        r"KB생명",
        r"신한생명",
        r"메트라이프생명",
        r"푸르덴셜생명",
        r"동양생명",
        r"미래에셋생명",
        r"라이나생명",
        r"삼성화재",
        r"현대해상",
        r"DB손해보험",
        r"메리츠화재",
        r"KB손해보험",
        r"흥국화재",
    ]

    # 보험 상품 유형 패턴
    PRODUCT_PATTERNS = [
        r"종신보험",
        r"정기보험",
        r"연금보험",
        r"암보험",
        r"건강보험",
        r"실손보험",
        r"CI보험",
        r"변액보험",
        r"저축보험",
        r"유니버셜보험",
        r"어린이보험",
        r"태아보험",
        r"운전자보험",
        r"여행자보험",
        r"보험",  # Generic insurance term
    ]

    # 보장 항목 패턴
    COVERAGE_PATTERNS = [
        r"사망보험금",
        r"암진단비",
        r"진단비",
        r"수술비",
        r"입원비",
        r"통원비",
        r"장해급여금",
        r"만기환급금",
        r"해약환급금",
        r"생존급여금",
        r"연금급여",
    ]

    # 금액 패턴
    MONEY_PATTERNS = [
        r"\d+억원?",
        r"\d+천만원?",
        r"\d+백만원?",
        r"\d+만원?",
        r"\d+,\d+원?",
        r"\d+원",
    ]

    # 기간 패턴
    PERIOD_PATTERNS = [
        r"\d+년",
        r"\d+개월",
        r"\d+일",
    ]

    def __init__(self):
        """Initialize entity extractor."""
        # Compile patterns for efficiency
        self._org_pattern = re.compile("|".join(self.ORGANIZATION_PATTERNS))
        self._product_pattern = re.compile("|".join(self.PRODUCT_PATTERNS))
        self._coverage_pattern = re.compile("|".join(self.COVERAGE_PATTERNS))
        self._money_pattern = re.compile("|".join(self.MONEY_PATTERNS))
        self._period_pattern = re.compile("|".join(self.PERIOD_PATTERNS))

    def extract_entities(self, text: str) -> list[Entity]:
        """텍스트에서 엔티티 추출.

        Args:
            text: 추출할 텍스트

        Returns:
            추출된 엔티티 리스트
        """
        if not text:
            return []

        entities = []

        # Extract organizations
        for match in self._org_pattern.finditer(text):
            entity = Entity(
                name=match.group(),
                entity_type="organization",
                attributes={"domain": "insurance"},
            )
            entities.append(entity)

        # Extract products
        for match in self._product_pattern.finditer(text):
            entity = Entity(
                name=match.group(),
                entity_type="product",
                attributes={"category": "insurance_product"},
            )
            entities.append(entity)

        # Extract coverage items
        for match in self._coverage_pattern.finditer(text):
            entity = Entity(
                name=match.group(),
                entity_type="coverage",
                attributes={"type": "benefit"},
            )
            entities.append(entity)

        # Extract money amounts
        for match in self._money_pattern.finditer(text):
            entity = Entity(
                name=match.group(),
                entity_type="money",
                attributes={"unit": "KRW"},
            )
            entities.append(entity)

        # Extract periods
        for match in self._period_pattern.finditer(text):
            entity = Entity(
                name=match.group(),
                entity_type="period",
                attributes={"type": "duration"},
            )
            entities.append(entity)

        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            key = (entity.name, entity.entity_type)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)

        return unique_entities

    def extract_relations(self, text: str, entities: list[Entity]) -> list[Relation]:
        """엔티티 간 관계 추출.

        Args:
            text: 원본 텍스트
            entities: 추출된 엔티티 리스트

        Returns:
            추출된 관계 리스트
        """
        if not text or not entities:
            return []

        relations = []

        # Create entity lookup by type
        entities_by_type = {}
        for entity in entities:
            if entity.entity_type not in entities_by_type:
                entities_by_type[entity.entity_type] = []
            entities_by_type[entity.entity_type].append(entity)

        # Extract organization -> product relations (제공/판매)
        if "organization" in entities_by_type and "product" in entities_by_type:
            relations.extend(
                self._extract_provides_relations(
                    text,
                    entities_by_type["organization"],
                    entities_by_type["product"],
                )
            )

        # Extract product -> coverage relations (보장)
        if "product" in entities_by_type and "coverage" in entities_by_type:
            relations.extend(
                self._extract_coverage_relations(
                    text,
                    entities_by_type["product"],
                    entities_by_type["coverage"],
                )
            )

        # Extract coverage -> money relations (금액)
        if "coverage" in entities_by_type and "money" in entities_by_type:
            relations.extend(
                self._extract_amount_relations(
                    text,
                    entities_by_type["coverage"],
                    entities_by_type["money"],
                )
            )

        # Extract product/coverage -> period relations (기간)
        if "period" in entities_by_type:
            for entity_type in ["product", "coverage"]:
                if entity_type in entities_by_type:
                    relations.extend(
                        self._extract_period_relations(
                            text,
                            entities_by_type[entity_type],
                            entities_by_type["period"],
                        )
                    )

        return relations

    def _extract_provides_relations(
        self,
        text: str,
        orgs: list[Entity],
        products: list[Entity],
    ) -> list[Relation]:
        """Extract 'provides' relations between organizations and products."""
        relations = []

        # Pattern: "회사의 상품" or "회사는 상품을"
        for org in orgs:
            for product in products:
                # Check if they appear close to each other
                org_pos = text.find(org.name)
                product_pos = text.find(product.name)

                if org_pos != -1 and product_pos != -1:
                    distance = abs(org_pos - product_pos)
                    # If they appear within 50 characters
                    if distance < 50:
                        relation = Relation(
                            source=org.name,
                            target=product.name,
                            relation_type="provides",
                        )
                        relations.append(relation)

        return relations

    def _extract_coverage_relations(
        self,
        text: str,
        products: list[Entity],
        coverages: list[Entity],
    ) -> list[Relation]:
        """Extract 'has_coverage' relations between products and coverage."""
        relations = []

        # Pattern: "상품은 보장금을 보장"
        for product in products:
            for coverage in coverages:
                product_pos = text.find(product.name)
                coverage_pos = text.find(coverage.name)

                if product_pos != -1 and coverage_pos != -1:
                    # Check if "보장" appears between them
                    min_pos = min(product_pos, coverage_pos)
                    max_pos = max(product_pos, coverage_pos)
                    between_text = text[min_pos:max_pos + len(coverage.name)]

                    if "보장" in between_text or max_pos - min_pos < 50:
                        relation = Relation(
                            source=product.name,
                            target=coverage.name,
                            relation_type="has_coverage",
                        )
                        relations.append(relation)

        return relations

    def _extract_amount_relations(
        self,
        text: str,
        coverages: list[Entity],
        amounts: list[Entity],
    ) -> list[Relation]:
        """Extract 'has_amount' relations between coverage and money."""
        relations = []

        for coverage in coverages:
            for amount in amounts:
                coverage_pos = text.find(coverage.name)
                amount_pos = text.find(amount.name)

                if coverage_pos != -1 and amount_pos != -1:
                    distance = abs(coverage_pos - amount_pos)
                    # If they appear within 30 characters
                    if distance < 30:
                        relation = Relation(
                            source=coverage.name,
                            target=amount.name,
                            relation_type="has_amount",
                        )
                        relations.append(relation)

        return relations

    def _extract_period_relations(
        self,
        text: str,
        sources: list[Entity],
        periods: list[Entity],
    ) -> list[Relation]:
        """Extract 'has_period' relations."""
        relations = []

        for source in sources:
            for period in periods:
                source_pos = text.find(source.name)
                period_pos = text.find(period.name)

                if source_pos != -1 and period_pos != -1:
                    distance = abs(source_pos - period_pos)
                    # If they appear within 40 characters
                    if distance < 40:
                        relation = Relation(
                            source=source.name,
                            target=period.name,
                            relation_type="has_period",
                        )
                        relations.append(relation)

        return relations
