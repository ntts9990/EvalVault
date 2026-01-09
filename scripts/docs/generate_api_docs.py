#!/usr/bin/env python3
"""Generate interactive API documentation for the EvalVault project.

이 스크립트는 프로젝트의 모든 클래스/함수에 대해
입력(파라미터/의존성) → 출력(리턴/예외/부작용/산출물) 데이터 형태를
전수조사하여 인터랙티브 웹 보고서로 생성합니다.

버전 관리:
- 각 실행마다 타임스탬프 기반 버전 폴더 생성
- latest 심볼릭 링크로 최신 버전 접근
- 버전 인덱스 페이지에서 모든 버전 확인

Usage:
    python scripts/docs/generate_api_docs.py
    python scripts/docs/generate_api_docs.py --src src/evalvault --out reports/api-docs
    python scripts/docs/generate_api_docs.py --include-private --include-dunder
    python scripts/docs/generate_api_docs.py --no-versioning  # 버전 관리 없이 덮어쓰기
"""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 스크립트 직접 실행을 위한 경로 설정
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.docs.analyzer.ast_scanner import ASTScanner, ScanConfig
from scripts.docs.analyzer.confidence_scorer import ConfidenceScorer
from scripts.docs.analyzer.graph_builder import GraphBuilder
from scripts.docs.analyzer.side_effect_detector import SideEffectDetector
from scripts.docs.models.schema import ProjectAnalysis
from scripts.docs.renderer.html_generator import HTMLGenerator


