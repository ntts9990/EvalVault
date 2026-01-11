#!/usr/bin/env python3
"""
EvalVault 개발 백서 생성 도구

모든 섹션 파일들을 통합하여 완전한 백서를 생성합니다.
"""

from pathlib import Path

# 백서 섹션 파일 순서
SECTIONS = [
    "00-frontmatter.md",
    "01-project-overview.md",
    "02-architecture.md",
    "03-data-flow.md",
    # 추가 섹션들이 계속 추가될 것입니다
]

WHITEPAPER_DIR = Path(__file__).parent.parent / "whitepaper"
WHITEPAPER_OUTPUT = Path(__file__).parent.parent.parent / "WHITEPAPER.md"


def generate_whitepaper():
    """섹션 파일들을 통합하여 완전한 백서 생성"""

    # 섹션 파일들을 읽기
    sections = []
    for section_file in SECTIONS:
        section_path = WHITEPAPER_DIR / section_file

        if not section_path.exists():
            print(f"⚠️  섹션 파일을 찾을 수 없음: {section_path}")
            continue

        with open(section_path, encoding="utf-8") as f:
            content = f.read()
            sections.append(content)

        print(f"✅ 섹션 로드 완료: {section_file}")

    # 섹션들을 합치기
    full_paper = "\n\n".join(sections)

    # 완전한 백서 생성
    WHITEPAPER_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with open(WHITEPAPER_OUTPUT, "w", encoding="utf-8") as f:
        f.write(full_paper)

    print(f"\n✅ 백서 생성 완료: {WHITEPAPER_OUTPUT}")
    print(f"   총 라인 수: {len(full_paper.splitlines())}")
    print(f"   총 단어 수: {len(full_paper.split())}")


def generate_stats():
    """백서 통계 생성"""

    if not WHITEPAPER_OUTPUT.exists():
        print(f"⚠️  백서 파일을 찾을 수 없음: {WHITEPAPER_OUTPUT}")
        print("먼저 백서를 생성해주세요.")
        return

    with open(WHITEPAPER_OUTPUT, encoding="utf-8") as f:
        content = f.read()

    import re

    stats = {
        "총 라인 수": len(content.splitlines()),
        "총 단어 수": len(content.split()),
        "총 문자 수": len(content),
        "섹션 수": len(re.findall(r"^##\s+", content, re.MULTILINE)),
        "코드 블록 수": len(re.findall(r"```", content)) // 2,
        "표 수": len(re.findall(r"\|.*\|", content)),
    }

    print("\n📊 백서 통계:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


def validate_links():
    """백서 링크 유효성 검증"""

    if not WHITEPAPER_OUTPUT.exists():
        print(f"⚠️  백서 파일을 찾을 수 없음: {WHITEPAPER_OUTPUT}")
        return

    with open(WHITEPAPER_OUTPUT, encoding="utf-8") as f:
        content = f.read()

    import re

    # 마크다운 링크 추출
    link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    links = re.findall(link_pattern, content)

    print(f"\n🔍 발견된 링크: {len(links)}개")

    # 외부 링크와 내부 링크 구분
    external_links = []
    internal_links = []

    for text, url in links:
        if url.startswith("http"):
            external_links.append((text, url))
        else:
            internal_links.append((text, url))

    print(f"  외부 링크: {len(external_links)}개")
    print(f"  내부 링크: {len(internal_links)}개")

    # 잠재적인 문제 링크
    problematic_links = []
    for text, url in internal_links:
        # 섹션 참조 형식 확인 (예: 섹션 X.Y)
        if not re.match(r"section\s+\d+\.\d+", url, re.IGNORECASE):
            problematic_links.append((text, url))

    if problematic_links:
        print(f"\n⚠️  잠재적인 문제 링크 ({len(problematic_links)}개):")
        for text, url in problematic_links:
            print(f"  - [{text}]({url})")


def check_sections():
    """섹션 파일 존재 여부 확인"""

    print("📋 섹션 파일 확인:")

    missing_sections = []
    existing_sections = []

    for section_file in SECTIONS:
        section_path = WHITEPAPER_DIR / section_file

        if section_path.exists():
            existing_sections.append(section_file)
            print(f"  ✅ {section_file}")
        else:
            missing_sections.append(section_file)
            print(f"  ❌ {section_file}")

    print(f"\n존재하는 섹션: {len(existing_sections)}개")
    print(f"누락된 섹션: {len(missing_sections)}개")

    if missing_sections:
        print("\n⚠️  누락된 섹션이 있습니다:")
        for section_file in missing_sections:
            print(f"  - {section_file}")


def main():
    """메인 함수"""

    import argparse

    parser = argparse.ArgumentParser(description="EvalVault 개발 백서 생성 도구")
    parser.add_argument(
        "--stats",
        action="store_true",
        help="백서 통계 생성",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="백서 링크 유효성 검증",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="섹션 파일 존재 여부 확인",
    )

    args = parser.parse_args()

    # 섹션 파일 확인
    if args.check or not any([args.stats, args.validate]):
        check_sections()

    # 백서 생성
    if not any([args.stats, args.validate]):
        generate_whitepaper()

    # 통계 생성
    if args.stats:
        generate_stats()

    # 링크 검증
    if args.validate:
        validate_links()


if __name__ == "__main__":
    main()
