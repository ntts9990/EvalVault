"""Interactive HTML report generator.

인터랙티브 웹 보고서를 생성합니다.
- 검색/필터/드릴다운
- 타입 그래프 시각화
- 점진적 공개(Progressive Disclosure)
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.docs.models.schema import (
    ProjectAnalysis,
)


class HTMLGenerator:
    """HTML 보고서 생성기."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, analysis: ProjectAnalysis) -> Path:
        """보고서 생성.

        Args:
            analysis: 프로젝트 분석 결과

        Returns:
            생성된 index.html 경로
        """
        # JSON 데이터 생성 (별도 파일 + 인라인 둘 다)
        data_json = self._serialize_analysis(analysis)

        data_path = self.output_dir / "data.json"
        data_path.write_text(data_json, encoding="utf-8")

        # HTML 생성 (데이터 인라인 포함)
        index_path = self.output_dir / "index.html"
        self._write_index_html(analysis, index_path, data_json)

        # CSS 생성
        styles_path = self.output_dir / "styles.css"
        self._write_styles_css(styles_path)

        # JavaScript 생성
        app_path = self.output_dir / "app.js"
        self._write_app_js(app_path)

        return index_path

    def _serialize_analysis(self, analysis: ProjectAnalysis) -> str:
        """분석 결과를 JSON 문자열로 직렬화."""
        from dataclasses import fields, is_dataclass
        from enum import Enum

        def serialize(obj, seen=None):
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
        return json.dumps(data, ensure_ascii=False)

    def _write_index_html(self, analysis: ProjectAnalysis, path: Path, data_json: str) -> None:
        """메인 HTML 파일 생성."""
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{analysis.project_name} - API Documentation</title>
    <link rel="stylesheet" href="styles.css">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Pretendard:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="app-container">
        <!-- 사이드바 -->
        <aside class="sidebar">
            <div class="sidebar-header">
                <h1 class="logo">{analysis.project_name}</h1>
                <span class="version">API Docs v{analysis.version}</span>
            </div>

            <!-- 메인 네비게이션 버튼 -->
            <div class="main-nav">
                <button class="nav-btn active" onclick="showDashboard()" id="nav-dashboard">
                    <span class="nav-btn-icon">📊</span>
                    <span>대시보드</span>
                </button>
                <button class="nav-btn" onclick="showGraphView()" id="nav-graph">
                    <span class="nav-btn-icon">🔗</span>
                    <span>그래프</span>
                </button>
                <a href="../index.html" class="nav-btn" id="nav-versions">
                    <span class="nav-btn-icon">📚</span>
                    <span>버전 목록</span>
                </a>
            </div>

            <div class="search-container">
                <input type="text" id="search-input" placeholder="검색... (Ctrl+K)" autocomplete="off">
                <div id="search-results" class="search-results hidden"></div>
            </div>

            <nav class="nav-tree" id="nav-tree">
                <!-- 동적으로 생성됨 -->
            </nav>

            <div class="sidebar-footer">
                <div class="stats">
                    <div class="stat">
                        <span class="stat-value" id="stat-modules">0</span>
                        <span class="stat-label">모듈</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value" id="stat-classes">0</span>
                        <span class="stat-label">클래스</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value" id="stat-functions">0</span>
                        <span class="stat-label">함수</span>
                    </div>
                </div>
                <div class="generated-at">
                    생성: {analysis.analyzed_at}
                </div>
            </div>
        </aside>

        <!-- 메인 컨텐츠 -->
        <main class="main-content">
            <!-- 대시보드 (기본 뷰) -->
            <section id="dashboard" class="view active">
                <header class="view-header">
                    <h2>📊 대시보드</h2>
                    <p class="view-description">프로젝트 API 전체 현황</p>
                </header>

                <div class="dashboard-grid">
                    <div class="card coverage-card">
                        <h3>타입 커버리지</h3>
                        <div class="coverage-chart" id="coverage-chart">
                            <!-- 동적으로 생성됨 -->
                        </div>
                    </div>

                    <div class="card layer-card">
                        <h3>레이어별 분포</h3>
                        <div class="layer-bars" id="layer-bars">
                            <!-- 동적으로 생성됨 -->
                        </div>
                    </div>

                    <div class="card issues-card">
                        <h3>⚠️ 주의 필요</h3>
                        <ul id="issues-list" class="issues-list">
                            <!-- 동적으로 생성됨 -->
                        </ul>
                    </div>

                    <div class="card quick-access-card">
                        <h3>빠른 접근</h3>
                        <div id="quick-access" class="quick-access-grid">
                            <!-- 동적으로 생성됨 -->
                        </div>
                    </div>
                </div>
            </section>

            <!-- 심볼 상세 뷰 -->
            <section id="symbol-detail" class="view">
                <header class="view-header">
                    <button class="back-btn" onclick="showDashboard()">← 뒤로</button>
                    <div class="symbol-header-content">
                        <h2 id="symbol-name">-</h2>
                        <span id="symbol-type" class="badge">-</span>
                        <span id="symbol-confidence" class="confidence-badge">-</span>
                    </div>
                </header>

                <div class="symbol-content">
                    <div class="symbol-meta" id="symbol-meta">
                        <!-- 동적으로 생성됨 -->
                    </div>

                    <div class="symbol-sections">
                        <!-- 시그니처 -->
                        <div class="section signature-section">
                            <h3>📝 시그니처</h3>
                            <pre id="symbol-signature" class="code-block"></pre>
                        </div>

                        <!-- 입력 -->
                        <div class="section inputs-section">
                            <h3>📥 입력 (Parameters)</h3>
                            <table id="symbol-inputs" class="io-table">
                                <thead>
                                    <tr>
                                        <th>이름</th>
                                        <th>타입</th>
                                        <th>기본값</th>
                                        <th>설명</th>
                                        <th>확신도</th>
                                    </tr>
                                </thead>
                                <tbody></tbody>
                            </table>
                        </div>

                        <!-- 출력 -->
                        <div class="section output-section">
                            <h3>📤 출력 (Returns)</h3>
                            <div id="symbol-output" class="output-box"></div>
                        </div>

                        <!-- 예외 -->
                        <div class="section raises-section">
                            <h3>⚠️ 예외 (Raises)</h3>
                            <ul id="symbol-raises" class="raises-list"></ul>
                        </div>

                        <!-- 부작용 -->
                        <div class="section side-effects-section">
                            <h3>💥 부작용 (Side Effects)</h3>
                            <ul id="symbol-side-effects" class="side-effects-list"></ul>
                        </div>

                        <!-- 문서 -->
                        <div class="section docstring-section">
                            <h3>📖 문서</h3>
                            <pre id="symbol-docstring" class="docstring-block"></pre>
                        </div>
                    </div>
                </div>
            </section>

            <!-- 그래프 뷰 -->
            <section id="graph-view" class="view">
                <header class="view-header">
                    <div class="view-header-left">
                        <button class="back-btn" onclick="showDashboard()">← 대시보드</button>
                        <h2>🔗 타입/의존성 그래프</h2>
                        <p class="view-description">클래스, 함수, 타입 간의 관계를 시각화합니다. 노드를 클릭하면 상세 정보를 볼 수 있습니다.</p>
                    </div>
                    <div class="graph-controls">
                        <div class="control-group">
                            <label>레이어 필터</label>
                            <select id="graph-filter" onchange="filterGraph(this.value)">
                                <option value="all">전체</option>
                                <option value="domain">Domain</option>
                                <option value="ports">Ports</option>
                                <option value="adapters">Adapters</option>
                            </select>
                        </div>
                        <div class="control-group">
                            <label>줌</label>
                            <button class="btn-sm" onclick="zoomGraph(-0.2)">−</button>
                            <button class="btn-sm" onclick="zoomGraph(0.2)">+</button>
                        </div>
                        <button class="btn" onclick="resetGraph()">리셋</button>
                    </div>
                </header>
                <div class="graph-info-bar">
                    <span id="graph-stats">노드: 0 / 엣지: 0</span>
                    <span class="graph-hint">💡 G 키: 그래프 뷰 전환 | 노드 클릭: 상세 보기 | 마우스 호버: 정보 표시</span>
                </div>
                <div class="graph-container">
                    <svg id="graph-svg" width="100%" height="600"></svg>
                </div>
                <div id="graph-tooltip" class="tooltip hidden"></div>
            </section>
        </main>
    </div>

    <script id="analysis-data" type="application/json">
