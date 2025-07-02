# A股投资Agent后端系统

本项目是一个完整的前后端分离架构的投资管理系统，基于原有的多智能代理股票分析框架，扩展了用户管理、权限控制、投资组合管理等企业级功能。

## 核心特性

- 完整的用户认证和权限管理系统 (JWT + RBAC)
- 智能股票分析和多代理工作流
- 投资组合管理和交易记录
- 系统配置和参数管理
- 数据统计和报表功能
- 系统监控和日志管理
- 标准化的RESTful API接口

## 技术栈

- **Web框架**: FastAPI (Python 3.11+)
- **数据库**: SQLite (生产环境可升级到PostgreSQL)
- **认证**: JWT (JSON Web Tokens)
- **依赖管理**: Poetry
- **API文档**: OpenAPI/Swagger自动生成
- **代理框架**: LangGraph (多智能代理协作)

## 项目结构

```
AShareAgent/
├── backend/                    # 后端代码
│   ├── models/                 # 数据模型和业务逻辑
│   │   ├── auth_models.py      # 用户认证模型
│   │   ├── portfolio_models.py # 投资组合模型
│   │   ├── config_models.py    # 系统配置模型
│   │   ├── stats_models.py     # 数据统计模型
│   │   ├── monitor_models.py   # 系统监控模型
│   │   └── api_models.py       # API响应模型
│   ├── routers/                # API路由
│   │   ├── auth.py             # 认证API
│   │   ├── portfolio.py        # 投资组合API
│   │   ├── config.py           # 配置管理API
│   │   ├── stats.py            # 统计报表API
│   │   ├── monitor.py          # 系统监控API
│   │   ├── analysis.py         # 股票分析API
│   │   ├── agents.py           # 智能代理API
│   │   ├── api_runs.py         # 运行历史API (内存状态)
│   │   ├── workflow.py         # 工作流API
│   │   ├── logs.py             # 日志查询API (日志存储)
│   │   └── runs.py             # 运行详情API (日志存储)
│   ├── services/               # 业务服务
│   │   ├── auth_service.py     # 认证服务
│   │   └── analysis.py         # 分析服务
│   ├── middleware/             # 中间件
│   │   └── stats_middleware.py # API统计中间件
│   ├── storage/                # 数据存储
│   │   ├── base.py             # 存储基类
│   │   └── memory.py           # 内存存储实现
│   ├── utils/                  # 工具函数
│   │   ├── api_utils.py        # API相关工具
│   │   └── context_managers.py # 上下文管理器
│   ├── dependencies.py         # 依赖注入
│   ├── state.py                # 内存状态管理
│   ├── schemas.py              # 内部数据结构
│   └── main.py                 # 主应用程序
├── src/                        # 原有代理系统
│   ├── agents/                 # 智能代理
│   ├── database/               # 数据库模型和架构
│   │   ├── models.py           # 数据库管理器
│   │   └── schema.sql          # 数据库架构
│   └── workflow/               # 工作流引擎
├── scripts/                    # 初始化脚本
│   └── init_agents.py          # 代理初始化
└── comprehensive_test.py       # 综合测试脚本
```

## 数据库架构

### 核心表结构

#### 用户管理表
- `users` - 用户基础信息
- `roles` - 角色定义
- `permissions` - 权限定义
- `user_roles` - 用户角色关联
- `role_permissions` - 角色权限关联

#### 业务功能表
- `user_portfolios` - 用户投资组合
- `user_holdings` - 持仓信息
- `user_transactions` - 交易记录
- `user_analysis_tasks` - 用户分析任务
- `system_config` - 系统配置

#### 监控统计表
- `api_usage_stats` - API使用统计
- `system_logs` - 系统操作日志

#### 原有数据表
- `stock_news` - 股票新闻
- `stock_price_data` - 股价数据
- `technical_indicators` - 技术指标
- 其他代理和分析相关表

## API架构

### 基于内存状态的API (`/api/*`)

