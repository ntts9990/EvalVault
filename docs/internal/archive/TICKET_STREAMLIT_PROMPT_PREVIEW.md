## Ticket: Streamlit Prompt Diff 미리보기

- **요청 배경**: Streamlit History/Reports에서 Prompt 상태 패널이 `status`, checksum, diff 헤더만 보여주기 때문에 운영자가 실제 프롬프트 내용을 확인하려면 로컬 파일을 열거나 CLI를 다시 실행해야 함. Prompt drift가 발생했을 때 즉시 내용을 확인할 수 있는 UI/UX가 필요함.
- **현재 증상**:
  - Run `5ec6d3ad-f2b6-42d0-9047-c1d22fbb52b4`처럼 Prompt status = modified일 때도 UI에는 diff 헤더만 나오고 파일 내용 클릭/다운로드가 불가능.
  - 온콜 중 Slack/Streamlit에서 Prompt 내용을 바로 보지 못해 대응 속도가 느려짐.
- **요구 사항**:
  1. Streamlit History/Reports Prompt 패널에서 각 파일 행을 클릭하면 모달/하단 패널로 실제 내용과 diff를 렌더링한다.
  2. 최소한 `agent/prompts/*.txt` 내용 전문 또는 상위 N줄을 보여주고, Phoenix manifest metadata(Notes, Experiment ID 등)를 함께 노출한다.
  3. Slack/릴리즈 노트 템플릿에도 동일 미리보기 링크나 코드 블록을 포함해 Prompt drift 원인을 빠르게 확인할 수 있게 한다.
- **수행 범위**:
  - `src/evalvault/adapters/inbound/web/components/history.py` / `reports.py` UI 확장.
  - Prompt metadata 직렬화(`tracker_metadata["phoenix"]["prompts"]`)에 `content_preview` 또는 diff 문자열 포함.
  - 문서 업데이트: `docs/guides/OBSERVABILITY_PLAYBOOK.md` Prompt 루프 챕터에 새 UI 스크린샷/설명 추가.
- **완료 기준**:
  - Prompt 파일을 수정한 뒤 Streamlit에서 행 클릭 → 모달에서 diff와 본문이 즉시 노출.
  - Slack/릴리즈 노트가 동일 정보를 제공하고, Prompt drift 대응 시간이 단축되었다는 QA 확인.
