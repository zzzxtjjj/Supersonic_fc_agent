# Product Architecture

## Boundary

```text
Frontend (React)
      │ HTTP API
      ▼
FastAPI
      │ product adapter
      ▼
LangGraph Agent
      ├── Structured Tools
      ├── RAG
      └── Future Database
```

This layout is an interface boundary, not a change to the current Agent design.
FastAPI calls the product entry point rather than placing planning, verification,
recovery, tool routing, retrieval, or database logic inside route handlers.

## Current state

- **Frontend:** Agent、Matches、Players、Stats、Gallery 均通过 Backend API。
- **Backend:** Agent chat 调用正式 LangGraph 产品入口；赛季与媒体数据使用项目 JSON/本地媒体文件。
- **Agent:** remains an independent Python package; FastAPI only calls its public `run_graph_agent` entry point.
- **Database:** not connected and no migration has been performed.

## Agent request flow

```text
Frontend POST /api/agent/chat
  → FastAPI validates AgentChatRequest
  → route invokes the existing LangGraph product entry point
  → FastAPI returns answer, session_id, and sources
```

Evaluation trace remains inside `evals/`. The public response does not include
tool calls, workflow state, prompts, model reasoning, `reasoning_details`, API
keys, or other internal secrets.

`frontend/src/services/api.ts` 使用 `VITE_API_BASE_URL` 作为部署地址。开发环境由
Vite 将 `/api` 代理到本地 FastAPI；赛季页面不会在 API 失败时回退到旧 mock。
