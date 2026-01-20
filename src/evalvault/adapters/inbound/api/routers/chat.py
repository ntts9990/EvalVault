from __future__ import annotations

import asyncio
import json
import os
import re
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(tags=["chat"])

MCP_URL = os.getenv("EVALVAULT_MCP_URL", "http://localhost:8000/api/v1/mcp")
MCP_TOKEN = os.getenv("EVALVAULT_MCP_TOKEN", "mcp-local-dev-token")

_RAG_RETRIEVER = None
_RAG_DOCS_COUNT = 0
_RAG_TEXTS: list[str] = []
_RAG_INITIALIZED = False


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: list[ChatMessage] | None = None


def _extract_run_ids(text: str) -> list[str]:
    return re.findall(r"run_[A-Za-z0-9_-]+", text)


def _format_tool_result(result: Any) -> str:
    if isinstance(result, dict):
        if "result" in result:
            return str(result["result"])
        if "error" in result:
            return f"오류: {result['error']}"
    return str(result)


def _summarize_runs(payload: dict[str, Any]) -> str:
    runs = payload.get("runs") or []
    if not runs:
        return "실행 기록이 없습니다."
    lines = ["최근 실행 목록:"]
    for run in runs[:10]:
        lines.append(
            "- {run_id} | {dataset} | {model} | pass={pass_rate:.2f}".format(
                run_id=run.get("run_id"),
                dataset=run.get("dataset_name"),
                model=run.get("model_name"),
                pass_rate=run.get("pass_rate", 0.0),
            )
        )
    return "\n".join(lines)


def _summarize_run_summary(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    if not summary:
        return "요약 정보를 찾지 못했습니다."
    return (
        "요약: {run_id}\n"
        "- dataset: {dataset}\n"
        "- model: {model}\n"
        "- pass_rate: {pass_rate:.2f}\n"
        "- total: {total} / passed: {passed}\n"
        "- metrics: {metrics}".format(
            run_id=summary.get("run_id"),
            dataset=summary.get("dataset_name"),
            model=summary.get("model_name"),
            pass_rate=summary.get("pass_rate", 0.0),
            total=summary.get("total_test_cases"),
            passed=summary.get("passed_test_cases"),
            metrics=", ".join(summary.get("metrics_evaluated", []) or []),
        )
    )


def _summarize_compare(payload: dict[str, Any]) -> str:
    baseline = payload.get("baseline_run_id")
    candidate = payload.get("candidate_run_id")
    delta = payload.get("metrics_delta") or {}
    avg = delta.get("avg") or {}
    lines = [
        f"비교 결과: {baseline} vs {candidate}",
        "평균 변화:",
    ]
    for metric, value in avg.items():
        lines.append(f"- {metric}: {value:+.4f}")
    notes = delta.get("notes") or []
    if notes:
        lines.append("노트: " + "; ".join(notes))
    return "\n".join(lines)


def _summarize_artifacts(payload: dict[str, Any]) -> str:
    artifacts = payload.get("artifacts") or {}
    if not artifacts:
        return "아티팩트 경로를 찾지 못했습니다."
    return (
        "아티팩트:\n"
        f"- kind: {artifacts.get('kind')}\n"
        f"- report: {artifacts.get('report_path')}\n"
        f"- output: {artifacts.get('output_path')}\n"
        f"- dir: {artifacts.get('artifacts_dir')}"
    )


def _summarize_result(tool_name: str, payload: dict[str, Any]) -> str:
    if tool_name == "list_runs":
        return _summarize_runs(payload)
    if tool_name == "get_run_summary":
        return _summarize_run_summary(payload)
    if tool_name == "analyze_compare":
        return _summarize_compare(payload)
    if tool_name == "get_artifacts":
        return _summarize_artifacts(payload)
    return str(payload)


def _load_text_files(root: Path, extensions: tuple[str, ...], limit: int) -> list[str]:
    texts: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in extensions:
            continue
        if limit and len(texts) >= limit:
            break
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if content.strip():
            texts.append(content)
    return texts


async def _get_rag_retriever():
    global _RAG_RETRIEVER
    global _RAG_DOCS_COUNT
    global _RAG_TEXTS
    global _RAG_INITIALIZED

    if _RAG_RETRIEVER is not None:
        return _RAG_RETRIEVER, _RAG_DOCS_COUNT

    if not _RAG_INITIALIZED:
        docs_root = Path(os.getenv("EVALVAULT_RAG_DOCS", "docs"))
        src_root = Path(os.getenv("EVALVAULT_RAG_SRC", "src"))
        docs_limit = int(os.getenv("EVALVAULT_RAG_DOCS_LIMIT", "120"))
        src_limit = int(os.getenv("EVALVAULT_RAG_SRC_LIMIT", "120"))

        texts: list[str] = []
        if docs_root.exists():
            texts.extend(_load_text_files(docs_root, (".md", ".txt"), docs_limit))
        if src_root.exists():
            texts.extend(_load_text_files(src_root, (".py",), src_limit))

        _RAG_TEXTS = texts
        _RAG_DOCS_COUNT = len(texts)
        _RAG_INITIALIZED = True

    if not _RAG_TEXTS:
        return None, 0

    from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter
    from evalvault.adapters.outbound.nlp.korean.toolkit_factory import try_create_korean_toolkit
    from evalvault.config.settings import Settings

    settings = Settings()
    ollama_adapter = OllamaAdapter(settings)
    toolkit = try_create_korean_toolkit()
    if toolkit is None:
        return None, 0

    use_hybrid = os.getenv("EVALVAULT_RAG_USE_HYBRID", "true").lower() == "true"
    retriever = toolkit.build_retriever(
        documents=_RAG_TEXTS,
        use_hybrid=use_hybrid,
        ollama_adapter=ollama_adapter if use_hybrid else None,
        embedding_profile=os.getenv("EVALVAULT_RAG_EMBEDDING_PROFILE", "dev"),
        verbose=False,
    )
    if retriever is None:
        return None, 0

    _RAG_RETRIEVER = retriever
    return retriever, _RAG_DOCS_COUNT


async def _direct_chat_answer(user_text: str) -> str | None:
    payload = {
        "model": os.getenv("OLLAMA_CHAT_MODEL", "gpt-oss-safeguard:20b"),
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for EvalVault."},
            {"role": "user", "content": user_text},
        ],
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    return data.get("message", {}).get("content", "").strip() or None


def _simple_retrieve(texts: list[str], query: str, top_k: int) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9가-힣]+", query.lower())
    if not tokens:
        return []
    scored: list[tuple[int, str]] = []
    for text in texts:
        hay = text.lower()
        score = sum(hay.count(token) for token in tokens)
        if score:
            scored.append((score, text))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [text for _, text in scored[:top_k]]


