# A股投资Agent系统

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.1+-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-3178C6.svg)](https://www.typescriptlang.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.56-orange.svg)](https://langchain-ai.github.io/langgraph/)

## 项目概述

A股投资Agent系统是一个基于人工智能的投资决策支持系统，通过多Agent协同工作，结合大型语言模型(LLM)的分析能力，为A股投资提供全方位的分析和决策支持。

### 核心特性

- 🤖 **多Agent协同**: 12个专业Agent独立分析，从多角度评估投资机会
- 🧠 **LLM增强决策**: 集成Gemini/OpenAI等LLM进行深度分析
- 🎯 **辩论室机制**: 多空对决，确保决策的全面性和客观性
- 📊 **智能回测**: 支持细粒度频率控制的回测系统
- 🌐 **前后端分离**: React + FastAPI架构，支持Web界面和API调用
- 🔄 **实时监控**: 完整的日志系统和Agent状态监控

## 系统架构

### 系统整体架构图

```mermaid
graph TB
    subgraph "前端层 (React + TypeScript)"
        A[用户界面]
        B[股票分析界面]
        C[策略回测界面]
        D[Agent管理界面]
        E[投资组合界面]
    end
    
    subgraph "后端层 (FastAPI + Python)"
        F[API网关]
        G[认证授权服务]
        H[业务服务层]
        I[任务调度器]
    end
    
    subgraph "Agent层 (LangGraph工作流)"
        J[市场数据Agent]
        K[技术分析Agent]
        L[基本面Agent]
        M[情感分析Agent]
        N[估值分析Agent]
        O[宏观分析Agent]
        P[辩论室Agent]
        Q[风险管理Agent]
        R[投资组合Agent]
    end
    
    subgraph "数据层"
        S[(SQLite/PostgreSQL)]
        T[Redis缓存]
        U[文件存储]
        V[外部API]
    end
    
    A --> F
    B --> F
    C --> F
    D --> F
    E --> F
    
    F --> G
    F --> H
    H --> I
    
    I --> J
    J --> K
    J --> L
    J --> M
    J --> N
    J --> O
    K --> P
    L --> P
    M --> P
    N --> P
    O --> P
    P --> Q
    Q --> R
    
    H --> S
    H --> T
    H --> U
    J --> V
    
    style A fill:#e1f5fe
    style F fill:#f3e5f5
    style J fill:#e8f5e8
    style S fill:#fff3e0
```

### Agent工作流程图

```mermaid
graph TD
    START([开始]) --> A[Market Data Agent<br/>市场数据收集]
    
    A --> B[Technical Analyst<br/>技术分析]
    A --> C[Fundamentals Analyst<br/>基本面分析]
    A --> D[Sentiment Analyst<br/>情感分析]
    A --> E[Valuation Analyst<br/>估值分析]
    A --> F[Macro News Agent<br/>宏观新闻分析]
    
    B --> G[Researcher Bull<br/>多方研究员]
    C --> G
    D --> G
    E --> G
    
    B --> H[Researcher Bear<br/>空方研究员]
    C --> H
    D --> H
    E --> H
    
    G --> I[Debate Room<br/>辩论室]
    H --> I
    
    I --> J[Risk Manager<br/>风险管理]
    
    J --> K[Macro Analyst<br/>宏观分析师]
    
    K --> L[Portfolio Manager<br/>投资组合管理]
    F --> L
    
    L --> END([投资决策输出])
    
    subgraph "数据收集层"
        A
        F
    end
    
    subgraph "分析执行层"
        B
        C
        D
        E
    end
    
    subgraph "研究决策层"
        G
        H
        I
    end
    
    subgraph "风险控制层"
        J
        K
        L
    end
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#f3e5f5
    style D fill:#f3e5f5
    style E fill:#f3e5f5
    style F fill:#e1f5fe
    style G fill:#e8f5e8
    style H fill:#ffebee
    style I fill:#fff3e0
    style J fill:#fce4ec
    style K fill:#e0f2f1
    style L fill:#e8eaf6
```

### 系统网络拓扑结构图

```mermaid
graph LR
    subgraph "用户端"
        User1[个人投资者]
        User2[机构投资者]
        User3[金融从业人员]
    end
    
    subgraph "Internet"
        CDN[内容分发网络]
        LB[负载均衡器]
    end
    
    subgraph "DMZ区"
        WAF[Web应用防火墙]
        Proxy[反向代理]
    end
    
    subgraph "应用服务器集群"
        Web1[Web服务器1]
        Web2[Web服务器2]
        API1[API服务器1]
        API2[API服务器2]
    end
    
    subgraph "Agent计算集群"
        Agent1[Agent节点1]
        Agent2[Agent节点2]
        Agent3[Agent节点3]
    end
    
    subgraph "数据层"
        DB1[(主数据库)]
        DB2[(备份数据库)]
        Redis[(缓存集群)]
    end
    
    subgraph "外部服务"
        DataAPI[市场数据API]
        NewsAPI[新闻数据API]
        LLM[大语言模型API]
    end
    
    User1 -.->|HTTPS| CDN
    User2 -.->|HTTPS| CDN
    User3 -.->|HTTPS| CDN
    
    CDN --> LB
    LB --> WAF
    WAF --> Proxy
    
    Proxy --> Web1
    Proxy --> Web2
    Proxy --> API1
    Proxy --> API2
    
    API1 --> Agent1
    API1 --> Agent2
    API2 --> Agent2
    API2 --> Agent3
    
    Agent1 --> DB1
    Agent2 --> DB1
    Agent3 --> DB1
    DB1 -.->|同步| DB2
    
    Agent1 --> Redis
    Agent2 --> Redis
    Agent3 --> Redis
    
    Agent1 -.->|API调用| DataAPI
    Agent2 -.->|API调用| NewsAPI
    Agent3 -.->|API调用| LLM
    
    style User1 fill:#e3f2fd
    style CDN fill:#f3e5f5
    style Agent1 fill:#e8f5e8
    style DB1 fill:#fff3e0
```

### 投资分析活动图

```mermaid
flowchart TD
    Start([开始投资分析]) --> Input[输入股票代码和参数]
    Input --> DataCollect[市场数据收集]
    
    DataCollect --> ParallelStart{开始并行分析}
    
    ParallelStart --> Technical[技术分析]
    ParallelStart --> Fundamental[基本面分析]
    ParallelStart --> Sentiment[情绪分析]
    ParallelStart --> Valuation[估值分析]
    ParallelStart --> MacroNews[宏观新闻分析]
    
    Technical --> WaitSync[等待并行分析完成]
    Fundamental --> WaitSync
    Sentiment --> WaitSync
    Valuation --> WaitSync
    
    WaitSync --> BullResearch[多方研究员分析]
    WaitSync --> BearResearch[空方研究员分析]
    
    BullResearch --> Debate[多空辩论]
    BearResearch --> Debate
    
    Debate --> LLMEval[LLM第三方评估]
    LLMEval --> Risk[风险管理评估]
    Risk --> MacroAnalyst[宏观分析师]
    
    MacroAnalyst --> Portfolio[投资组合管理]
    MacroNews --> Portfolio
    
    Portfolio --> Decision{生成投资决策}
    Decision --> Buy[买入建议]
    Decision --> Sell[卖出建议]
    Decision --> Hold[持有建议]
    
    Buy --> End([结束])
    Sell --> End
    Hold --> End
    
    style Technical fill:#e1f5fe
    style Fundamental fill:#e8f5e8
    style Sentiment fill:#fff3e0
    style Valuation fill:#f3e5f5
    style MacroNews fill:#e0f2f1
    style Debate fill:#ffebee
    style Portfolio fill:#e8eaf6
```

## 技术栈

### 后端技术
- **Python 3.9+** - 核心开发语言
- **FastAPI** - 高性能Web框架
- **LangGraph** - Agent工作流编排
- **SQLite/PostgreSQL** - 数据存储
- **Redis** - 缓存系统
- **Pydantic** - 数据验证和序列化

### 前端技术
- **React 19.1+** - 用户界面框架
- **TypeScript** - 类型安全的JavaScript
- **Ant Design** - UI组件库
- **Vite** - 构建工具
- **Axios** - HTTP客户端

### AI/数据技术
- **LangChain** - LLM应用框架
- **OpenAI API** - 大语言模型
- **Google Gemini** - 谷歌AI模型
- **AkShare** - A股数据获取
- **Pandas/NumPy** - 数据处理
- **Matplotlib** - 数据可视化

## 快速开始

### 环境要求
- Python 3.9+
- Node.js 16+
- Poetry (Python包管理器)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/AShareAgent.git
cd AShareAgent
```

2. **安装Poetry**
```bash
# Windows PowerShell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# Unix/macOS
curl -sSL https://install.python-poetry.org | python3 -
```

3. **安装后端依赖**
```bash
poetry install
```

4. **安装前端依赖**
```bash
cd frontend
npm install
cd ..
```

5. **配置环境变量**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入API密钥
nano .env
```

环境变量配置：
```env
# Gemini API 配置
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash

# OpenAI Compatible API 配置（可选）
OPENAI_COMPATIBLE_API_KEY=your-openai-compatible-api-key
OPENAI_COMPATIBLE_BASE_URL=https://your-api-endpoint.com/v1
OPENAI_COMPATIBLE_MODEL=your-model-name
```

### 运行系统

#### 方式1：完整系统（推荐）
```bash
# 启动后端API服务
poetry run python run_with_backend.py

# 在新终端启动前端
cd frontend
npm run dev
```

访问 http://localhost:5173 使用Web界面

#### 用户认证流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as 前端LoginForm
    participant A as 认证API
    participant S as 认证服务
    participant D as 数据库
    participant T as JWT令牌
    
    U->>F: 输入用户名密码
    F->>F: 表单验证
    F->>A: POST /auth/login
    A->>S: authenticate_user()
    S->>D: 查询用户信息
    D-->>S: 返回用户数据
    S->>S: verify_password()
    
    alt 认证成功
        S->>T: create_access_token()
        T-->>S: 返回JWT令牌
        S-->>A: 用户信息+令牌
        A-->>F: ApiResponse(success=true)
        F->>F: 保存令牌到localStorage
        F->>F: 更新用户状态
        F-->>U: 跳转到主页面
    else 认证失败
        S-->>A: 认证失败错误
        A-->>F: ApiResponse(success=false)
        F-->>U: 显示错误信息
    end
    
    Note over F,T: 后续请求携带JWT令牌进行权限验证
    
    F->>A: 请求受保护资源 (Bearer Token)
    A->>S: verify_token()
    S->>T: 解码验证JWT
    T-->>S: 令牌有效性
    
    alt 令牌有效
        S->>D: 获取用户权限
        D-->>S: 权限信息
        S-->>A: 权限验证通过
        A-->>F: 返回请求资源
    else 令牌无效
        S-->>A: 权限验证失败
        A-->>F: 401 Unauthorized
        F->>F: 清除本地令牌
        F-->>U: 重定向到登录页
    end
```

#### 方式2：命令行分析
```bash
# 基本分析
poetry run python src/main.py --ticker 000001

# 显示详细推理过程
poetry run python src/main.py --ticker 000001 --show-reasoning

# 智能回测
poetry run python src/backtesting/backtester.py --ticker 600519 --start-date 2024-01-01 --end-date 2024-12-31
```

## 核心功能

### 1. 多Agent协同分析
- **市场数据Agent**: 收集股票行情、财务数据
- **技术分析Agent**: 计算技术指标，识别趋势
- **基本面Agent**: 分析财务报表，评估基本面
- **情感分析Agent**: 分析新闻情绪，评估市场氛围
- **估值分析Agent**: DCF估值，相对估值分析
- **宏观分析Agent**: 宏观经济环境分析

### 2. 辩论室机制

#### Agent工作流执行时序图

```mermaid
sequenceDiagram
    participant W as 工作流引擎
    participant M as Market Data Agent
    participant T as Technical Agent
    participant F as Fundamentals Agent
    participant S as Sentiment Agent
    participant V as Valuation Agent
    participant B as Bull Researcher
    participant Bear as Bear Researcher
    participant D as Debate Room
    participant R as Risk Manager
    participant P as Portfolio Manager
    participant L as LLM API
    participant Cache as 缓存管理器
    
    W->>M: 启动市场数据收集
    M->>Cache: 检查价格数据缓存
    alt 缓存命中
        Cache-->>M: 返回缓存数据
    else 缓存未命中
        M->>外部API: 获取股票数据
        外部API-->>M: 返回市场数据
        M->>Cache: 更新缓存
    end
    M-->>W: 市场数据就绪
    
    par 并行执行分析Agent
        W->>T: 执行技术分析
        T->>T: 计算技术指标
        T-->>W: 技术分析结果
    and
        W->>F: 执行基本面分析
        F->>F: 分析财务指标
        F-->>W: 基本面分析结果
    and
        W->>S: 执行情感分析
        S->>S: 分析新闻情感
        S-->>W: 情感分析结果
    and
        W->>V: 执行估值分析
        V->>V: DCF估值计算
        V-->>W: 估值分析结果
    end
    
    W->>B: 启动多方研究员
    B->>B: 收集看多论点
    B-->>W: 多方观点
    
    W->>Bear: 启动空方研究员
    Bear->>Bear: 收集看空论点
    Bear-->>W: 空方观点
    
    W->>D: 启动辩论室分析
    D->>D: 收集多空观点
    D->>L: 请求LLM第三方分析
    L-->>D: LLM客观评估
    D->>D: 计算混合置信度
    D->>D: 应用A股特色调整
    D-->>W: 辩论结论
    
    W->>R: 启动风险管理
    R->>R: 评估投资风险
    R->>R: 计算仓位限制
    R-->>W: 风险评估结果
    
    W->>P: 启动投资组合管理
    P->>P: 综合所有信号
    P->>P: 应用A股权重策略
    P->>L: 生成最终决策
    L-->>P: 投资决策建议
    P-->>W: 最终投资决策
    
    W-->>用户: 返回完整分析结果
```

**特性说明**:
- **多方研究员**: 收集看多论据
- **空方研究员**: 收集看空论据  
- **辩论室**: LLM第三方客观评估
- **混合置信度**: 多方信息融合决策

### 3. 智能回测系统

#### 回测系统缓存机制

```mermaid
graph TB
    subgraph "回测引擎"
        A[IntelligentBacktester]
        B[频率控制器]
        C[执行调度器]
    end
    
    subgraph "缓存管理层"
        D[CacheManager]
        E[数据缓存池]
        F[结果缓存池]
        G[缓存统计器]
    end
    
    subgraph "Agent执行层"
        H[Agent决策引擎]
        I[完整工作流]
        J[简化工作流]
    end
    
    subgraph "数据源"
        K[股价API]
        L[财务数据API]
        M[新闻数据API]
    end
    
    A --> B
    B --> C
    C --> D
    
    D --> E
    D --> F
    D --> G
    
    D --> H
    H --> I
    H --> J
    
    E --> K
    E --> L
    E --> M
    
    subgraph "缓存流程"
        direction TB
        N[请求数据] --> O{检查缓存}
        O -->|命中| P[返回缓存数据]
        O -->|未命中| Q[调用API获取]
        Q --> R[更新缓存]
        R --> S[返回新数据]
        P --> T[统计命中率]
        S --> T
    end
    
    subgraph "缓存键策略"
        U[股票代码+日期范围<br/>price_data_600519_2024-01-01_2024-12-31]
        V[Agent组合+日期<br/>agent_result_2024-01-15_tech-fund-sent]
        W[市场条件+参数<br/>market_condition_volatility_0.05]
    end
    
    subgraph "性能优化效果"
        X[缓存命中率: 60%<br/>执行优化率: 45%<br/>API调用减少: 50%]
    end
    
    D -.-> N
    E -.-> U
    F -.-> V
    G -.-> X
    
    style A fill:#e3f2fd
    style D fill:#e8f5e8
    style E fill:#fff3e0
    style F fill:#f3e5f5
    style K fill:#ffebee
    style X fill:#e0f2f1
```

**特性说明**:
- **频率控制**: 不同Agent可配置不同执行频率
- **缓存优化**: 智能缓存减少API调用
- **性能分析**: 详细的回测报告和可视化
- **风险管理**: 动态止损和仓位管理

### 4. Web界面管理

#### 前端组件架构

```mermaid
graph TB
    subgraph "应用层 (App.tsx)"
        A[主应用组件]
        B[路由管理]
        C[权限控制]
        D[全局状态]
    end
    
    subgraph "页面层 (Pages)"
        E[股票分析页面]
        F[策略回测页面]
        G[Agent管理页面]
        H[投资组合页面]
        I[系统设置页面]
    end
    
    subgraph "业务组件层 (Components)"
        J[AnalysisForm<br/>分析表单]
        K[AnalysisStatus<br/>状态监控]
        L[BacktestForm<br/>回测配置]
        M[BacktestVisualization<br/>结果可视化]
        N[AgentMonitor<br/>Agent监控]
        O[PortfolioManagement<br/>组合管理]
    end
    
    subgraph "UI组件层 (UI Components)"
        P[Button按钮]
        Q[Form表单]
        R[Table表格]
        S[Chart图表]
        T[Modal弹窗]
        U[Loading加载]
    end
    
    subgraph "服务层 (Services)"
        V[ApiService<br/>API调用]
        W[AuthService<br/>认证服务]
        X[CacheService<br/>缓存服务]
        Y[UtilService<br/>工具函数]
    end
    
    subgraph "状态管理 (State)"
        Z[Context全局状态]
        AA[useState本地状态]
        BB[useEffect副作用]
        CC[自定义Hooks]
    end
    
    A --> B
    A --> C
    A --> D
    
    B --> E
    B --> F
    B --> G
    B --> H
    B --> I
    
    E --> J
    E --> K
    F --> L
    F --> M
    G --> N
    H --> O
    
    J --> P
    J --> Q
    K --> R
    K --> U
    L --> Q
    L --> P
    M --> S
    M --> R
    N --> R
    N --> S
    O --> R
    O --> T
    
    J --> V
    K --> V
    L --> V
    M --> V
    N --> V
    O --> V
    
    V --> W
    V --> X
    V --> Y
    
    E --> Z
    F --> AA
    G --> BB
    H --> CC
    
    style A fill:#e3f2fd
    style V fill:#f3e5f5
    style J fill:#e8f5e8
    style S fill:#fff3e0
    style Z fill:#fce4ec
```

**特性说明**:
- **实时监控**: Agent状态和执行进度
- **历史记录**: 分析历史和决策轨迹
- **参数配置**: 灵活的策略参数调整
- **报告导出**: 分析报告和图表导出

## 使用示例

### 单只股票分析
```bash
# 分析贵州茅台
poetry run python src/main.py --ticker 600519 --show-reasoning
```

### 批量回测
```bash
# 贵州茅台2024年回测
poetry run python src/backtesting/backtester.py \
    --ticker 600519 \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --technical-freq daily \
    --fundamentals-freq weekly \
    --valuation-freq monthly
```

### API调用
```python
import requests

# 启动分析任务
response = requests.post("http://localhost:8000/analysis/start", json={
    "ticker": "600519",
    "initial_capital": 100000,
    "num_of_news": 20
})

# 查看分析结果
result = response.json()
print(result)
```

## 项目结构

```
AShareAgent/
├── backend/                    # 后端API服务
│   ├── main.py                # FastAPI应用
│   ├── routers/               # API路由
│   ├── services/              # 业务逻辑
│   ├── models/                # 数据模型
│   └── utils/                 # 工具函数
├── frontend/                  # 前端React应用
│   ├── src/
│   │   ├── components/        # React组件
│   │   ├── services/          # API服务
│   │   └── App.tsx           # 主应用组件
│   └── package.json          # 前端依赖
├── src/                       # 核心Agent系统
│   ├── agents/               # Agent实现
│   ├── backtesting/          # 回测系统
│   ├── tools/                # 工具模块
│   ├── utils/                # 通用工具
│   └── main.py               # 命令行入口
├── tests/                    # 测试文件
├── logs/                     # 日志目录
├── data/                     # 数据存储
├── poetry.lock               # 依赖锁定
├── pyproject.toml            # 项目配置
└── README.md                 # 项目文档
```

## 风险提示

⚠️ **重要声明**: 本系统仅用于教育和研究目的，不构成投资建议。投资有风险，入市需谨慎。

- 系统分析结果仅供参考，不保证准确性
- 历史回测结果不代表未来收益
- 请结合自身风险承受能力做出投资决策
- 建议在充分了解市场风险后使用

---

⭐ 如果这个项目对你有帮助，请给我们一个Star！