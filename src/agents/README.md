# 智能投资代理系统 - 多Agent协同架构

## 概述

智能投资代理系统采用多Agent协同架构，通过专业化分工和集体决策来模拟真实的投资团队。系统包含12个专业化代理，涵盖市场数据收集、基本面分析、技术分析、估值分析、情感分析、风险管理、宏观分析等各个方面，最终通过投资组合管理代理做出综合投资决策。

## 系统架构

```
src/agents/
├── __init__.py              # 模块初始化
├── base_agent.py            # 基础代理类和通用功能
├── state.py                 # 代理状态管理和消息传递
├── market_data.py           # 市场数据收集代理
├── fundamentals.py          # 基本面分析代理
├── technicals.py            # 技术分析代理
├── sentiment.py             # 情感分析代理
├── valuation.py             # 估值分析代理
├── macro_analyst.py         # 宏观分析代理
├── macro_news_agent.py      # 宏观新闻分析代理
├── researcher_bull.py       # 多方研究员代理
├── researcher_bear.py       # 空方研究员代理
├── debate_room.py           # 辩论室代理
├── risk_manager.py          # 风险管理代理
├── portfolio_manager.py     # 投资组合管理代理
├── sentiment_refactored.py  # 重构后的情感分析代理
└── README.md               # 说明文档
```

## 代理角色说明

### 1. 核心分析代理

#### 市场数据代理 (Market Data Agent)
- **功能**: 负责收集和预处理市场数据
- **数据源**: 股价历史、财务指标、财务报表、市场信息
- **特点**: 
  - 智能数据验证和清洗
  - 增强型财务指标计算
  - 自动处理数据缺失和异常

#### 基本面分析代理 (Fundamentals Agent)
- **功能**: 分析公司财务指标、盈利能力和增长潜力
- **分析维度**:
  - 盈利能力分析 (ROE, 净利润率, 营业利润率)
  - 增长分析 (营收增长, 利润增长, 净资产增长)
  - 财务健康分析 (流动比率, 资产负债率, 自由现金流)
  - 估值比率分析 (P/E, P/B, P/S)

#### 技术分析代理 (Technical Analyst Agent)
- **功能**: 基于价格走势和技术指标提供交易信号
- **策略组合**:
  - 趋势跟踪策略 (EMA, ADX, Ichimoku)
  - 均值回归策略 (Bollinger Bands, RSI, Z-Score)
  - 动量策略 (多时间框架动量分析)
  - 波动率策略 (历史波动率分析)
  - 统计套利信号 (Hurst指数, 偏度分析)

#### 估值分析代理 (Valuation Agent)
- **功能**: 使用DCF和所有者收益法评估公司内在价值
- **估值方法**:
  - DCF估值 (现金流折现模型)
  - 所有者收益法 (巴菲特方法)
  - 动态增长率调整
  - 安全边际计算

#### 情感分析代理 (Sentiment Agent)
- **功能**: 分析市场新闻和社交媒体情绪
- **特点**:
  - 7天内新闻过滤
  - 智能情感评分
  - 多源信息整合

### 2. 宏观分析代理

#### 宏观分析代理 (Macro Analyst Agent)
- **功能**: 分析宏观经济环境对目标股票的影响
- **分析要素**:
  - 货币政策影响
  - 财政政策变化
  - 产业政策导向
  - 国际环境因素
  - 市场情绪变化

#### 宏观新闻代理 (Macro News Agent)
- **功能**: 获取沪深300全量新闻并进行宏观分析
- **特点**:
  - 按月缓存分析结果
  - 市场情绪解读
  - 热点板块识别
  - 潜在风险提示
  - 政策影响分析

### 3. 研究决策代理

#### 多方研究员 (Researcher Bull Agent)
- **功能**: 从看多角度分析市场数据并提出投资论点
- **A股特色分析**:
  - 政策敏感性分析
  - T+1交易制度考虑
  - 涨跌停板影响评估
  - 流动性风险评估

#### 空方研究员 (Researcher Bear Agent)
- **功能**: 从看空角度分析市场数据并提出风险警示
- **风险识别**:
  - 跌停板风险
  - 政策不确定性
  - 估值泡沫风险
  - 情绪过热风险

#### 辩论室代理 (Debate Room Agent)
- **功能**: 分析多空双方观点，得出平衡的投资结论
- **A股特色决策**:
  - 政策敏感性调整
  - 流动性风险考量
  - 情绪极端情况处理
  - LLM第三方观点整合

### 4. 风险管理代理

#### 风险管理代理 (Risk Manager Agent)
- **功能**: 评估投资风险并给出风险调整后的交易建议
- **风险评估**:
  - 历史波动率分析
  - VaR计算 (95%置信度)
  - 最大回撤分析
  - 压力测试
  - 仓位规模建议