async def _rag_answer(user_text: str) -> str | None:
    retriever, _ = await _get_rag_retriever()
    contexts: list[str] = []

    if retriever is not None:
        results = retriever.search(user_text, top_k=5)
        for item in results:
            context = getattr(item, "document", None)
            if context:
                contexts.append(context)

    if not contexts and _RAG_TEXTS:
        contexts = _simple_retrieve(_RAG_TEXTS, user_text, top_k=5)

    if not contexts:
        return None

    if os.getenv("EVALVAULT_RAG_LLM_ENABLED", "true").lower() != "true":
        return "\n\n".join(contexts[:3])

    prompt = (
        "다음은 EvalVault 코드/문서에서 검색된 컨텍스트입니다.\n"
        "컨텍스트만 근거로 사용해 한국어로 답하세요.\n\n"
        "[컨텍스트]\n"
        + "\n\n---\n\n".join(contexts[:3])
        + "\n\n[질문]\n"
        + user_text
        + "\n\n[답변]"
    )

    payload = {
        "model": os.getenv("OLLAMA_CHAT_MODEL", "gpt-oss-safeguard:20b"),
        "messages": [
            {"role": "system", "content": "You are a helpful assistant for EvalVault."},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    return data.get("message", {}).get("content", "").strip() or None


async def _call_mcp_tool(tool_name: str, tool_args: dict[str, Any]) -> Any:
    headers = {
        "Authorization": f"Bearer {MCP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": tool_args},
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(MCP_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    return data


async def _resolve_tool_with_llm(user_text: str) -> dict[str, Any] | None:
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    router_model = os.getenv("OLLAMA_ROUTER_MODEL", "gemma3:1b")

    system_prompt = (
        "You are a router for EvalVault. "
        "Return JSON only with keys: action, tool, arguments."
        "Action must be one of: tool, rag, direct."
        "Tools: list_runs, get_run_summary, run_evaluation, analyze_compare, get_artifacts."
        "Rules:"
        "- If user asks about datasets, prefer tool list_datasets."
        "- If question is about EvalVault docs/usage, prefer rag."
        "- If greeting or general chat, use direct."
        "- For tool list_runs: arguments {limit:int}"
        "- For tool get_run_summary: {run_id:string}"
        "- For tool analyze_compare: {run_id_a:string, run_id_b:string}"
        "- For tool run_evaluation: {dataset_path:string, metrics:[string], profile:string, auto_analyze:bool}"
        "- For tool get_artifacts: {run_id:string, kind:'analysis'|'comparison'}"
        "- For tool list_datasets: {limit:int}"
    )

    payload = {
        "model": router_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{ollama_url}/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()

    content = data.get("message", {}).get("content", "").strip()
    if not content:
        return None

    try:
        return json.loads(content)
    except Exception:
        return None


def _extract_json_content(result: Any) -> dict[str, Any] | None:
    if isinstance(result, dict) and isinstance(result.get("structuredContent"), dict):
        return result.get("structuredContent")

    if hasattr(result, "structuredContent"):
        payload = result.structuredContent
        if isinstance(payload, dict):
            return payload

    if hasattr(result, "content"):
        content = result.content
    elif isinstance(result, dict):
        content = result.get("content")
    else:
        content = None

    if not isinstance(content, list):
        return None

    for item in content:
        if isinstance(item, dict):
            item_type = item.get("type")
            if item_type == "json":
                payload = item.get("json")
                if isinstance(payload, dict):
                    return payload
            if item_type == "text":
                text = item.get("text")
                if isinstance(text, str):
                    try:
                        parsed = json.loads(text)
                    except Exception:
                        return None
                    if isinstance(parsed, dict):
                        return parsed
        else:
            item_type = getattr(item, "type", None)
            if item_type == "text":
                text = getattr(item, "text", None)
                if isinstance(text, str):
                    try:
                        parsed = json.loads(text)
                    except Exception:
                        return None
                    if isinstance(parsed, dict):
                        return parsed
    return None


def _chunk_text(text: str, size: int = 42) -> list[str]:
    if not text:
        return []
    return [text[i : i + size] for i in range(0, len(text), size)]


def _event(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False) + "\n"


async def _emit_answer(answer: str) -> AsyncGenerator[str, None]:
    for chunk in _chunk_text(answer):
        yield _event({"type": "delta", "content": chunk})
        await asyncio.sleep(0)
    yield _event({"type": "final", "content": answer})


async def _chat_stream(user_text: str) -> AsyncGenerator[str, None]:
    started_at = time.perf_counter()
    if len(user_text) <= 4:
        yield _event({"type": "final", "content": "안녕하세요! EvalVault 관련 질문을 해주세요."})
        return

    if len(user_text) <= 6:
        yield _event({"type": "status", "message": "짧은 질문 처리 중..."})
        answer = await _direct_chat_answer(user_text)
        if answer:
            async for item in _emit_answer(answer):
                yield item
        else:
            yield _event({"type": "final", "content": "답변을 생성하지 못했습니다."})
        return

    yield _event({"type": "status", "message": "요청 분류 중..."})
    try:
        router = await asyncio.wait_for(_resolve_tool_with_llm(user_text), timeout=20)
    except TimeoutError:
        router = None
    except Exception:
        router = None

    if not isinstance(router, dict):
        router = None

    if router is None:
        yield _event({"type": "status", "message": "문서 검색 중..."})
        try:
            rag_answer = await asyncio.wait_for(_rag_answer(user_text), timeout=30)
        except TimeoutError:
            yield _event({"type": "error", "message": "문서 검색이 지연됩니다. 다시 시도해주세요."})
            return
        if rag_answer:
            async for item in _emit_answer(rag_answer):
                yield item
            return
        answer = await _direct_chat_answer(user_text)
        if answer:
            async for item in _emit_answer(answer):
                yield item
            return
        yield _event({"type": "final", "content": "요청을 해석하지 못했습니다. 다시 질문해주세요."})
        return

    action = router.get("action")
    tool_name = router.get("tool")
    tool_args = router.get("arguments", {})

    if action == "direct":
        answer = await _direct_chat_answer(user_text)
        if answer:
            async for item in _emit_answer(answer):
                yield item
        else:
            yield _event({"type": "final", "content": "답변을 생성하지 못했습니다."})
        return

    if action == "rag":
        yield _event({"type": "status", "message": "문서 검색 중..."})
        try:
            rag_answer = await asyncio.wait_for(_rag_answer(user_text), timeout=30)
        except TimeoutError:
            yield _event({"type": "error", "message": "문서 검색이 지연됩니다. 다시 시도해주세요."})
            return
        if rag_answer:
            async for item in _emit_answer(rag_answer):
                yield item
        else:
            yield _event({"type": "final", "content": "관련 문서를 찾지 못했습니다."})
        return

    if action != "tool":
        yield _event({"type": "final", "content": "요청을 해석하지 못했습니다. 다시 질문해주세요."})
        return

    if not tool_name:
        yield _event({"type": "final", "content": "도구 이름을 찾지 못했습니다."})
        return

    yield _event({"type": "status", "message": "도구 실행 중..."})
    try:
        result = await asyncio.wait_for(_call_mcp_tool(tool_name, tool_args), timeout=12)
    except TimeoutError:
        yield _event(
            {"type": "error", "message": "응답 지연(12s 초과). MCP 서버 상태를 확인해주세요."}
        )
        return
    except Exception as exc:
        yield _event({"type": "error", "message": f"도구 호출 실패: {exc}"})
        return

    payload = _extract_json_content(result)
    if isinstance(payload, dict):
        summary = _summarize_result(tool_name, payload)
        async for item in _emit_answer(summary):
            yield item
        return

    if hasattr(result, "content"):
        text = _format_tool_result(result.content)
    else:
        text = f"도구 실행 결과: {_format_tool_result(result)}"
    async for item in _emit_answer(text):
        yield item

    elapsed_ms = (time.perf_counter() - started_at) * 1000
    yield _event({"type": "status", "message": f"처리 완료 ({elapsed_ms:.0f}ms)"})


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    user_text = request.message.strip()
    if not user_text:
        return StreamingResponse(
            iter([_event({"type": "error", "message": "질문을 입력해주세요."})]),
            media_type="application/x-ndjson",
        )

    async def event_generator():
        async for item in _chat_stream(user_text):
            yield item

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