__DATA_PLACEHOLDER__
    </script>
    <script src="app.js"></script>
</body>
</html>
"""
        # HTML 내부에서 안전하게 사용하기 위해 이스케이프
        escaped_data_json = data_json.replace("</", "<\\/").replace("<!--", "<\\!--")
        html = html.replace("__DATA_PLACEHOLDER__", escaped_data_json)
        path.write_text(html, encoding="utf-8")

    def _write_styles_css(self, path: Path) -> None:
        """CSS 스타일 파일 생성."""
        css = """/* === Variables === */
:root {
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-tertiary: #21262d;
    --bg-hover: #30363d;

    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
    --text-muted: #6e7681;

    --accent-blue: #58a6ff;
    --accent-green: #3fb950;
    --accent-orange: #d29922;
    --accent-red: #f85149;
    --accent-purple: #a371f7;
    --accent-pink: #db61a2;

    --border-color: #30363d;
    --border-radius: 8px;

    --font-sans: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

    --sidebar-width: 300px;
    --header-height: 60px;

    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
    --shadow-lg: 0 10px 20px rgba(0, 0, 0, 0.5);
}

/* === Reset === */
*, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

/* === Base === */
html {
    font-size: 14px;
}

body {
    font-family: var(--font-sans);
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    overflow: hidden;
}

/* === Layout === */
.app-container {
    display: flex;
    height: 100vh;
}

/* === Sidebar === */
.sidebar {
    width: var(--sidebar-width);
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    height: 100vh;
}

.sidebar-header {
    padding: 20px;
    border-bottom: 1px solid var(--border-color);
}

.logo {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--accent-blue);
    margin-bottom: 4px;
}

.version {
    font-size: 0.75rem;
    color: var(--text-muted);
}

/* === Main Navigation === */
.main-nav {
    display: flex;
    gap: 8px;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-color);
}

.nav-btn {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 10px 8px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    color: var(--text-secondary);
    font-size: 0.7rem;
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
}

.nav-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
    border-color: var(--accent-blue);
}

.nav-btn.active {
    background: rgba(88, 166, 255, 0.15);
    color: var(--accent-blue);
    border-color: var(--accent-blue);
}

.nav-btn-icon {
    font-size: 1.25rem;
}

/* === Search === */
.search-container {
    padding: 12px 16px;
    position: relative;
}

#search-input {
    width: 100%;
    padding: 10px 14px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    color: var(--text-primary);
    font-size: 0.875rem;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
}

#search-input:focus {
    border-color: var(--accent-blue);
    box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.2);
}