提供Agent最新状态、运行摘要和实时工作流信息的接口。数据主要来源于内存中的`api_state`对象。特点：响应快速，反映最新情况，但数据会在服务重启后丢失。使用统一的`ApiResponse`格式包装响应数据。

#### 认证系统 (`/api/auth/`)
- `POST /register` - 用户注册
- `POST /login` - 用户登录
- `GET /me` - 获取当前用户信息
- `GET /users` - 用户列表 (管理员)
- `POST /users/{user_id}/roles` - 分配角色 (管理员)

#### 投资组合管理 (`/api/portfolios/`)
- `GET /` - 获取用户投资组合列表
- `POST /` - 创建新投资组合
- `GET /{portfolio_id}/summary` - 获取组合详情
- `POST /{portfolio_id}/transactions` - 记录交易
- `GET /{portfolio_id}/holdings` - 获取持仓信息

#### 系统配置 (`/api/config/`)
- `GET /` - 获取配置列表
- `POST /` - 创建配置项
- `GET /{key}` - 获取特定配置
- `PUT /{key}` - 更新配置
- `DELETE /{key}` - 删除配置

#### 数据统计 (`/api/stats/`)
- `GET /users` - 用户统计
- `GET /analysis` - 分析任务统计
- `GET /portfolios` - 投资组合统计
- `GET /system` - 系统统计
- `GET /api` - API调用统计
- `GET /overview` - 综合统计

#### 系统监控 (`/api/monitor/`)
- `GET /health` - 系统健康检查
- `GET /metrics` - 系统性能指标
- `GET /logs` - 系统日志
- `GET /dashboard` - 监控仪表板
- `GET /alerts` - 系统告警

#### 股票分析 (`/api/analysis/`)
- `POST /start` - 启动股票分析
- `GET /history` - 分析历史
- `GET /status/{task_id}` - 查询分析状态
- `GET /{run_id}/result` - 获取分析结果

#### 智能代理 (`/api/agents/`)
- `GET /` - 获取代理列表
- `GET /{agent_name}` - 获取代理详情
- `GET /{agent_name}/latest_llm_request` - 获取最新LLM请求
- `GET /{agent_name}/latest_llm_response` - 获取最新LLM响应

#### 运行历史 (`/api/runs/`)
- `GET /` - 获取运行历史列表 (内存状态)
- `GET /{run_id}` - 获取运行详情 (内存状态)

#### 工作流 (`/api/workflow/`)
- `GET /status` - 获取工作流状态

### 基于日志存储的API

提供详细的运行历史、Agent执行步骤和LLM交互日志的接口。数据来源于`BaseLogStorage`接口（当前默认为`InMemoryLogStorage`）。特点：数据更详细，可用于深入分析和流程重建。

#### 日志查询 (`/logs/`)
- `GET /` - 查询LLM交互日志，可通过`run_id`和`agent_name`过滤

#### 运行详情 (`/runs/`)
- `GET /` - 获取运行历史摘要列表 (基于日志存储)
- `GET /{run_id}` - 获取特定运行摘要
- `GET /{run_id}/agents` - 获取运行中所有Agent执行摘要
- `GET /{run_id}/agents/{agent_name}` - 获取特定Agent执行详情
- `GET /{run_id}/flow` - 获取工作流程图数据

## 统一响应格式

所有`/api/*`前缀的API端点使用统一的`ApiResponse`格式：

```json
{
  "success": true,
  "message": "操作成功",
  "data": {
    // 具体响应数据，类型取决于具体接口
  },
  "timestamp": "2023-04-01T12:34:56.789Z"
}
```

`/logs/`和`/runs/`端点则直接返回其查询结果对应的Pydantic模型列表或对象。

## 权限系统

### 角色定义
- **管理员 (admin)**: 全系统管理权限
- **普通用户 (user)**: 基础功能使用权限
- **分析师 (analyst)**: 高级分析功能权限