### 5. 投资组合管理代理

#### 投资组合管理代理 (Portfolio Manager Agent)
- **功能**: 负责投资组合管理和最终交易决策
- **A股权重配置策略**:
  - 基本面分析 (35% 权重)
  - 估值分析 (25% 权重)
  - 技术分析 (20% 权重)
  - 宏观分析 (15% 权重)
  - 情绪分析 (5% 权重)

## 使用方法

### 基本用法

```python
from src.main import run_hedge_fund

# 运行完整的投资决策流程
decision = run_hedge_fund(
    ticker="600519",  # 股票代码
    num_of_news=20,   # 新闻分析数量
    end_date="2024-01-31",  # 分析截止日期
    show_reasoning=True  # 显示推理过程
)

print(f"投资决策: {decision['action']}")
print(f"建议数量: {decision['quantity']}")
print(f"置信度: {decision['confidence']}")
```

### 单独使用特定代理

```python
from src.agents.fundamentals import fundamentals_agent
from src.agents.state import AgentState

# 构造代理状态
state = AgentState({
    "messages": [],
    "data": {
        "ticker": "600519",
        "financial_metrics": [...],  # 财务指标数据
        "prices": [...]  # 价格数据
    },
    "metadata": {"show_reasoning": True}
})

# 运行基本面分析
result = fundamentals_agent(state)
print(result["data"]["fundamental_analysis"])
```

### 自定义代理开发

```python
from src.agents.base_agent import BaseAgent, AnalysisResult
from src.agents.state import AgentState

class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__("custom", "自定义分析代理")
    
    def analyze(self, state: AgentState):
        # 自定义分析逻辑
        data = state["data"]
        
        # 执行分析
        signal = "bullish"  # 或 "bearish", "neutral"
        confidence = 0.8
        reasoning = "基于自定义逻辑的分析结果"
        
        # 返回标准格式结果
        result = AnalysisResult(signal, confidence, reasoning)
        return {
            "messages": state["messages"] + [self.create_message(result.to_json())],
            "data": state["data"],
            "metadata": state["metadata"]
        }
```

## API 参考

### BaseAgent 基类

所有代理的基础类，提供通用功能。

#### 方法

- `analyze(state: AgentState) -> Dict[str, Any]`: 子类必须实现的分析方法
- `safe_llm_call(messages, fallback_response=None)`: 安全的LLM调用
- `safe_json_parse(content, fallback=None)`: 安全的JSON解析
- `validate_data(data, required_fields)`: 数据验证
- `create_message(content, name=None)`: 创建标准化消息
- `log_reasoning(reasoning_data, state)`: 记录推理过程

### AgentState 状态管理

代理间消息传递和状态管理。

#### 字段

- `messages`: 代理间消息序列
- `data`: 共享数据字典
- `metadata`: 元数据和配置信息

#### 工具函数

- `show_workflow_status(agent_name, status="processing")`: 显示工作流状态
- `show_agent_reasoning(output, agent_name)`: 显示代理推理过程

### AnalysisResult 结果类

标准化的分析结果格式。

#### 字段

- `signal`: 投资信号 ("bullish", "bearish", "neutral")
- `confidence`: 置信度 (0.0 - 1.0)
- `reasoning`: 推理说明
- `additional_data`: 额外数据字典

#### 方法

- `to_dict()`: 转换为字典格式
- `to_json()`: 转换为JSON字符串

## 配置选项

### 代理频率控制

在回测中可以配置不同代理的执行频率：

```python
agent_frequencies = {
    'market_data': 'daily',      # 每日执行
    'technical': 'daily',        # 每日执行
    'fundamentals': 'weekly',    # 每周执行
    'sentiment': 'daily',        # 每日执行
    'valuation': 'monthly',      # 每月执行
    'macro': 'weekly',          # 每周执行
    'portfolio': 'daily'        # 每日执行
}
```

### LLM 配置

```python
# 在 src/tools/openrouter_config.py 中配置
LLM_CONFIG = {
    "model": "anthropic/claude-3-haiku",
    "temperature": 0.1,
    "max_tokens": 4000
}
```

### 日志配置

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.INFO)

# 显示推理过程
state["metadata"]["show_reasoning"] = True
```

## 与回测系统集成

### 回测中的代理协同

```python
from src.backtesting import IntelligentBacktester

# 创建回测器并配置代理频率
backtester = IntelligentBacktester(
    agent=run_hedge_fund,
    ticker="600519",
    start_date="2024-01-01",
    end_date="2024-12-31",
    initial_capital=100000,
    agent_frequencies={
        'market_data': 'daily',
        'fundamentals': 'weekly',
        'technical': 'daily',
        'sentiment': 'daily',
        'valuation': 'monthly',
        'macro': 'weekly',
        'portfolio': 'daily'
    }
)

