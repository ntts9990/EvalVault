"""Unit tests for domain configuration module.

Tests for DomainMemoryConfig Pydantic models and config loading/saving.
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from evalvault.config.domain_config import (
    DomainMemoryConfig,
    DomainMetadata,
    ExperientialConfig,
    FactualConfig,
    LanguageConfig,
    LearningConfig,
    WorkingConfig,
    generate_domain_template,
    list_domains,
    load_domain_config,
    save_domain_config,
)


class TestLanguageConfig:
    """Tests for LanguageConfig model."""

    def test_language_config_defaults(self):
        """기본값 테스트."""
        config = LanguageConfig()
        assert config.ko is None
        assert config.en is None

    def test_language_config_with_values(self):
        """값 설정 테스트."""
        config = LanguageConfig(ko="terms_ko.json", en="terms_en.json")
        assert config.ko == "terms_ko.json"
        assert config.en == "terms_en.json"

    def test_get_language(self):
        """언어별 리소스 경로 조회."""
        config = LanguageConfig(ko="terms_ko.json", en="terms_en.json")
        assert config.get("ko") == "terms_ko.json"
        assert config.get("en") == "terms_en.json"
        assert config.get("ja") is None

    def test_languages_list(self):
        """설정된 언어 목록 반환."""
        config = LanguageConfig(ko="terms_ko.json")
        assert config.languages() == ["ko"]

        config2 = LanguageConfig(ko="terms_ko.json", en="terms_en.json")
        assert set(config2.languages()) == {"ko", "en"}


class TestFactualConfig:
    """Tests for FactualConfig model."""

    def test_factual_config_defaults(self):
        """기본값 테스트."""
        config = FactualConfig()
        assert config.glossary.ko is None
        assert config.glossary.en is None
        assert config.regulatory_rules is None
        assert config.shared == {}

    def test_factual_config_with_glossary(self):
        """용어사전 설정 테스트."""
        config = FactualConfig(
            glossary=LanguageConfig(ko="terms_ko.json", en="terms_en.json"),
            shared={"companies": "companies.json"},
        )
        assert config.glossary.ko == "terms_ko.json"
        assert config.shared["companies"] == "companies.json"


class TestExperientialConfig:
    """Tests for ExperientialConfig model."""

    def test_experiential_config_defaults(self):
        """기본값 테스트."""
        config = ExperientialConfig()
        assert config.failure_modes == "failures.json"
        assert config.behavior_handbook == "behaviors.json"

    def test_experiential_config_with_reliability(self):
        """신뢰도 점수 설정 테스트."""
        config = ExperientialConfig(
            reliability_scores=LanguageConfig(ko="reliability_ko.json"),
        )
        assert config.reliability_scores.ko == "reliability_ko.json"


class TestWorkingConfig:
    """Tests for WorkingConfig model."""

    def test_working_config_defaults(self):
        """기본값 테스트."""
        config = WorkingConfig()
        assert config.run_cache == "${RUN_DIR}/memory.db"
        assert config.kg_binding is None
        assert config.max_cache_size_mb == 100

    def test_working_config_custom(self):
        """사용자 정의 설정 테스트."""
        config = WorkingConfig(
            run_cache="/tmp/cache.db",
            kg_binding="kg://insurance",
            max_cache_size_mb=200,
        )
        assert config.run_cache == "/tmp/cache.db"
        assert config.kg_binding == "kg://insurance"
        assert config.max_cache_size_mb == 200


class TestLearningConfig:
    """Tests for LearningConfig model."""

    def test_learning_config_defaults(self):
        """기본값 테스트."""
        config = LearningConfig()
        assert config.enabled is True
        assert config.min_confidence_to_store == 0.6
        assert config.behavior_extraction is True
        assert config.auto_apply is True
        assert config.decay_rate == 0.95
        assert config.forget_threshold_days == 90

    def test_learning_config_validation(self):
        """값 범위 검증 테스트."""
        # Valid values
        config = LearningConfig(
            min_confidence_to_store=0.0,
            decay_rate=1.0,
        )
        assert config.min_confidence_to_store == 0.0
        assert config.decay_rate == 1.0

    def test_learning_config_invalid_confidence(self):
        """잘못된 confidence 값 검증."""
        with pytest.raises(ValueError):
            LearningConfig(min_confidence_to_store=1.5)

    def test_learning_config_invalid_decay_rate(self):
        """잘못된 decay_rate 값 검증."""
        with pytest.raises(ValueError):
            LearningConfig(decay_rate=-0.1)


class TestDomainMetadata:
    """Tests for DomainMetadata model."""

    def test_metadata_required_fields(self):
        """필수 필드 테스트."""
        metadata = DomainMetadata(domain="insurance")
        assert metadata.domain == "insurance"
        assert metadata.version == "1.0.0"
        assert metadata.supported_languages == ["ko", "en"]
        assert metadata.default_language == "ko"

    def test_metadata_custom_values(self):
        """사용자 정의 값 테스트."""
        metadata = DomainMetadata(
            domain="medical",
            version="2.0.0",
            supported_languages=["ko"],
            default_language="ko",
            description="의료 도메인",
        )
        assert metadata.domain == "medical"
        assert metadata.version == "2.0.0"
        assert metadata.description == "의료 도메인"


class TestDomainMemoryConfig:
    """Tests for DomainMemoryConfig model."""

    def test_domain_memory_config_minimal(self):
        """최소 설정 테스트."""
        config = DomainMemoryConfig(
            metadata=DomainMetadata(domain="test"),
        )
        assert config.metadata.domain == "test"
        assert config.learning.enabled is True

    def test_domain_memory_config_full(self):
        """전체 설정 테스트."""
        config = DomainMemoryConfig(
            metadata=DomainMetadata(
                domain="insurance",
                supported_languages=["ko", "en"],
            ),
            factual=FactualConfig(
                glossary=LanguageConfig(ko="terms_ko.json", en="terms_en.json"),
            ),
            experiential=ExperientialConfig(
                reliability_scores=LanguageConfig(ko="reliability_ko.json"),
            ),
            working=WorkingConfig(max_cache_size_mb=200),
            learning=LearningConfig(enabled=True, min_confidence_to_store=0.7),
        )
        assert config.metadata.domain == "insurance"
        assert config.factual.glossary.ko == "terms_ko.json"
        assert config.learning.min_confidence_to_store == 0.7

    def test_get_glossary_path(self):
        """용어사전 경로 조회 테스트."""
        config = DomainMemoryConfig(
            metadata=DomainMetadata(domain="insurance", default_language="ko"),
            factual=FactualConfig(
                glossary=LanguageConfig(ko="terms_ko.json", en="terms_en.json"),
            ),
        )
        assert config.get_glossary_path() == "terms_ko.json"
        assert config.get_glossary_path("en") == "terms_en.json"
        assert config.get_glossary_path("ja") is None

    def test_supports_language(self):
        """언어 지원 확인 테스트."""
        config = DomainMemoryConfig(
            metadata=DomainMetadata(
                domain="insurance",
                supported_languages=["ko", "en"],
            ),
        )
        assert config.supports_language("ko") is True
        assert config.supports_language("en") is True
        assert config.supports_language("ja") is False


class TestGenerateDomainTemplate:
    """Tests for generate_domain_template function."""

    def test_generate_template_default(self):
        """기본 템플릿 생성 테스트."""
        template = generate_domain_template("insurance")
        assert template["metadata"]["domain"] == "insurance"
        assert template["metadata"]["supported_languages"] == ["ko", "en"]
        assert template["metadata"]["default_language"] == "ko"
        assert template["learning"]["enabled"] is True

    def test_generate_template_custom_languages(self):
        """사용자 정의 언어 템플릿 생성."""
        template = generate_domain_template("medical", languages=["ko"])
        assert template["metadata"]["supported_languages"] == ["ko"]
        assert template["factual"]["glossary"]["ko"] == "terms_dictionary_ko.json"
        assert "en" not in template["factual"]["glossary"]

    def test_generate_template_with_description(self):
        """설명 포함 템플릿 생성."""
        template = generate_domain_template(
            "insurance",
            description="보험 도메인 설정",
        )
        assert template["metadata"]["description"] == "보험 도메인 설정"


class TestSaveAndLoadDomainConfig:
    """Tests for save_domain_config and load_domain_config functions."""

    def test_save_and_load_config(self):
        """설정 저장 및 로드 테스트."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Generate and save config
            template = generate_domain_template("test_domain", languages=["ko"])
            config_path = save_domain_config("test_domain", template, config_dir)

            assert config_path.exists()
            assert config_path.name == "memory.yaml"

            # Load config
            loaded = load_domain_config("test_domain", config_dir)
            assert loaded.metadata.domain == "test_domain"
            assert loaded.metadata.supported_languages == ["ko"]

    def test_load_nonexistent_config(self):
        """존재하지 않는 설정 로드 시 에러."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            with pytest.raises(FileNotFoundError):
                load_domain_config("nonexistent", config_dir)

    def test_save_domain_memory_config_object(self):
        """DomainMemoryConfig 객체 저장 테스트."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            config = DomainMemoryConfig(
                metadata=DomainMetadata(domain="test", version="2.0.0"),
                learning=LearningConfig(enabled=False),
            )
            save_domain_config("test", config, config_dir)

            loaded = load_domain_config("test", config_dir)
            assert loaded.metadata.version == "2.0.0"
            assert loaded.learning.enabled is False

    def test_load_flat_format_yaml(self):
        """플랫 형식 YAML 로드 테스트 (metadata 키 없는 형식)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            domain_dir = config_dir / "test_flat"
            domain_dir.mkdir(parents=True)

            # Create flat format YAML (without nested metadata)
            flat_config = {
                "domain": "test_flat",
                "version": "1.0.0",
                "supported_languages": ["ko"],
                "default_language": "ko",
                "description": "Flat format test",
                "factual": {
                    "glossary": {"ko": "terms_ko.json"},
                },
                "learning": {"enabled": True},
            }

            config_path = domain_dir / "memory.yaml"
            with open(config_path, "w") as f:
                yaml.dump(flat_config, f)

            loaded = load_domain_config("test_flat", config_dir)
            assert loaded.metadata.domain == "test_flat"
            assert loaded.metadata.description == "Flat format test"


class TestListDomains:
    """Tests for list_domains function."""

    def test_list_domains_empty(self):
        """빈 디렉토리 테스트."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            domains = list_domains(config_dir)
            assert domains == []

    def test_list_domains_multiple(self):
        """여러 도메인 목록 테스트."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create multiple domains
            for domain_name in ["insurance", "medical", "legal"]:
                template = generate_domain_template(domain_name)
                save_domain_config(domain_name, template, config_dir)

            domains = list_domains(config_dir)
            assert len(domains) == 3
            assert "insurance" in domains
            assert "medical" in domains
            assert "legal" in domains

    def test_list_domains_ignores_invalid(self):
        """유효하지 않은 디렉토리 무시 테스트."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create valid domain
            template = generate_domain_template("valid")
            save_domain_config("valid", template, config_dir)

            # Create directory without memory.yaml
            invalid_dir = config_dir / "invalid"
            invalid_dir.mkdir()

            # Create file (not directory)
            (config_dir / "not_a_dir.txt").write_text("test")

            domains = list_domains(config_dir)
            assert domains == ["valid"]