### 权限控制
- **基于JWT令牌的身份认证**
- **RBAC (Role-Based Access Control) 权限模型**
- **API级别的权限检查**
- **资源级别的访问控制**

## 业务功能

### 投资组合管理
- **多组合支持**: 用户可创建多个投资组合
- **交易记录**: 完整的买入/卖出交易历史
- **持仓跟踪**: 实时计算持仓数量和价值
- **收益计算**: 自动计算投资收益和收益率

### 股票分析
- **多代理协作**: 12个专业分析代理
- **全面分析**: 技术分析、基本面分析、情感分析
- **实时数据**: 集成多个数据源
- **历史跟踪**: 完整的分析任务历史

### 系统配置
- **灵活配置**: 支持字符串、数字、布尔值、JSON配置
- **分类管理**: 按类别组织配置项
- **类型验证**: 自动验证配置值类型
- **版本控制**: 配置变更历史跟踪

## 监控和统计

### API使用统计
- 自动记录所有已认证用户的API调用
- 统计响应时间、状态码、调用频率
- 支持按用户、端点、时间范围分析

### 系统监控
- 数据库健康检查
- API性能监控
- 存储空间监控
- 错误率和响应时间统计

### 日志管理
- 用户操作日志记录
- 系统错误日志跟踪
- 分类和过滤功能
- 日志统计和分析

## 日志记录机制

- **Agent执行日志**: 由`src.utils.api_utils`中的`@agent_endpoint`装饰器负责记录
- **LLM交互日志**: 由`src.utils.api_utils`中的`@log_llm_interaction`装饰器负责记录

注意：如果LLM调用发生在匿名函数(lambda)内部，装饰器可能无法正确获取`messages`，导致日志记录不完整。推荐将lambda中的LLM调用提取到独立的、使用该装饰器修饰的辅助函数中。

## 安全特性

### 认证安全
- **密码加密**: bcrypt哈希加密
- **令牌机制**: JWT访问令牌和刷新令牌
- **令牌过期**: 可配置的令牌有效期
- **权限检查**: 每个API端点的权限验证

### 数据安全
- **参数验证**: Pydantic模型验证所有输入
- **SQL注入防护**: 使用参数化查询
- **CORS配置**: 跨域请求控制
- **错误处理**: 安全的错误信息返回

## 部署和运维

### 开发环境
```bash
# 使用Poetry管理依赖
poetry install

# 启动后端服务
poetry run python run_with_backend.py
```

### 生产环境建议
- 使用Gunicorn + Uvicorn异步部署
- 配置Nginx反向代理
- 使用PostgreSQL替代SQLite
- 配置Redis用于会话管理
- 设置日志轮转和监控告警

### 环境变量配置
```bash
# 数据库配置
DATABASE_URL=sqlite:///./data/stock_agent.db

# JWT配置
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 其他配置...
```

### API文档
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 数据访问说明

- **实时/最新状态 (`/api/*`)**: 查询`backend.state.api_state`内存对象，提供快速访问Agent最新状态。数据在服务重启后会丢失。

- **历史/详细日志 (`/`, `/logs/`, `/runs/`)**: 查询`backend.storage.BaseLogStorage`，记录Agent执行详细步骤和LLM交互。当前默认实现为内存型，可通过更换实现来持久化日志。

## 开发指南

添加新的API端点时请遵循以下规则：

1. 根据数据来源和用途选择合适的路由前缀(`/api/`或`/`)和路由模块
2. 如果使用`/api/`前缀，请使用`ApiResponse`包装所有响应
3. 为接口提供清晰的文档字符串
4. 添加适当的错误处理和日志记录
5. 如果添加新的Agent，确保其主函数使用`@agent_endpoint`，并且所有调用LLM的地方都使用`@log_llm_interaction`

## 错误码说明

- `200` - 成功
- `400` - 请求参数错误
- `401` - 未认证
- `403` - 权限不足
- `404` - 资源不存在
- `422` - 数据验证失败
- `500` - 服务器内部错误