# 运行回测
backtester.run_backtest()
```

### 代理执行统计

回测系统会提供详细的代理执行统计：

```
智能优化统计
======================================================================
market_data    :  30/30 次执行 (100.0%)
technical      :  30/30 次执行 (100.0%)
fundamentals   :   4/30 次执行 ( 13.3%)
sentiment      :  30/30 次执行 (100.0%)
valuation      :   1/30 次执行 (  3.3%)
macro          :   4/30 次执行 ( 13.3%)
portfolio      :  30/30 次执行 (100.0%)
```

## A股市场特色适配

### 交易制度适配

- **T+1交易制度**: 技术分析考虑隔日交易限制
- **涨跌停板**: 技术分析包含涨跌停风险评估
- **价格发现机制**: 适应A股特有的价格波动模式

### 政策敏感性分析

- **政策导向投资**: 基本面和宏观分析重点关注政策影响
- **行业轮动**: 技术分析适应A股行业轮动特征
- **监管环境**: 风险管理考虑监管政策变化

### 市场情绪特征

- **散户占比**: 情感分析权重相对降低
- **资金流向**: 技术分析增加资金流向指标
- **机构行为**: 研究员分析考虑机构投资者行为

## 性能优化

### 缓存机制

```python
# 宏观新闻按月缓存
# 文件位置: src/data/macro_summary.json
{
    "2024-01": {
        "summary_content": "宏观分析内容...",
        "retrieved_news_count": 150,
        "last_updated": "2024-01-15T10:30:00"
    }
}
```

### 错误处理和恢复

```python
from src.utils.exceptions import MarketDataError, ErrorRecoveryStrategy

try:
    # 代理分析逻辑
    result = agent.analyze(state)
except MarketDataError as e:
    # 自动错误恢复
    fallback_result = ErrorRecoveryStrategy.get_default_analysis_result(
        agent_name, str(e)
    )
```

### 并发执行优化

系统支持部分代理的并发执行以提高性能：

```python
# 独立数据源的代理可以并发执行
concurrent_agents = [
    "market_data_agent",
    "macro_news_agent"
]
```

## 扩展开发

### 添加新代理

1. 继承 `BaseAgent` 类
2. 实现 `analyze` 方法
3. 使用 `@agent_endpoint` 装饰器
4. 在工作流中集成

```python
from src.agents.base_agent import BaseAgent
from src.utils.api_utils import agent_endpoint

@agent_endpoint("new_agent", "新代理描述")
def new_agent(state: AgentState):
    # 实现新代理逻辑
    return {
        "messages": [...],
        "data": {...},
        "metadata": {...}
    }
```

### 修改决策权重

在 `portfolio_manager.py` 中调整A股权重配置：

```python
# A股市场权重配置策略
weights = {
    'fundamental': 0.35,  # 可调整权重
    'valuation': 0.25,
    'technical': 0.20,
    'macro': 0.15,
    'sentiment': 0.05
}
```

### 自定义分析指标

在相应代理中添加新的分析指标：

```python
# 在 technicals.py 中添加新指标
def calculate_new_indicator(prices_df):
    # 实现新的技术指标
    return indicator_values

# 在策略中使用
new_indicator = calculate_new_indicator(prices_df)
```

## 故障排除

### 常见问题

1. **代理执行失败**
   ```bash
   # 检查日志文件
   tail -f logs/fundamentals_agent.log
   ```

2. **数据获取错误**
   ```python
   # 验证数据源连接
   from src.tools.api import get_financial_metrics
   metrics = get_financial_metrics("600519")
   ```

3. **LLM调用超时**
   ```python
   # 调整超时设置
   LLM_CONFIG["timeout"] = 60  # 秒
   ```

### 调试建议

1. **启用详细日志**
   ```python
   state["metadata"]["show_reasoning"] = True
   ```

2. **单步调试代理**
   ```python
   # 逐个测试代理
   result = fundamentals_agent(test_state)
   print(json.dumps(result, indent=2))
   ```

3. **验证状态传递**
   ```python
   # 检查代理间状态传递
   print([msg.name for msg in state["messages"]])
   ```

### 性能监控

```python
# 监控代理执行时间
import time

start_time = time.time()
result = agent(state)
execution_time = time.time() - start_time
print(f"代理执行时间: {execution_time:.2f}秒")
```

### 测试方法

```bash
# 运行代理单元测试
poetry run python -m pytest tests/unit/test_agents.py

# 运行集成测试
poetry run python -m pytest tests/integration/test_agent_workflow.py

# 运行性能测试
poetry run python tests/performance/test_agent_performance.py
```