# Streamlit Web UI (Legacy)

> Streamlit UI는 간단 미리보기용으로만 유지되며 점진적 페이드아웃 예정입니다.
> 신규 기능/개선은 React + FastAPI Web UI에 집중합니다.

---

## 권장 사용 범위

- 로컬 SQLite DB 빠른 조회
- 데모/샘플 데이터 확인

---

## 실행

```bash
uv run evalvault web --db data/db/evalvault.db
```

---

## 참고

- `--extra web` 설치가 필요합니다.
- 결과 확인을 위해 `--db` 또는 `EVALVAULT_DB_PATH`를 동일하게 유지하세요.
- 본격적인 평가/분석/보고서는 Web UI(React + FastAPI) 또는 CLI 사용을 권장합니다.
