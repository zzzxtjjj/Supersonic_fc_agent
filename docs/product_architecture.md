# Product Architecture

## Boundary

```text
Frontend (React)
      │ future HTTP API
      ▼
FastAPI
      │ future adapter
      ▼
LangGraph Agent
      ├── Structured Tools
      ├── RAG
      └── Future Database
```

This layout is an interface boundary, not a change to the current Agent design.
FastAPI must call a future adapter rather than placing planning, verification,
recovery, tool routing, retrieval, or database logic inside route handlers.

## Current state

- **Frontend:** Matches、Players、Stats 通过 API 读取赛季数据；Gallery 仍使用本地 mock。
- **Backend:** Matches、Players、Stats 已连接 `data/seasons/<season>/`；Agent 与 Gallery 写入仍为 placeholder。
- **Agent:** independent Python application; it is not imported by the backend.
- **Database:** not connected and no migration has been performed.

## Future request flow

```text
Frontend POST /api/agent/chat
  → FastAPI validates AgentChatRequest
  → adapter invokes the existing LangGraph entry point
  → FastAPI returns answer, session_id, sources, and optional tool_trace
```

The public response may include tool names and execution status for debugging,
but must never expose model reasoning, `reasoning_details`, API keys, or other
internal secrets.

`frontend/src/services/api.ts` 使用 `VITE_API_BASE_URL` 作为部署地址。开发环境由
Vite 将 `/api` 代理到本地 FastAPI；赛季页面不会在 API 失败时回退到旧 mock。