#search-input::placeholder {
    color: var(--text-muted);
}

.search-results {
    position: absolute;
    top: 100%;
    left: 16px;
    right: 16px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    max-height: 400px;
    overflow-y: auto;
    z-index: 100;
    box-shadow: var(--shadow-lg);
}

.search-results.hidden {
    display: none;
}

.search-result-item {
    padding: 10px 14px;
    cursor: pointer;
    border-bottom: 1px solid var(--border-color);
    transition: background 0.15s;
}

.search-result-item:hover {
    background: var(--bg-hover);
}

.search-result-item:last-child {
    border-bottom: none;
}

.search-result-name {
    font-family: var(--font-mono);
    font-size: 0.875rem;
    color: var(--accent-blue);
}

.search-result-path {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 2px;
}

/* === Navigation Tree === */
.nav-tree {
    flex: 1;
    overflow-y: auto;
    padding: 12px 0;
}

.nav-layer {
    margin-bottom: 8px;
}

.nav-layer-header {
    padding: 8px 16px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
}

.nav-module {
    cursor: pointer;
}

.nav-module-header {
    display: flex;
    align-items: center;
    padding: 6px 16px;
    gap: 8px;
    transition: background 0.15s;
}

.nav-module-header:hover {
    background: var(--bg-hover);
}

.nav-module-icon {
    font-size: 0.875rem;
    transition: transform 0.2s;
}

.nav-module.expanded .nav-module-icon {
    transform: rotate(90deg);
}

.nav-module-name {
    font-size: 0.875rem;
    color: var(--text-secondary);
}

.nav-module-children {
    display: none;
    padding-left: 24px;
}

.nav-module.expanded .nav-module-children {
    display: block;
}

.nav-item {
    display: flex;
    align-items: center;
    padding: 5px 16px;
    gap: 8px;
    cursor: pointer;
    font-size: 0.8125rem;
    color: var(--text-secondary);
    transition: background 0.15s, color 0.15s;
}

.nav-item:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
}

.nav-item.active {
    background: rgba(88, 166, 255, 0.15);
    color: var(--accent-blue);
}

.nav-item-icon {
    font-size: 0.75rem;
}

.nav-item-icon.class { color: var(--accent-orange); }
.nav-item-icon.function { color: var(--accent-purple); }
.nav-item-icon.method { color: var(--accent-green); }

/* === Sidebar Footer === */
.sidebar-footer {
    padding: 16px;
    border-top: 1px solid var(--border-color);
    background: var(--bg-tertiary);
}

.stats {
    display: flex;
    justify-content: space-around;
    margin-bottom: 12px;
}

.stat {
    text-align: center;
}

.stat-value {
    display: block;
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--accent-blue);
}

.stat-label {
    font-size: 0.7rem;
    color: var(--text-muted);
}

.generated-at {
    font-size: 0.7rem;
    color: var(--text-muted);
    text-align: center;
}

/* === Main Content === */
.main-content {
    flex: 1;
    overflow-y: auto;
    padding: 24px 32px;
}

/* === Views === */
.view {
    display: none;
}

.view.active {
    display: block;
}

.view-header {
    margin-bottom: 24px;
}

.view-header h2 {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 4px;
}

.view-description {
    color: var(--text-secondary);
    font-size: 0.875rem;
}

/* === Dashboard === */
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
}

.card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    padding: 20px;
}

.card h3 {
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: 16px;
    color: var(--text-secondary);
}

/* Coverage Chart */
.coverage-chart {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.coverage-bar {
    display: flex;
    align-items: center;
    gap: 12px;
}

.coverage-label {
    width: 80px;
    font-size: 0.75rem;
    color: var(--text-secondary);
}

.coverage-track {
    flex: 1;
    height: 8px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    overflow: hidden;
}

.coverage-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease-out;
}

.coverage-fill.high { background: var(--accent-green); }
.coverage-fill.medium { background: var(--accent-orange); }
.coverage-fill.low { background: var(--accent-red); }

.coverage-value {
    width: 50px;
    font-size: 0.75rem;
    font-weight: 500;
    text-align: right;
}