def parse_args() -> argparse.Namespace:
    """커맨드라인 인자 파싱."""
    parser = argparse.ArgumentParser(
        description="프로젝트 API 문서 생성기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
    # 기본 실행 (src/evalvault 스캔)
    python scripts/docs/generate_api_docs.py

    # 커스텀 경로
    python scripts/docs/generate_api_docs.py --src src/evalvault --out docs/api

    # private 심볼 포함
    python scripts/docs/generate_api_docs.py --include-private

    # JSON만 생성 (HTML 없이)
    python scripts/docs/generate_api_docs.py --json-only
""",
    )

    parser.add_argument(
        "--src",
        type=Path,
        default=Path("src/evalvault"),
        help="스캔할 소스 디렉토리 (기본: src/evalvault)",
    )

    parser.add_argument(
        "--out",
        type=Path,
        default=Path("reports/api-docs"),
        help="출력 디렉토리 (기본: reports/api-docs)",
    )

    parser.add_argument(
        "--project-name",
        type=str,
        default="EvalVault",
        help="프로젝트 이름 (기본: EvalVault)",
    )

    parser.add_argument(
        "--include-private",
        action="store_true",
        default=True,
        help="private 심볼(_로 시작) 포함 (기본: True)",
    )

    parser.add_argument(
        "--exclude-private",
        action="store_true",
        help="private 심볼 제외",
    )

    parser.add_argument(
        "--include-dunder",
        action="store_true",
        help="dunder 메서드(__name__) 포함",
    )

    parser.add_argument(
        "--exclude-patterns",
        type=str,
        nargs="*",
        default=["test_*", "*_test.py", "conftest.py"],
        help="제외할 파일 패턴들",
    )

    parser.add_argument(
        "--json-only",
        action="store_true",
        help="JSON 데이터만 생성 (HTML 스킵)",
    )

    parser.add_argument(
        "--no-versioning",
        action="store_true",
        help="버전 관리 없이 덮어쓰기 (기본: 버전별 폴더 생성)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="상세 출력",
    )

    return parser.parse_args()


def analyze_project(
    src_path: Path,
    project_name: str,
    config: ScanConfig,
    exclude_patterns: list[str],
    verbose: bool = False,
) -> ProjectAnalysis:
    """프로젝트 분석 수행.

    Args:
        src_path: 소스 디렉토리 경로
        project_name: 프로젝트 이름
        config: 스캔 설정
        exclude_patterns: 제외 패턴들
        verbose: 상세 출력 여부

    Returns:
        프로젝트 분석 결과
    """
    if verbose:
        print(f"📂 소스 디렉토리 스캔 중: {src_path}")

    # 1. AST 스캔
    scanner = ASTScanner(config)
    modules = scanner.scan_directory(src_path, exclude_patterns)

    if verbose:
        print(f"   → {len(modules)}개 모듈 발견")

    # 2. 부작용 탐지
    side_effect_detector = SideEffectDetector()
    for module in modules:
        for func in module.functions:
            # 소스 파일을 다시 읽어서 부작용 탐지 (간단한 구현)
            try:
                source = Path(module.file_path).read_text(encoding="utf-8")
                import ast

                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if (
                        isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
                        and node.name == func.name
                    ):
                        side_effects = side_effect_detector.detect_in_function(node)
                        func.io.side_effects.extend(side_effects)
                        break
            except Exception:
                pass

        for cls in module.classes:
            for method in cls.methods:
                try:
                    source = Path(module.file_path).read_text(encoding="utf-8")
                    import ast

                    tree = ast.parse(source)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef) and node.name == cls.name:
                            for child in node.body:
                                if (
                                    isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef)
                                    and child.name == method.name
                                ):
                                    side_effects = side_effect_detector.detect_in_function(child)
                                    method.io.side_effects.extend(side_effects)
                                    break
                except Exception:
                    pass

    if verbose:
        print("   → 부작용 탐지 완료")

    # 3. 확신도 계산
    confidence_scorer = ConfidenceScorer()
    all_stats: dict[str, float] = {
        "total": 0,
        "high_ratio": 0,
        "medium_ratio": 0,
        "low_ratio": 0,
        "unknown_ratio": 0,
    }

    for module in modules:
        stats = confidence_scorer.score_module(module)
        if stats["total"] > 0:
            weight = stats["total"]
            for key in ["high_ratio", "medium_ratio", "low_ratio", "unknown_ratio"]:
                all_stats[key] = (all_stats[key] * all_stats["total"] + stats[key] * weight) / (
                    all_stats["total"] + weight
                )
            all_stats["total"] += weight

    if verbose:
        print(f"   → 타입 커버리지: High {all_stats['high_ratio'] * 100:.1f}%")

    # 4. 그래프 빌드
    graph_builder = GraphBuilder()
    type_graph = graph_builder.build_type_graph(modules)

    if verbose:
        print(f"   → 타입 그래프: {len(type_graph.nodes)}개 노드, {len(type_graph.edges)}개 엣지")

    # 5. 결과 조합
    analysis = ProjectAnalysis(
        project_name=project_name,
        analyzed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        version="1.0.0",
        modules=modules,
        type_graph=type_graph,
        statistics=all_stats,
    )

    return analysis


def generate_report(
    analysis: ProjectAnalysis,
    output_dir: Path,
    json_only: bool,
    verbose: bool,
    versioning: bool = True,
) -> Path:
    """보고서 생성.

    Args:
        analysis: 분석 결과
        output_dir: 출력 디렉토리
        json_only: JSON만 생성 여부
        verbose: 상세 출력 여부
        versioning: 버전 관리 여부

    Returns:
        실제 출력된 디렉토리 경로
    """
    if versioning:
        # 타임스탬프 기반 버전 폴더 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_dir = output_dir / f"v_{timestamp}"
        version_dir.mkdir(parents=True, exist_ok=True)
        actual_output = version_dir

        # latest 심볼릭 링크 업데이트
        latest_link = output_dir / "latest"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        with contextlib.suppress(OSError):
            latest_link.symlink_to(version_dir.name)

        if verbose:
            print(f"\n📝 보고서 생성 중: {version_dir}")
            print(f"   버전: {timestamp}")
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
        actual_output = output_dir
        if verbose:
            print(f"\n📝 보고서 생성 중: {output_dir}")

    if json_only:
        # JSON만 생성
        json_path = actual_output / "analysis.json"
        from dataclasses import fields, is_dataclass
        from enum import Enum

        def serialize(obj: Any, seen: set | None = None) -> Any:
            if seen is None:
                seen = set()

            obj_id = id(obj)
            if obj_id in seen:
                return None

            if is_dataclass(obj) and not isinstance(obj, type):
                seen.add(obj_id)
                result = {}
                for f in fields(obj):
                    value = getattr(obj, f.name)
                    result[f.name] = serialize(value, seen)
                return result
            elif isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, list):
                return [serialize(item, seen) for item in obj]
            elif isinstance(obj, dict):
                return {k: serialize(v, seen) for k, v in obj.items()}
            elif isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            elif hasattr(obj, "__dict__"):
                seen.add(obj_id)
                return {
                    k: serialize(v, seen) for k, v in obj.__dict__.items() if not k.startswith("_")
                }
            return str(obj)

        data = serialize(analysis)
        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ JSON 생성 완료: {json_path}")
    else:
        # HTML 보고서 생성
        generator = HTMLGenerator(actual_output)
        index_path = generator.generate(analysis)
        print(f"✅ HTML 보고서 생성 완료: {index_path}")

    # 버전 인덱스 페이지 생성 (버전 관리 시)
    if versioning:
        _generate_version_index(output_dir, analysis.project_name)

    return actual_output


def _generate_version_index(base_dir: Path, project_name: str) -> None:
    """버전 인덱스 페이지 생성."""
    versions = []
    for item in sorted(base_dir.iterdir(), reverse=True):
        if item.is_dir() and item.name.startswith("v_"):
            # 버전 정보 추출
            version_name = item.name
            timestamp = version_name[2:]  # v_ 제거
            try:
                dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                formatted_time = timestamp

            # 통계 정보 로드 (있으면)
            stats = {}
            data_json = item / "data.json"
            if data_json.exists():
                try:
                    data = json.loads(data_json.read_text(encoding="utf-8"))
                    stats = {
                        "modules": len(data.get("modules", [])),
                        "classes": sum(len(m.get("classes", [])) for m in data.get("modules", [])),
                        "functions": sum(
                            len(m.get("functions", [])) for m in data.get("modules", [])
                        ),
                    }
                except Exception:
                    pass

            versions.append(
                {
                    "name": version_name,
                    "path": f"{version_name}/index.html",
                    "time": formatted_time,
                    "stats": stats,
                }
            )

    # 인덱스 HTML 생성
    index_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - API 문서 버전 목록</title>
    <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-hover: #21262d;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --accent-blue: #58a6ff;
            --accent-green: #3fb950;
            --border-color: #30363d;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Pretendard', -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 2rem;
            margin-bottom: 8px;
            color: var(--accent-blue);
        }}
        .subtitle {{
            color: var(--text-secondary);
            margin-bottom: 32px;
        }}
        .version-list {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        .version-card {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            text-decoration: none;
            color: inherit;
            transition: all 0.2s;
        }}
        .version-card:hover {{
            background: var(--bg-hover);
            border-color: var(--accent-blue);
            transform: translateY(-2px);
        }}
        .version-card.latest {{
            border-color: var(--accent-green);
            position: relative;
        }}
        .version-card.latest::before {{
            content: 'LATEST';
            position: absolute;
            top: -10px;
            right: 20px;
            background: var(--accent-green);
            color: var(--bg-primary);
            padding: 2px 10px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
        }}
        .version-info h3 {{
            font-size: 1.1rem;
            margin-bottom: 4px;
        }}
        .version-info .time {{
            color: var(--text-secondary);
            font-size: 0.875rem;
        }}
        .version-stats {{
            display: flex;
            gap: 20px;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--accent-blue);
        }}
        .stat-label {{
            font-size: 0.7rem;
            color: var(--text-secondary);
        }}
        .empty {{
            text-align: center;
            padding: 60px;
            color: var(--text-secondary);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 {project_name} API 문서</h1>
        <p class="subtitle">버전별 API 문서 아카이브</p>

        <div class="version-list">
"""

    if versions:
        for i, v in enumerate(versions):
            latest_class = "latest" if i == 0 else ""
            stats_html = ""
            if v["stats"]:
                stats_html = f"""
                <div class="version-stats">
                    <div class="stat">
                        <div class="stat-value">{v["stats"].get("modules", 0)}</div>
                        <div class="stat-label">모듈</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{v["stats"].get("classes", 0)}</div>
                        <div class="stat-label">클래스</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{v["stats"].get("functions", 0)}</div>
                        <div class="stat-label">함수</div>
                    </div>
                </div>
                """

            index_html += f"""
            <a href="{v["path"]}" class="version-card {latest_class}">
                <div class="version-info">
                    <h3>{v["name"]}</h3>
                    <span class="time">{v["time"]}</span>
                </div>
                {stats_html}
            </a>
"""
    else:
        index_html += """
            <div class="empty">
                <p>아직 생성된 버전이 없습니다.</p>
            </div>
"""

    index_html += """
        </div>
    </div>
</body>
</html>
"""

    (base_dir / "index.html").write_text(index_html, encoding="utf-8")


def print_summary(analysis: ProjectAnalysis) -> None:
    """분석 결과 요약 출력."""
    print("\n" + "=" * 60)
    print(f"📊 {analysis.project_name} API 문서 분석 완료")
    print("=" * 60)

    total_classes = sum(len(m.classes) for m in analysis.modules)
    total_functions = sum(len(m.functions) for m in analysis.modules)
    total_methods = sum(sum(len(c.methods) for c in m.classes) for m in analysis.modules)

    print(f"\n📁 모듈: {len(analysis.modules)}개")
    print(f"📦 클래스: {total_classes}개")
    print(f"🔧 함수: {total_functions}개")
    print(f"⚙️  메서드: {total_methods}개")

    stats = analysis.statistics
    print("\n📈 타입 커버리지:")
    print(f"   • High: {stats.get('high_ratio', 0) * 100:.1f}%")
    print(f"   • Medium: {stats.get('medium_ratio', 0) * 100:.1f}%")
    print(f"   • Low: {stats.get('low_ratio', 0) * 100:.1f}%")
    print(f"   • Unknown: {stats.get('unknown_ratio', 0) * 100:.1f}%")

    print(
        f"\n🔗 타입 그래프: {len(analysis.type_graph.nodes)}개 노드, {len(analysis.type_graph.edges)}개 엣지"
    )

    # 레이어별 분포
    layer_counts: dict[str, int] = {}
    for module in analysis.modules:
        layer = module.layer or "other"
        layer_counts[layer] = layer_counts.get(layer, 0) + 1

    print("\n🏗️  레이어별 모듈 분포:")
    for layer, count in sorted(layer_counts.items()):
        print(f"   • {layer}: {count}개")


def main() -> None:
    """메인 함수."""
    args = parse_args()

    # 설정 구성
    include_private = args.include_private and not args.exclude_private
    config = ScanConfig(
        include_private=include_private,
        include_dunder=args.include_dunder,
        extract_docstrings=True,
        extract_raises=True,
    )

    # 소스 경로 확인
    if not args.src.exists():
        print(f"❌ 소스 디렉토리를 찾을 수 없습니다: {args.src}")
        return

    versioning = not args.no_versioning

    print(f"🚀 {args.project_name} API 문서 생성 시작...")
    print(f"   소스: {args.src}")
    print(f"   출력: {args.out}")
    print(f"   버전 관리: {'ON' if versioning else 'OFF'}")
    print(f"   Private 포함: {include_private}")
    print(f"   Dunder 포함: {args.include_dunder}")

    # 분석 수행
    analysis = analyze_project(
        src_path=args.src,
        project_name=args.project_name,
        config=config,
        exclude_patterns=args.exclude_patterns,
        verbose=args.verbose,
    )

    # 보고서 생성
    actual_output = generate_report(
        analysis, args.out, args.json_only, args.verbose, versioning=versioning
    )

    # 요약 출력
    print_summary(analysis)

    if versioning:
        print("\n🎉 완료!")
        print(f"   📁 버전 목록: {args.out / 'index.html'}")
        print(f"   📄 최신 버전: {actual_output / 'index.html'}")
        print(f"   🔗 latest 링크: {args.out / 'latest' / 'index.html'}")
    else:
        print(f"\n🎉 완료! 브라우저에서 열기: {args.out / 'index.html'}")


if __name__ == "__main__":
    main()
