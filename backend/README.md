# A 股投资 Agent 后端 API

本文档提供 A 股投资 Agent 后端 API 的概览和使用指南。

## Backend Directory Structure

```
backend/
├── __init__.py              # Initializes the backend package
├── main.py                  # FastAPI application instance and core setup
├── dependencies.py          # Dependency injection setup (e.g., for log storage)
├── state.py                 # In-memory state management (`api_state`) for real-time data
├── schemas.py               # Pydantic models for internal data structures (logs, etc.)
├── models/                  # Pydantic models for API requests/responses (`api_models.py`)
├── routers/                 # FastAPI routers defining API endpoints
│   ├── __init__.py
│   ├── agents.py            # Endpoints for `/api/agents/*`
│   ├── analysis.py          # Endpoints for `/api/analysis/*`
│   ├── api_runs.py          # Endpoints for `/api/runs/*` (memory state based)
│   ├── logs.py              # Endpoints for `/logs/*` (log storage based)
│   ├── runs.py              # Endpoints for `/runs/*` (log storage based)
│   └── workflow.py          # Endpoints for `/api/workflow/*`
├── services/                # Business logic services
│   ├── __init__.py
│   └── analysis.py          # Service for executing stock analysis workflow
├── storage/                 # Data storage implementations
│   ├── __init__.py
│   ├── base.py              # Base class/interface for log storage (`BaseLogStorage`)
│   └── memory.py            # In-memory implementation (`InMemoryLogStorage`)
├── utils/                   # Utility functions specific to the backend
│   ├── __init__.py
│   ├── api_utils.py         # API related helpers (serialization, response formatting)
│   └── context_managers.py  # Context managers (e.g., `workflow_run`)
└── README.md                # This documentation file
```

## API 结构

API 主要分为以下几个部分，基于不同的数据来源和用途：

1.  **`/api/*` (基于内存状态的 API)**:

    - 提供 Agent 最新状态、运行摘要和实时工作流信息的接口。
    - 数据主要来源于内存中的 `api_state` 对象。
    - 特点：响应快速，反映最新情况，但数据会在服务重启后丢失。
    - 使用统一的 `ApiResponse` 格式包装响应数据。
    - 主要端点包括：
      - `/api/agents/*`: 获取 Agent 最新信息、输入/输出、推理、LLM 交互。**注意：`latest_llm_request` 中的 `messages` 字段可能为 `null`，尤其当 LLM 调用是通过 lambda 函数进行时，这可能导致装饰器无法正确提取参数。请检查对应 Agent 的实现。**
      - `/api/analysis/*`: 启动和查询股票分析任务状态。
      - `/api/runs/*`: 获取内存中记录的运行摘要信息。
      - `/api/workflow/*`: 获取当前正在运行的工作流状态。

2.  **`/` (基于日志存储的 API)**:
    - 提供详细的运行历史、Agent 执行步骤和 LLM 交互日志的接口。
    - 数据来源于 `BaseLogStorage` 接口（当前默认为 `InMemoryLogStorage`）。
    - 特点：数据更详细，可用于深入分析和流程重建。当前内存实现下数据会在服务重启后丢失，但架构设计支持未来切换到持久化存储（如数据库）。
    - 返回特定的 Pydantic 模型列表或对象（非 `ApiResponse` 格式）。
    - 主要端点包括：
      - `/logs/*`: 查询 LLM 交互日志 (`LLMInteractionLog`)。**可以通过 `run_id` 和可选的 `agent_name` 进行过滤。**
      - `/runs/*`: 查询 Agent 执行日志 (`AgentExecutionLog`) 并构建运行摘要 (`RunSummary`)、Agent 详情 (`AgentDetail`) 和工作流图 (`WorkflowFlow`)。

## 统一响应格式 (`ApiResponse`)

所有 `/api/*` 前缀的新 API 端点使用统一的 `ApiResponse` 格式，方便前端处理：

```json
{
  "success": true,
  "message": "操作成功",
  "data": {
    /* 具体响应数据, 类型取决于具体接口 */
  },
  "timestamp": "2023-04-01T12:34:56.789Z"
}
```

`/logs/` 和 `/runs/` 端点则直接返回其查询结果对应的 Pydantic 模型列表或对象。

## API Endpoint Examples

以下是一些主要 API 端点的请求和响应示例。

### `/api/agents` (基于内存状态)

**`GET /api/agents/`**

- **描述:** 列出所有已注册 Agent 的最新状态。
- **响应示例 (`ApiResponse[List[AgentInfo]]`):**
  ```json
  {
    "success": true,
    "message": "操作成功",
    "data": [
      {
        "name": "market_data_agent",
        "description": "收集市场数据",
        "state": "completed",
        "last_update": "2024-04-10T10:01:15.123Z"
      },
      {
        "name": "sentiment_agent",
        "description": "分析市场情绪",
        "state": "running",
        "last_update": "2024-04-10T10:05:30.456Z"
      },
      {
        "name": "portfolio_management_agent",
        "description": "投资组合管理",
        "state": "idle",
        "last_update": "2024-04-10T09:55:00.000Z"
      }
      // ... more agents
    ],
    "timestamp": "2024-04-10T10:10:00.789Z"
  }
  ```

**`GET /api/agents/{agent_name}`**

- **描述:** 获取特定 Agent 的详细信息。
- **响应示例 (`ApiResponse[AgentInfo]`):**
  ```json
  {
    "success": true,
    "message": "操作成功",
    "data": {
      "name": "sentiment_agent",
      "description": "分析市场情绪",
      "state": "running",
      "last_update": "2024-04-10T10:05:30.456Z"
    },
    "timestamp": "2024-04-10T10:10:05.111Z"
  }
  ```

**`GET /api/agents/{agent_name}/latest_llm_request`**

- **描述:** 获取特定 Agent 最近一次 LLM 调用的请求内容。
- **响应示例 (`ApiResponse[Dict]`):**
  ```json
  {
    "success": true,
    "message": "操作成功",
    "data": {
      "caller": {
        "function": "_call_sentiment_llm",
        "file": "E:/github/A_Share_investment_Agent/src/agents/sentiment.py",
        "line": 85
      },
      "messages": [
        {
          "role": "system",
          "content": "Analyze the sentiment of the following news."
        },
        { "role": "user", "content": "News article text..." }
      ],
      "model": "gemini-1.5-flash",
      "client_type": "google",
      "arguments": {
        "args": [
          /* serialized args */
        ]
      },
      "kwargs": { "model": "gemini-1.5-flash", "client_type": "google" }
    },
    "timestamp": "2024-04-10T10:05:28.222Z"
  }
  ```
  _注意: 如果日志记录失败（例如在 lambda 函数中调用），`messages` 字段可能为 `null`。_

**`GET /api/agents/{agent_name}/latest_llm_response`**

- **描述:** 获取特定 Agent 最近一次 LLM 调用的响应内容。
- **响应示例 (`ApiResponse[Dict]`):**
  ```json
  {
    "success": true,
    "message": "操作成功",
    "data": {
      "content": "{\"sentiment_score\": 0.7, \"reasoning\": \"Positive news mentioning contract win.\"}",
      "response_metadata": {
        /* LLM provider specific metadata */
      }
    },
    "timestamp": "2024-04-10T10:05:29.333Z"
  }
  ```

### `/api/analysis` (基于内存状态)

**`POST /api/analysis/start`**

- **描述:** 启动一个新的股票分析任务。
- **请求体示例 (`StockAnalysisRequest`):**
  ```json
  {
    "ticker": "000001",
    "show_reasoning": true,
    "num_of_news": 5,
    "initial_capital": 100000.0,
    "initial_position": 0
  }
  ```
- **响应示例 (`ApiResponse[Dict]`):**
  ```json
  {
    "success": true,
    "message": "分析任务已启动",
    "data": {
      "run_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "message": "分析任务已成功启动，运行 ID 为 a1b2c3d4-e5f6-7890-1234-567890abcdef"
    },
    "timestamp": "2024-04-10T11:00:01.999Z"
  }
  ```

### `/api/runs` (基于内存状态)

**`GET /api/runs/`**

- **描述:** 获取内存中记录的运行历史列表。
- **响应示例 (`List[RunInfo]`):**
  ```json
  [
    {
      "run_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "start_time": "2024-04-10T11:00:01.999Z",
      "end_time": null,
      "status": "running",
      "ticker": "000001"
    },
    {
      "run_id": "fedcba98-7654-3210-0987-654321fedcba",
      "start_time": "2024-04-10T10:30:00.111Z",
      "end_time": "2024-04-10T10:45:12.555Z",
      "status": "completed",
      "ticker": "600519"
    }
    // ... more runs (up to limit)
  ]
  ```

**`GET /api/runs/{run_id}`**

- **描述:** 获取内存中特定运行的详细信息。
- **响应示例 (`ApiResponse[RunInfo]`):**
  ```json
  {
    "success": true,
    "message": "操作成功",
    "data": {
      "run_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "start_time": "2024-04-10T11:00:01.999Z",
      "end_time": null,
      "status": "running",
      "ticker": "000001"
    },
    "timestamp": "2024-04-10T11:05:00.321Z"
  }
  ```

### `/api/workflow` (基于内存状态)

**`GET /api/workflow/status`**

- **描述:** 获取当前正在运行的工作流状态。
- **响应示例 (运行中) (`ApiResponse[Dict]`):**
  ```json
  {
    "success": true,
    "message": "操作成功",
    "data": {
      "status": "running",
      "run_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "start_time": "2024-04-10T11:00:01.999Z",
      "agents": [
        {
          "name": "market_data_agent",
          "description": "收集市场数据",
          "state": "completed",
          "last_update": "2024-04-10T11:01:05.123Z"
        },
        {
          "name": "sentiment_agent",
          "description": "分析市场情绪",
          "state": "running",
          "last_update": "2024-04-10T11:05:30.456Z"
        }
        // ... other active agents
      ]
    },
    "timestamp": "2024-04-10T11:05:35.888Z"
  }
  ```
- **响应示例 (空闲) (`ApiResponse[Dict]`):**
  ```json
  {
    "success": true,
    "message": "操作成功",
    "data": {
      "status": "idle",
      "message": "当前没有运行中的工作流"
    },
    "timestamp": "2024-04-10T12:00:00.111Z"
  }
  ```

### `/logs` (基于日志存储)

**`GET /logs/`**

- **描述:** 查询 LLM 交互日志 (`LLMInteractionLog`)。可以通过 `run_id` 查询特定运行的所有 LLM 交互，或通过 `run_id` 和 `agent_name` 查询特定 Agent 的交互。
- **响应示例 (`List[LLMInteractionLog]`):**
  ```json
  [
    {
      "agent_name": "debate_room_agent",
      "run_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "request_data": {
        "caller": {
          /* ... */
        },
        "messages": [
          /* ... */
        ]
        /* ... */
      },
      "response_data": {
        "content": "{\"analysis\": \"...\", \"score\": 0.2, \"reasoning\": \"...\"}"
        /* ... */
      },
      "timestamp": "2024-04-10T11:15:45.678Z"
    },
    {
      "agent_name": "sentiment_agent",
      "run_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "request_data": {
        /* ... */
      },
      "response_data": {
        /* ... */
      },
      "timestamp": "2024-04-10T11:05:29.333Z"
    }
    // ... more logs (potentially filtered by query params)
  ]
  ```

### `/runs` (基于日志存储)

**`GET /runs/`**

- **描述:** 获取基于日志存储记录的运行历史摘要列表。
- **响应示例 (`List[RunSummary]`):**
  ```json
  [
    {
      "run_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "start_time": "2024-04-10T11:00:05.123Z", // Min start time from Agent logs
      "end_time": "2024-04-10T11:20:30.999Z", // Max end time from Agent logs
      "agents_executed": [
        "market_data_agent",
        "sentiment_agent",
        "technical_analyst_agent",
        // ... other agents in this run
        "portfolio_management_agent"
      ],
      "status": "completed"
    }
    // ... more runs (up to limit)
  ]
  ```

**`GET /runs/{run_id}`**

- **描述:** 获取特定运行的摘要信息。
- **响应示例 (`RunSummary`):**
  ```json
  {
    "run_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "start_time": "2024-04-10T11:00:05.123Z",
    "end_time": "2024-04-10T11:20:30.999Z",
    "agents_executed": [
      /* ... */
    ],
    "status": "completed"
  }
  ```

**`GET /runs/{run_id}/agents`**

- **描述:** 获取特定运行中所有 Agent 的执行摘要。
- **响应示例 (`List[AgentSummary]`):**
  ```json
  [
    {
      "agent_name": "market_data_agent",
      "start_time": "2024-04-10T11:00:05.123Z",
      "end_time": "2024-04-10T11:01:05.123Z",
      "execution_time_seconds": 60.0,
      "status": "completed"
    },
    {
      "agent_name": "sentiment_agent",
      "start_time": "2024-04-10T11:01:06.000Z",
      "end_time": "2024-04-10T11:05:30.456Z",
      "execution_time_seconds": 264.456,
      "status": "completed"
    }
    // ... sorted by start_time
  ]
  ```

**`GET /runs/{run_id}/agents/{agent_name}`**

- **描述:** 获取特定 Agent 在特定运行中的详细执行情况。
- **响应示例 (`AgentDetail`):**
  ```json
  {
    "agent_name": "sentiment_agent",
    "start_time": "2024-04-10T11:01:06.000Z",
    "end_time": "2024-04-10T11:05:30.456Z",
    "execution_time_seconds": 264.456,
    "status": "completed",
    "input_state": {
      /* Serialized input state data */
    },
    "output_state": {
      /* Serialized output state data */
    },
    "reasoning": {
      /* Reasoning details if available */
    },
    "llm_interactions": ["0", "1"] // Indices corresponding to LLM logs for this agent/run
  }
  ```

**`GET /runs/{run_id}/flow`**

- **描述:** 获取特定运行的工作流程图数据。
- **响应示例 (`WorkflowFlow`):**
  ```json
  {
    "run_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "start_time": "2024-04-10T11:00:05.123Z",
    "end_time": "2024-04-10T11:20:30.999Z",
    "agents": {
      "market_data_agent": {
        /* AgentSummary */
      },
      "sentiment_agent": {
        /* AgentSummary */
      }
      // ... all agents in this run
    },
    "state_transitions": [
      {
        "from_agent": "start",
        "to_agent": "market_data_agent",
        "state_size": 150, // Example state size
        "timestamp": "2024-04-10T11:00:05.123Z"
      },
      {
        "from_agent": "market_data_agent",
        "to_agent": "sentiment_agent",
        "state_size": 1024,
        "timestamp": "2024-04-10T11:01:06.000Z"
      },
      // ... more transitions
      {
        "from_agent": "portfolio_management_agent",
        "to_agent": "end",
        "state_size": 512,
        "timestamp": "2024-04-10T11:20:30.999Z"
      }
    ],
    "final_decision": "{\"action\": \"buy\", \"quantity\": 100, \"confidence\": 0.65, ...}"
  }
  ```

## 数据访问说明

理解不同接口的数据来源至关重要：

- **实时/最新状态 (`/api/*`)**: 这些接口查询 `backend.state.api_state`。`api_state` 是一个**内存对象**，用于快速访问 Agent 的**最新**状态、输入/输出、LLM 交互以及**内存中记录**的运行摘要。**此数据在服务重启后会丢失。**

- **历史/详细日志 (`/`, `/logs/`, `/runs/`)**: 这些接口查询 `backend.storage.BaseLogStorage`。该存储记录了 Agent 执行的**详细步骤** (`AgentExecutionLog`) 和 LLM 的**每一次交互** (`LLMInteractionLog`)。当前默认实现 `InMemoryLogStorage` 也是内存型的，**日志会在重启后丢失**，但可以通过更换 `BaseLogStorage` 的实现（如改为数据库存储）来持久化这些日志，**无需修改 API 代码**（TODO）。

  - **`GET /runs/` (获取最近运行列表 - 基于日志存储)**: 此接口查询 `BaseLogStorage` (当前为内存实现 `InMemoryLogStorage`) 中的 `AgentExecutionLog` 记录，返回最近完成的工作流运行摘要 (`RunSummary`)。 注意：基于内存的日志在服务重启后会丢失。 _TODO: 通过依赖注入 `BaseLogStorage` 的不同实现 (如数据库存储)，可以轻松切换到底层存储，无需修改此接口代码。_

## 日志记录机制

- **Agent 执行日志**: 由 `src.utils.api_utils` 中的 `@agent_endpoint` 装饰器负责记录。它会将 `AgentExecutionLog` 同时写入 `BaseLogStorage`（供 `/runs/*` 使用）并更新 `api_state` 中的 Agent 最新状态（供 `/api/agents/*` 使用）。
- **LLM 交互日志**: 由 `src.utils.api_utils` 中的 `@log_llm_interaction` 装饰器负责记录。它需要被显式应用到调用 LLM（如 `get_chat_completion`）的 Agent 函数或其辅助函数上。**此装饰器会尝试从被装饰函数的参数中提取 `messages` 信息。如果 LLM 调用发生在匿名函数 (lambda) 内部，装饰器可能无法正确获取 `messages`，导致日志记录不完整（例如 `messages: null`）。推荐将 lambda 中的 LLM 调用提取到独立的、使用该装饰器修饰的辅助函数中，以确保日志记录的准确性 (参考 `src/agents/debate_room.py` 中的处理方式建议)。** 它会将 `LLMInteractionLog` 同时写入 `BaseLogStorage`（供 `/logs/` 使用）并更新 `api_state` 中的 Agent 最新 LLM 交互信息（供 `/api/agents/.../latest_llm_*` 使用）。

## 开发指南

添加新的 API 端点时请遵循以下规则：

1.  根据数据来源和用途选择合适的路由前缀 (`/api/` 或 `/`) 和路由模块。
2.  如果使用 `/api/` 前缀，请使用 `ApiResponse` 包装所有响应。
3.  为接口提供清晰的文档字符串。
4.  添加适当的错误处理和日志记录。
5.  如果添加新的 Agent，确保其主函数使用 `@agent_endpoint`，并且所有调用 LLM 的地方都使用 `@log_llm_interaction`。
