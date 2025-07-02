# 智能回测系统 - 模块化架构

## 概述

智能回测系统已重构为模块化架构，支持细粒度频率控制。系统被拆分为多个独立模块，提高了代码可维护性和扩展性。

## 模块结构

```
src/backtesting/
├── __init__.py          # 模块初始化和导出
├── models.py            # 数据模型和类型定义
├── cache.py             # 智能缓存管理器
├── trading.py           # 交易执行器
├── metrics.py           # 性能和风险指标计算器
├── visualizer.py        # 性能可视化器
├── backtester.py        # 主回测器类
└── README.md           # 说明文档
```

## 核心特性

### 1. 细粒度频率控制
- **daily**: 每日执行
- **weekly**: 每周一执行  
- **monthly**: 每月第一个交易日执行
- **conditional**: 基于市场条件触发

### 2. 智能缓存系统
- 数据缓存：减少重复的API调用
- 结果缓存：避免重复计算
- 缓存命中率统计

### 3. 模块化设计
- **CacheManager**: 管理数据和结果缓存
- **TradeExecutor**: 处理交易执行和手续费
- **MetricsCalculator**: 计算性能和风险指标
- **PerformanceVisualizer**: 生成图表和可视化

## 使用方法

### 基本用法

```python
from src.backtesting import IntelligentBacktester
from src.main import run_hedge_fund

# 配置agent执行频率
agent_frequencies = {
    'market_data': 'daily',
    'technical': 'daily', 
    'fundamentals': 'weekly',
    'sentiment': 'daily',
    'valuation': 'monthly',
    'macro': 'weekly',
    'portfolio': 'daily'
}

# 创建回测器
backtester = IntelligentBacktester(
    agent=run_hedge_fund,
    ticker="600519",
    start_date="2024-01-01",
    end_date="2024-12-31",
    initial_capital=100000,
    num_of_news=5,
    agent_frequencies=agent_frequencies
)

# 运行回测
backtester.run_backtest()

# 分析性能
performance_df = backtester.analyze_performance(save_plots=True)
```

### 命令行用法

```bash
# 使用新的模块化系统
poetry run python src/backtesting/backtester.py --ticker 600519 --start-date 2024-01-01 --end-date 2024-12-31

# 配置不同的agent频率
poetry run python src/backtesting/backtester.py \
    --ticker 600519 \
    --technical-freq daily \
    --fundamentals-freq weekly \
    --valuation-freq monthly

# 向后兼容（仍然可用）
poetry run python src/intelligent_backtester.py --ticker 600519
```

## 优化效果

### 性能提升
- **Agent优化率**: 通过频率控制减少不必要的执行
- **缓存命中率**: 减少重复计算和API调用
- **执行统计**: 详细的agent执行次数统计

### 示例输出
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

缓存性能:
  缓存命中: 45
  缓存未命中: 30
  缓存命中率: 60.0%
  总体优化率: 45.2%
```

## API 参考

### IntelligentBacktester

主要的回测器类，整合所有组件。

#### 参数
- `agent`: 智能体函数
- `ticker`: 股票代码
- `start_date`: 开始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)
- `initial_capital`: 初始资金
- `num_of_news`: 新闻分析数量
- `commission_rate`: 手续费率 (默认: 0.0003)
- `slippage_rate`: 滑点率 (默认: 0.001)
- `benchmark_ticker`: 基准指数 (默认: '000001')
- `agent_frequencies`: Agent频率配置字典

#### 方法
- `run_backtest()`: 运行回测
- `analyze_performance(save_plots=True)`: 分析性能并生成图表

### CacheManager

管理数据和结果缓存。

#### 方法
- `get_cached_price_data(ticker, start_date, end_date)`: 获取缓存的价格数据
- `get_agent_result(cache_key)`: 获取缓存的agent结果
- `cache_agent_result(cache_key, result)`: 缓存agent结果

### TradeExecutor

处理交易执行。

#### 方法
- `execute_trade(action, quantity, current_price, date, portfolio)`: 执行交易
- `calculate_trade_pnl(trade)`: 计算交易盈亏

### MetricsCalculator

计算性能和风险指标。

#### 静态方法
- `calculate_performance_metrics(...)`: 计算性能指标
- `calculate_risk_metrics(...)`: 计算风险指标

### PerformanceVisualizer

生成性能图表。

#### 方法
- `create_performance_plot(...)`: 创建综合性能图表

## 向后兼容性

重构后的系统完全向后兼容：

```python
# 旧的导入方式仍然有效
from src.intelligent_backtester import IntelligentBacktester

# 命令行用法也保持兼容
python src/intelligent_backtester.py --ticker 600519
```

## 配置示例

### 保守策略配置
```python
conservative_frequencies = {
    'market_data': 'daily',
    'technical': 'weekly', 
    'fundamentals': 'monthly',
    'sentiment': 'weekly',
    'valuation': 'monthly',
    'macro': 'monthly',
    'portfolio': 'daily'
}
```

### 激进策略配置
```python
aggressive_frequencies = {
    'market_data': 'daily',
    'technical': 'daily', 
    'fundamentals': 'daily',
    'sentiment': 'daily',
    'valuation': 'weekly',
    'macro': 'daily',
    'portfolio': 'daily'
}
```

### 条件触发配置
```python
conditional_frequencies = {
    'market_data': 'daily',
    'technical': 'conditional',  # 高波动时触发
    'fundamentals': 'monthly',
    'sentiment': 'conditional',   # 价格大幅变动时触发
    'valuation': 'monthly',
    'macro': 'weekly',
    'portfolio': 'daily'
}
```

## 性能监控

系统提供详细的执行统计：

1. **Agent执行频率**: 每个agent的实际执行次数和比例
2. **缓存性能**: 缓存命中率和节省的请求数
3. **优化效果**: 总体执行优化率
4. **回测指标**: 传统的收益率、夏普比率等指标

## 故障排除

### 常见问题

1. **导入错误**
   ```bash
   # 确保使用poetry环境
   poetry run python your_script.py
   ```

2. **数据获取失败**
   - 检查网络连接
   - 验证股票代码格式
   - 确认日期范围有效

3. **性能问题**
   - 调整agent频率配置
   - 使用较短的回测期间进行测试
   - 检查缓存命中率

### 调试建议

1. 启用详细日志：
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   ```

2. 使用模拟agent进行测试：
   ```python
   def mock_agent(**kwargs):
       return {"action": "hold", "quantity": 0}
   ```

3. 检查模块导入：
   ```python
   from src.backtesting import *
   print("所有模块导入成功")
   ```

## 贡献指南

### 添加新功能

1. 在相应模块中添加新方法
2. 更新`__init__.py`中的导出
3. 添加单元测试
4. 更新文档

### 性能优化

1. 优化缓存策略
2. 改进agent频率控制逻辑
3. 增强错误处理
4. 添加更多指标计算

### 测试

```bash
# 运行单元测试
poetry run python -m pytest tests/

# 运行集成测试
poetry run python test_integration.py
```