from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from evalvault.adapters.inbound.mcp import tools as mcp_tools
from evalvault.config.settings import Settings, get_settings

router = APIRouter(tags=["mcp"])


class JsonRpcRequest(BaseModel):
    jsonrpc: str = Field("2.0", pattern=r"^2\.0$")
    id: int | str | None = None
    method: str
    params: dict[str, Any] | None = None


def _normalize_tokens(raw_tokens: str | None) -> set[str]:
    if not raw_tokens:
        return set()
    return {token.strip() for token in raw_tokens.split(",") if token.strip()}


def _require_mcp_token(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.mcp_enabled:
        raise HTTPException(status_code=404, detail="MCP is disabled")
    tokens = _normalize_tokens(settings.mcp_auth_tokens) or _normalize_tokens(
        settings.api_auth_tokens
    )
    if not tokens:
        raise HTTPException(status_code=401, detail="MCP auth tokens are required")
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing MCP token")
    token = auth_header[7:].strip()
    if token not in tokens:
        raise HTTPException(status_code=401, detail="Invalid or missing MCP token")


def _tool_registry() -> dict[str, Any]:
    return {
        "list_runs": mcp_tools.list_runs,
        "get_run_summary": mcp_tools.get_run_summary,
        "run_evaluation": mcp_tools.run_evaluation,
        "analyze_compare": mcp_tools.analyze_compare,
        "get_artifacts": mcp_tools.get_artifacts,
    }


def _allowed_tools(settings: Settings) -> set[str]:
    if settings.mcp_allowed_tools:
        return {name.strip() for name in settings.mcp_allowed_tools.split(",") if name.strip()}
    return set(_tool_registry().keys())


def _serialize_result(result: Any) -> Any:
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "dict"):
        return result.dict()
    try:
        return asdict(result)
    except TypeError:
        return result


def _jsonrpc_result(rpc_id: int | str | None, payload: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": rpc_id, "result": payload}


def _jsonrpc_error(rpc_id: int | str | None, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": code, "message": message}}


@router.post("")
def handle_mcp_request(
    request: JsonRpcRequest,
    settings: Settings = Depends(get_settings),
    _: None = Depends(_require_mcp_token),
) -> dict[str, Any]:
    method = request.method
    params = request.params or {}

    if method == "initialize":
        return _jsonrpc_result(
            request.id,
            {
                "protocolVersion": settings.mcp_protocol_version,
                "serverInfo": {
                    "name": "evalvault-mcp",
                    "version": settings.mcp_server_version,
                },
                "capabilities": {"tools": {"listChanged": False}},
            },
        )

    if method in {"initialized", "notifications/initialized"}:
        return _jsonrpc_result(request.id, None)

    if method == "tools/list":
        allowed = _allowed_tools(settings)
        tools = [tool for tool in mcp_tools.get_tool_specs() if tool.get("name") in allowed]
        return _jsonrpc_result(request.id, {"tools": tools})

    if method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments") or {}
        if not tool_name:
            return _jsonrpc_error(request.id, -32602, "Missing tool name")

        allowed = _allowed_tools(settings)
        if tool_name not in allowed:
            return _jsonrpc_error(request.id, -32601, "Tool not allowed")

        tool_fn = _tool_registry().get(tool_name)
        if tool_fn is None:
            return _jsonrpc_error(request.id, -32601, "Tool not found")

        try:
            result = tool_fn(tool_args)
        except Exception as exc:
            return _jsonrpc_error(request.id, -32000, f"Tool execution failed: {exc}")

        payload = _serialize_result(result)
        return _jsonrpc_result(
            request.id,
            {
                "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
                "structuredContent": payload,
            },
        )

    if method == "ping":
        return _jsonrpc_result(request.id, {"status": "ok"})

    return _jsonrpc_error(request.id, -32601, "Method not found")