class TestYAMLSerializationRoundtrip:
    """Tests for YAML serialization roundtrip."""

    def test_full_config_roundtrip(self):
        """전체 설정 직렬화/역직렬화 테스트."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            original = DomainMemoryConfig(
                metadata=DomainMetadata(
                    domain="insurance",
                    version="1.5.0",
                    supported_languages=["ko", "en"],
                    default_language="ko",
                    description="보험 도메인 메모리 설정",
                ),
                factual=FactualConfig(
                    glossary=LanguageConfig(ko="terms_ko.json", en="terms_en.json"),
                    regulatory_rules=LanguageConfig(ko="rules_ko.md"),
                    shared={"companies": "companies.json"},
                ),
                experiential=ExperientialConfig(
                    reliability_scores=LanguageConfig(ko="reliability_ko.json"),
                    failure_modes="failures.json",
                    behavior_handbook="behaviors.json",
                ),
                working=WorkingConfig(
                    run_cache="${RUN_DIR}/memory.db",
                    kg_binding="kg://insurance",
                    max_cache_size_mb=150,
                ),
                learning=LearningConfig(
                    enabled=True,
                    min_confidence_to_store=0.7,
                    behavior_extraction=True,
                    auto_apply=False,
                    decay_rate=0.9,
                    forget_threshold_days=60,
                ),
            )

            save_domain_config("insurance", original, config_dir)
            loaded = load_domain_config("insurance", config_dir)

            assert loaded.metadata.domain == original.metadata.domain
            assert loaded.metadata.version == original.metadata.version
            assert loaded.metadata.description == original.metadata.description
            assert loaded.factual.glossary.ko == original.factual.glossary.ko
            assert loaded.factual.shared == original.factual.shared
            assert loaded.working.kg_binding == original.working.kg_binding
            assert loaded.learning.auto_apply == original.learning.auto_apply
            assert loaded.learning.decay_rate == original.learning.decay_rate


class TestTermsDictionaryFormat:
    """Tests for terms dictionary JSON format."""

    def test_terms_dictionary_structure(self):
        """용어사전 JSON 구조 테스트."""
        terms_dict = {
            "version": "1.0.0",
            "language": "ko",
            "domain": "insurance",
            "description": "보험 도메인 한국어 용어 사전",
            "terms": {
                "보험료": {
                    "definition": "보험계약에 따라 계약자가 납입하는 금액",
                    "aliases": ["보험 요금", "월 보험료"],
                    "category": "payment",
                    "importance": "high",
                },
            },
            "categories": {
                "payment": "납입 관련",
            },
        }

        # Verify structure
        assert terms_dict["version"] == "1.0.0"
        assert terms_dict["language"] == "ko"
        assert "보험료" in terms_dict["terms"]
        assert terms_dict["terms"]["보험료"]["category"] == "payment"

    def test_terms_dictionary_roundtrip(self):
        """용어사전 JSON 직렬화/역직렬화."""
        # Create temp file, write, then close before reading (Windows compatibility)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            terms_dict = {
                "version": "1.0.0",
                "language": "ko",
                "domain": "test",
                "terms": {
                    "테스트용어": {
                        "definition": "테스트를 위한 용어",
                        "aliases": ["테스트"],
                        "category": "test",
                    },
                },
                "categories": {"test": "테스트"},
            }
            json.dump(terms_dict, f, ensure_ascii=False, indent=2)
            temp_path = f.name

        # File is now closed, safe to read on Windows
        try:
            with open(temp_path, encoding="utf-8") as rf:
                loaded = json.load(rf)
            assert loaded["terms"]["테스트용어"]["definition"] == "테스트를 위한 용어"
        finally:
            Path(temp_path).unlink()