/* Layer Bars */
.layer-bars {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.layer-bar {
    display: flex;
    align-items: center;
    gap: 12px;
}

.layer-name {
    width: 80px;
    font-size: 0.75rem;
    color: var(--text-secondary);
}

.layer-bar-track {
    flex: 1;
    height: 24px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    overflow: hidden;
}

.layer-bar-fill {
    height: 100%;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-right: 8px;
    font-size: 0.7rem;
    font-weight: 500;
    transition: width 0.5s ease-out;
}

.layer-bar-fill.domain { background: linear-gradient(90deg, #3fb950, #2ea043); }
.layer-bar-fill.ports { background: linear-gradient(90deg, #58a6ff, #388bfd); }
.layer-bar-fill.adapters { background: linear-gradient(90deg, #a371f7, #8957e5); }
.layer-bar-fill.other { background: linear-gradient(90deg, #6e7681, #484f58); }

/* Issues List */
.issues-list {
    list-style: none;
    max-height: 200px;
    overflow-y: auto;
}

.issue-item {
    padding: 8px 12px;
    margin-bottom: 8px;
    background: rgba(248, 81, 73, 0.1);
    border-left: 3px solid var(--accent-red);
    border-radius: 0 4px 4px 0;
    font-size: 0.8125rem;
    cursor: pointer;
    transition: background 0.15s;
}

.issue-item:hover {
    background: rgba(248, 81, 73, 0.2);
}

.issue-item.warning {
    background: rgba(210, 153, 34, 0.1);
    border-left-color: var(--accent-orange);
}

.issue-item.warning:hover {
    background: rgba(210, 153, 34, 0.2);
}

/* Quick Access */
.quick-access-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
}

.quick-access-item {
    padding: 12px;
    background: var(--bg-tertiary);
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.15s, transform 0.15s;
}

.quick-access-item:hover {
    background: var(--bg-hover);
    transform: translateY(-2px);
}

.quick-access-icon {
    font-size: 1.25rem;
    margin-bottom: 4px;
}

.quick-access-name {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-primary);
}

.quick-access-type {
    font-size: 0.65rem;
    color: var(--text-muted);
}

/* === Symbol Detail === */
.back-btn {
    background: none;
    border: none;
    color: var(--accent-blue);
    font-size: 0.875rem;
    cursor: pointer;
    padding: 4px 0;
    margin-bottom: 8px;
}

.back-btn:hover {
    text-decoration: underline;
}

.symbol-header-content {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.badge {
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 500;
    text-transform: uppercase;
}

.badge.class { background: rgba(210, 153, 34, 0.2); color: var(--accent-orange); }
.badge.function { background: rgba(163, 113, 247, 0.2); color: var(--accent-purple); }
.badge.method { background: rgba(63, 185, 80, 0.2); color: var(--accent-green); }

.confidence-badge {
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 500;
}

.confidence-badge.high { background: rgba(63, 185, 80, 0.2); color: var(--accent-green); }
.confidence-badge.medium { background: rgba(210, 153, 34, 0.2); color: var(--accent-orange); }
.confidence-badge.low { background: rgba(248, 81, 73, 0.2); color: var(--accent-red); }
.confidence-badge.unknown { background: rgba(110, 118, 129, 0.2); color: var(--text-muted); }

.symbol-meta {
    display: flex;
    gap: 24px;
    margin-bottom: 24px;
    padding: 16px;
    background: var(--bg-secondary);
    border-radius: var(--border-radius);
    font-size: 0.8125rem;
}

.meta-item {
    display: flex;
    align-items: center;
    gap: 6px;
}

.meta-label {
    color: var(--text-muted);
}

.meta-value {
    color: var(--text-secondary);
    font-family: var(--font-mono);
}

.meta-value a {
    color: var(--accent-blue);
    text-decoration: none;
}

.meta-value a:hover {
    text-decoration: underline;
}

/* === Sections === */
.section {
    margin-bottom: 24px;
    padding: 20px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
}

.section h3 {
    font-size: 0.9375rem;
    font-weight: 600;
    margin-bottom: 16px;
    color: var(--text-primary);
}

/* Code Block */
.code-block {
    background: var(--bg-tertiary);
    padding: 16px;
    border-radius: 6px;
    font-family: var(--font-mono);
    font-size: 0.8125rem;
    line-height: 1.5;
    overflow-x: auto;
    color: var(--text-primary);
}

/* IO Table */
.io-table {
    width: 100%;
    border-collapse: collapse;
}

.io-table th,
.io-table td {
    padding: 10px 12px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

.io-table th {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
}

.io-table td {
    font-size: 0.8125rem;
}

.io-table .type-cell {
    font-family: var(--font-mono);
    color: var(--accent-blue);
}

.io-table .default-cell {
    font-family: var(--font-mono);
    color: var(--accent-orange);
}

/* Output Box */
.output-box {
    padding: 16px;
    background: var(--bg-tertiary);
    border-radius: 6px;
}

.output-type {
    font-family: var(--font-mono);
    font-size: 0.9375rem;
    color: var(--accent-green);
}

/* Raises/Side Effects List */
.raises-list,
.side-effects-list {
    list-style: none;
}

.raises-list li,
.side-effects-list li {
    padding: 10px 12px;
    margin-bottom: 8px;
    background: var(--bg-tertiary);
    border-radius: 6px;
    display: flex;
    align-items: center;
    gap: 12px;
}

.raises-type {
    font-family: var(--font-mono);
    color: var(--accent-red);
    font-weight: 500;
}

.side-effect-kind {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 500;
    text-transform: uppercase;
}

.side-effect-kind.file_read { background: rgba(88, 166, 255, 0.2); color: var(--accent-blue); }
.side-effect-kind.file_write { background: rgba(219, 97, 162, 0.2); color: var(--accent-pink); }
.side-effect-kind.database { background: rgba(163, 113, 247, 0.2); color: var(--accent-purple); }
.side-effect-kind.http_request { background: rgba(63, 185, 80, 0.2); color: var(--accent-green); }
.side-effect-kind.environment { background: rgba(210, 153, 34, 0.2); color: var(--accent-orange); }
.side-effect-kind.logging { background: rgba(110, 118, 129, 0.2); color: var(--text-muted); }
.side-effect-kind.subprocess { background: rgba(248, 81, 73, 0.2); color: var(--accent-red); }

/* Docstring */
.docstring-block {
    background: var(--bg-tertiary);
    padding: 16px;
    border-radius: 6px;
    font-family: var(--font-sans);
    font-size: 0.8125rem;
    line-height: 1.7;
    white-space: pre-wrap;
    color: var(--text-secondary);
}

/* === Graph View === */
.graph-controls {
    display: flex;
    gap: 12px;
    align-items: center;
}

.graph-controls select {
    padding: 8px 12px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    color: var(--text-primary);
    font-size: 0.8125rem;
}

.btn {
    padding: 8px 16px;
    background: var(--accent-blue);
    border: none;
    border-radius: 6px;
    color: white;
    font-size: 0.8125rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.15s;
}

.btn:hover {
    background: #388bfd;
}

.graph-container {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    margin-top: 16px;
}

#graph-svg {
    display: block;
}

.graph-node {
    cursor: pointer;
}

.graph-node circle {
    transition: r 0.2s, fill 0.2s;
}

.graph-node:hover circle {
    r: 12;
}

.graph-node text {
    font-family: var(--font-sans);
    font-size: 10px;
    fill: var(--text-secondary);
    pointer-events: none;
}

.graph-edge {
    stroke: var(--border-color);
    stroke-width: 1;
    fill: none;
}

.graph-edge.input { stroke: var(--accent-blue); }
.graph-edge.output { stroke: var(--accent-green); }
.graph-edge.inherits { stroke: var(--accent-orange); stroke-dasharray: 4; }
.graph-edge.raises { stroke: var(--accent-red); stroke-dasharray: 2; }

.tooltip {
    position: absolute;
    padding: 8px 12px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    font-size: 0.75rem;
    box-shadow: var(--shadow-md);
    pointer-events: none;
    z-index: 1000;
}

.tooltip.hidden {
    display: none;
}

/* === Empty States === */
.empty-state {
    text-align: center;
    padding: 40px;
    color: var(--text-muted);
}

.empty-state-icon {
    font-size: 3rem;
    margin-bottom: 16px;
}

/* === Scrollbar === */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
    background: var(--bg-hover);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--text-muted);
}

/* === Responsive === */
@media (max-width: 1024px) {
    .dashboard-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .sidebar {
        width: 100%;
        height: auto;
        max-height: 50vh;
    }

    .app-container {
        flex-direction: column;
    }
}
"""
        path.write_text(css, encoding="utf-8")

    def _write_app_js(self, path: Path) -> None:
        """JavaScript 애플리케이션 파일 생성."""
        js = """// API Documentation Interactive App

let analysisData = null;
let symbolIndex = {};

// === Initialization ===
document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    buildSymbolIndex();
    renderNavTree();
    renderDashboard();
    setupSearch();
    setupKeyboardShortcuts();
});

async function loadData() {
    try {
        // 인라인 데이터 사용 (file:// 프로토콜 CORS 문제 해결)
        const dataScript = document.getElementById('analysis-data');
        if (dataScript && dataScript.textContent) {
            analysisData = JSON.parse(dataScript.textContent);
            console.log('Data loaded (inline):', analysisData.project_name);
        } else {
            // 폴백: fetch 시도
            const response = await fetch('data.json');
            analysisData = await response.json();
            console.log('Data loaded (fetch):', analysisData.project_name);
        }
    } catch (e) {
        console.error('Failed to load data:', e);
    }
}

// === Symbol Index ===
function buildSymbolIndex() {
    if (!analysisData) return;

    analysisData.modules.forEach(module => {
        // Index functions
        module.functions.forEach(func => {
            symbolIndex[func.qualified_name] = {
                type: 'function',
                data: func,
                module: module
            };
        });

        // Index classes and their methods
        module.classes.forEach(cls => {
            symbolIndex[cls.qualified_name] = {
                type: 'class',
                data: cls,
                module: module
            };

            cls.methods.forEach(method => {
                symbolIndex[method.qualified_name] = {
                    type: 'method',
                    data: method,
                    module: module,
                    parentClass: cls
                };
            });
        });
    });
}

// === Navigation Tree ===
function renderNavTree() {
    if (!analysisData) return;

    const navTree = document.getElementById('nav-tree');
    navTree.innerHTML = '';

    // Group modules by layer
    const layers = {};
    analysisData.modules.forEach(module => {
        const layer = module.layer || 'other';
        if (!layers[layer]) layers[layer] = [];
        layers[layer].push(module);
    });

    // Render each layer
    const layerOrder = ['domain', 'ports', 'adapters', 'config', 'other'];
    layerOrder.forEach(layer => {
        if (!layers[layer] || layers[layer].length === 0) return;

        const layerEl = document.createElement('div');
        layerEl.className = 'nav-layer';

        const headerEl = document.createElement('div');
        headerEl.className = 'nav-layer-header';
        headerEl.textContent = layer.toUpperCase();
        layerEl.appendChild(headerEl);

        layers[layer].forEach(module => {
            layerEl.appendChild(createModuleNavItem(module));
        });

        navTree.appendChild(layerEl);
    });

    // Update stats
    document.getElementById('stat-modules').textContent = analysisData.modules.length;
    document.getElementById('stat-classes').textContent =
        analysisData.modules.reduce((sum, m) => sum + m.classes.length, 0);
    document.getElementById('stat-functions').textContent =
        analysisData.modules.reduce((sum, m) => sum + m.functions.length +
            m.classes.reduce((s, c) => s + c.methods.length, 0), 0);
}

function createModuleNavItem(module) {
    const moduleEl = document.createElement('div');
    moduleEl.className = 'nav-module';

    const headerEl = document.createElement('div');
    headerEl.className = 'nav-module-header';
    headerEl.innerHTML = `
        <span class="nav-module-icon">▶</span>
        <span class="nav-module-name">${module.name.split('.').pop()}</span>
    `;
    headerEl.onclick = () => moduleEl.classList.toggle('expanded');
    moduleEl.appendChild(headerEl);

    const childrenEl = document.createElement('div');
    childrenEl.className = 'nav-module-children';

    // Add classes
    module.classes.forEach(cls => {
        const itemEl = document.createElement('div');
        itemEl.className = 'nav-item';
        itemEl.innerHTML = `
            <span class="nav-item-icon class">C</span>
            <span>${cls.name}</span>
        `;
        itemEl.onclick = (e) => {
            e.stopPropagation();
            showSymbolDetail(cls.qualified_name);
        };
        childrenEl.appendChild(itemEl);
    });

    // Add functions
    module.functions.forEach(func => {
        const itemEl = document.createElement('div');
        itemEl.className = 'nav-item';
        itemEl.innerHTML = `
            <span class="nav-item-icon function">ƒ</span>
            <span>${func.name}</span>
        `;
        itemEl.onclick = (e) => {
            e.stopPropagation();
            showSymbolDetail(func.qualified_name);
        };
        childrenEl.appendChild(itemEl);
    });

    moduleEl.appendChild(childrenEl);
    return moduleEl;
}

// === Dashboard ===
function renderDashboard() {
    if (!analysisData) return;

    renderCoverageChart();
    renderLayerBars();
    renderIssuesList();
    renderQuickAccess();
}

function renderCoverageChart() {
    const stats = analysisData.statistics || {};
    const container = document.getElementById('coverage-chart');

    const coverageData = [
        { label: 'High', value: (stats.high_ratio || 0) * 100, class: 'high' },
        { label: 'Medium', value: (stats.medium_ratio || 0) * 100, class: 'medium' },
        { label: 'Low/Unknown', value: ((stats.low_ratio || 0) + (stats.unknown_ratio || 0)) * 100, class: 'low' }
    ];

    container.innerHTML = coverageData.map(d => `
        <div class="coverage-bar">
            <span class="coverage-label">${d.label}</span>
            <div class="coverage-track">
                <div class="coverage-fill ${d.class}" style="width: ${d.value}%"></div>
            </div>
            <span class="coverage-value">${d.value.toFixed(1)}%</span>
        </div>
    `).join('');
}

function renderLayerBars() {
    const container = document.getElementById('layer-bars');

    const layerCounts = {};
    let total = 0;
    analysisData.modules.forEach(module => {
        const layer = module.layer || 'other';
        const count = module.functions.length + module.classes.length;
        layerCounts[layer] = (layerCounts[layer] || 0) + count;
        total += count;
    });

    const layers = ['domain', 'ports', 'adapters', 'other'];
    container.innerHTML = layers.map(layer => {
        const count = layerCounts[layer] || 0;
        const pct = total > 0 ? (count / total) * 100 : 0;
        return `
            <div class="layer-bar">
                <span class="layer-name">${layer}</span>
                <div class="layer-bar-track">
                    <div class="layer-bar-fill ${layer}" style="width: ${pct}%">
                        ${count}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function renderIssuesList() {
    const container = document.getElementById('issues-list');
    const issues = [];

    // Find symbols with unknown confidence
    Object.entries(symbolIndex).forEach(([name, info]) => {
        const confidence = info.data.io?.overall_confidence || info.data.visibility;
        if (confidence === 'unknown' || confidence === 'low') {
            issues.push({
                name: info.data.name,
                qualifiedName: name,
                type: info.type,
                reason: '타입 정보 부족'
            });
        }
    });

    if (issues.length === 0) {
        container.innerHTML = '<li class="empty-state">문제 없음 ✓</li>';
        return;
    }

    container.innerHTML = issues.slice(0, 10).map(issue => `
        <li class="issue-item warning" onclick="showSymbolDetail('${issue.qualifiedName}')">
            <strong>${issue.name}</strong>: ${issue.reason}
        </li>
    `).join('');
}

function renderQuickAccess() {
    const container = document.getElementById('quick-access');
    const quickItems = [];

    // Add some notable symbols
    Object.entries(symbolIndex).forEach(([name, info]) => {
        if (info.type === 'class' && !name.includes('._')) {
            quickItems.push({
                name: info.data.name,
                qualifiedName: name,
                type: 'class',
                icon: '📦'
            });
        }
    });

    container.innerHTML = quickItems.slice(0, 8).map(item => `
        <div class="quick-access-item" onclick="showSymbolDetail('${item.qualifiedName}')">
            <div class="quick-access-icon">${item.icon}</div>
            <div class="quick-access-name">${item.name}</div>
            <div class="quick-access-type">${item.type}</div>
        </div>
    `).join('');
}

// === Search ===
function setupSearch() {
    const input = document.getElementById('search-input');
    const results = document.getElementById('search-results');

    input.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        if (query.length < 2) {
            results.classList.add('hidden');
            return;
        }

        const matches = Object.entries(symbolIndex)
            .filter(([name, _]) => name.toLowerCase().includes(query))
            .slice(0, 10);

        if (matches.length === 0) {
            results.innerHTML = '<div class="search-result-item">결과 없음</div>';
        } else {
            results.innerHTML = matches.map(([name, info]) => `
                <div class="search-result-item" onclick="showSymbolDetail('${name}')">
                    <div class="search-result-name">${info.data.name}</div>
                    <div class="search-result-path">${name}</div>
                </div>
            `).join('');
        }

        results.classList.remove('hidden');
    });

    input.addEventListener('blur', () => {
        setTimeout(() => results.classList.add('hidden'), 200);
    });
}

// === Symbol Detail ===
function showSymbolDetail(qualifiedName) {
    const info = symbolIndex[qualifiedName];
    if (!info) return;

    const symbol = info.data;

    // Update header
    document.getElementById('symbol-name').textContent = symbol.name;
    document.getElementById('symbol-type').textContent = info.type;
    document.getElementById('symbol-type').className = `badge ${info.type}`;

    const confidence = symbol.io?.overall_confidence || 'unknown';
    document.getElementById('symbol-confidence').textContent = confidence.toUpperCase();
    document.getElementById('symbol-confidence').className = `confidence-badge ${confidence}`;

    // Update meta
    document.getElementById('symbol-meta').innerHTML = `
        <div class="meta-item">
            <span class="meta-label">경로:</span>
            <span class="meta-value">${qualifiedName}</span>
        </div>
        <div class="meta-item">
            <span class="meta-label">파일:</span>
            <span class="meta-value">${symbol.file_path}:${symbol.line_start}</span>
        </div>
        <div class="meta-item">
            <span class="meta-label">레이어:</span>
            <span class="meta-value">${symbol.layer || '-'}</span>
        </div>
    `;

    // Update signature
    document.getElementById('symbol-signature').textContent = generateSignature(symbol, info.type);

    // Update inputs table
    const inputsBody = document.querySelector('#symbol-inputs tbody');
    if (symbol.io?.inputs?.length > 0) {
        inputsBody.innerHTML = symbol.io.inputs.map(param => `
            <tr>
                <td>${param.name}</td>
                <td class="type-cell">${param.type_ref?.raw || '-'}</td>
                <td class="default-cell">${param.default || '-'}</td>
                <td>${param.description || '-'}</td>
                <td><span class="confidence-badge ${param.type_ref?.confidence || 'unknown'}">${(param.type_ref?.confidence || 'unknown').toUpperCase()}</span></td>
            </tr>
        `).join('');
    } else {
        inputsBody.innerHTML = '<tr><td colspan="5" class="empty-state">파라미터 없음</td></tr>';
    }

    // Update output
    const outputEl = document.getElementById('symbol-output');
    if (symbol.io?.output) {
        outputEl.innerHTML = `<span class="output-type">${symbol.io.output.raw}</span>`;
    } else {
        outputEl.innerHTML = '<span class="empty-state">반환 타입 없음</span>';
    }

    // Update raises
    const raisesEl = document.getElementById('symbol-raises');
    if (symbol.io?.raises?.length > 0) {
        raisesEl.innerHTML = symbol.io.raises.map(r => `
            <li>
                <span class="raises-type">${r.exception_type}</span>
                ${r.condition ? `<span>${r.condition}</span>` : ''}
            </li>
        `).join('');
    } else {
        raisesEl.innerHTML = '<li class="empty-state">예외 없음</li>';
    }

    // Update side effects
    const sideEffectsEl = document.getElementById('symbol-side-effects');
    if (symbol.io?.side_effects?.length > 0) {
        sideEffectsEl.innerHTML = symbol.io.side_effects.map(se => `
            <li>
                <span class="side-effect-kind ${se.kind}">${se.kind}</span>
                <span>${se.evidence}</span>
            </li>
        `).join('');
    } else {
        sideEffectsEl.innerHTML = '<li class="empty-state">부작용 없음</li>';
    }

    // Update docstring
    document.getElementById('symbol-docstring').textContent = symbol.docstring || '문서 없음';

    // Show detail view
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById('symbol-detail').classList.add('active');
}

function generateSignature(symbol, type) {
    if (type === 'class') {
        const bases = symbol.bases?.length > 0 ? `(${symbol.bases.join(', ')})` : '';
        return `class ${symbol.name}${bases}:`;
    }

    const asyncPrefix = symbol.is_async ? 'async ' : '';
    const params = symbol.io?.inputs?.map(p => {
        let s = p.name;
        if (p.type_ref?.raw) s += `: ${p.type_ref.raw}`;
        if (p.default) s += ` = ${p.default}`;
        return s;
    }).join(', ') || '';

    const returnType = symbol.io?.output?.raw ? ` -> ${symbol.io.output.raw}` : '';

    return `${asyncPrefix}def ${symbol.name}(${params})${returnType}:`;
}

function showDashboard() {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById('dashboard').classList.add('active');
    updateNavButtons('dashboard');
}

function updateNavButtons(active) {
    document.querySelectorAll('.main-nav .nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeBtn = document.getElementById(`nav-${active}`);
    if (activeBtn) activeBtn.classList.add('active');
}

// === Keyboard Shortcuts ===
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl+K or Cmd+K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            document.getElementById('search-input').focus();
        }

        // Escape to go back
        if (e.key === 'Escape') {
            showDashboard();
        }

        // G for graph view
        if (e.key === 'g' && !e.ctrlKey && !e.metaKey && document.activeElement.tagName !== 'INPUT') {
            showGraphView();
        }
    });
}

// === Graph View ===
function showGraphView() {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById('graph-view').classList.add('active');
    updateNavButtons('graph');
    renderGraph();
}

let graphFilter = 'all';
let graphZoom = 1;
let graphPan = { x: 0, y: 0 };

function renderGraph() {
    if (!analysisData?.type_graph) {
        console.log('No type_graph data');
        return;
    }

    const svg = document.getElementById('graph-svg');
    let { nodes, edges } = analysisData.type_graph;

    console.log(`Rendering graph: ${nodes.length} nodes, ${edges.length} edges`);

    // 필터링
    if (graphFilter !== 'all') {
        nodes = nodes.filter(n => {
            const layer = n.metadata?.layer || 'other';
            return layer === graphFilter;
        });
        const nodeIds = new Set(nodes.map(n => n.id));
        edges = edges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target));
    }

    // 노드 수 제한 (성능)
    const maxNodes = 200;
    if (nodes.length > maxNodes) {
        // 클래스와 함수 위주로 필터링
        nodes = nodes.filter(n => n.kind === 'class' || n.kind === 'function').slice(0, maxNodes);
        const nodeIds = new Set(nodes.map(n => n.id));
        edges = edges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target));
    }

    // Clear
    svg.innerHTML = '';

    // SVG 크기 설정
    const width = svg.clientWidth || 1000;
    const height = 600;

    // 그래프 그룹 (줌/팬용)
    const mainGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    mainGroup.setAttribute('id', 'graph-main');
    mainGroup.setAttribute('transform', `translate(${graphPan.x}, ${graphPan.y}) scale(${graphZoom})`);
    svg.appendChild(mainGroup);

    // 좌표 정규화
    const xs = nodes.map(n => n.x);
    const ys = nodes.map(n => n.y);
    const minX = Math.min(...xs) - 50;
    const maxX = Math.max(...xs) + 50;
    const minY = Math.min(...ys) - 50;
    const maxY = Math.max(...ys) + 50;

    const scaleX = width / (maxX - minX);
    const scaleY = height / (maxY - minY);
    const scale = Math.min(scaleX, scaleY, 1);

    const normalize = (node) => ({
        x: (node.x - minX) * scale + 50,
        y: (node.y - minY) * scale + 50
    });

    // Add edges
    edges.forEach(edge => {
        const sourceNode = nodes.find(n => n.id === edge.source);
        const targetNode = nodes.find(n => n.id === edge.target);
        if (!sourceNode || !targetNode) return;

        const s = normalize(sourceNode);
        const t = normalize(targetNode);

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', s.x);
        line.setAttribute('y1', s.y);
        line.setAttribute('x2', t.x);
        line.setAttribute('y2', t.y);
        line.setAttribute('class', `graph-edge ${edge.relation}`);
        line.setAttribute('stroke-opacity', '0.5');
        mainGroup.appendChild(line);
    });

    // Add nodes
    nodes.forEach(node => {
        const pos = normalize(node);

        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', 'graph-node');
        g.setAttribute('transform', `translate(${pos.x}, ${pos.y})`);

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('r', node.kind === 'class' ? 10 : 6);
        circle.setAttribute('fill', getNodeColor(node.kind));
        circle.setAttribute('stroke', '#fff');
        circle.setAttribute('stroke-width', '1');

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('dy', -14);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('fill', '#e6edf3');
        text.setAttribute('font-size', '9px');
        text.textContent = node.label.length > 15 ? node.label.slice(0, 15) + '...' : node.label;

        g.appendChild(circle);
        g.appendChild(text);

        // 호버 효과
        g.onmouseenter = () => {
            circle.setAttribute('r', node.kind === 'class' ? 14 : 10);
            showTooltip(node, pos.x, pos.y);
        };
        g.onmouseleave = () => {
            circle.setAttribute('r', node.kind === 'class' ? 10 : 6);
            hideTooltip();
        };

        g.onclick = () => {
            if (node.metadata?.qualified_name && symbolIndex[node.metadata.qualified_name]) {
                showSymbolDetail(node.metadata.qualified_name);
            }
        };

        mainGroup.appendChild(g);
    });

    // 범례
    renderGraphLegend(svg, width);

    // 통계 표시
    document.getElementById('graph-stats').innerHTML = `
        노드: ${nodes.length} / 엣지: ${edges.length}
    `;
}

function renderGraphLegend(svg, width) {
    const legend = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    legend.setAttribute('transform', `translate(${width - 120}, 20)`);

    const items = [
        { color: '#d29922', label: 'Class' },
        { color: '#a371f7', label: 'Function' },
        { color: '#58a6ff', label: 'Type' },
    ];

    items.forEach((item, i) => {
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('transform', `translate(0, ${i * 20})`);

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('r', 5);
        circle.setAttribute('fill', item.color);

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', 12);
        text.setAttribute('dy', 4);
        text.setAttribute('fill', '#8b949e');
        text.setAttribute('font-size', '10px');
        text.textContent = item.label;

        g.appendChild(circle);
        g.appendChild(text);
        legend.appendChild(g);
    });

    svg.appendChild(legend);
}

function showTooltip(node, x, y) {
    const tooltip = document.getElementById('graph-tooltip');
    tooltip.innerHTML = `
        <strong>${node.label}</strong><br>
        <span style="color: var(--text-muted)">종류: ${node.kind}</span><br>
        ${node.metadata?.layer ? `<span style="color: var(--text-muted)">레이어: ${node.metadata.layer}</span>` : ''}
    `;
    tooltip.style.left = `${x + 20}px`;
    tooltip.style.top = `${y}px`;
    tooltip.classList.remove('hidden');
}

function hideTooltip() {
    document.getElementById('graph-tooltip').classList.add('hidden');
}

function filterGraph(filter) {
    graphFilter = filter;
    renderGraph();
}

function zoomGraph(delta) {
    graphZoom = Math.max(0.5, Math.min(3, graphZoom + delta));
    renderGraph();
}

function resetGraph() {
    graphFilter = 'all';
    graphZoom = 1;
    graphPan = { x: 0, y: 0 };
    document.getElementById('graph-filter').value = 'all';
    renderGraph();
}

function getNodeColor(kind) {
    const colors = {
        'class': '#d29922',
        'function': '#a371f7',
        'type': '#58a6ff',
        'module': '#3fb950'
    };
    return colors[kind] || '#6e7681';
}
"""
        path.write_text(js, encoding="utf-8")
