# Database Module

## 概述

数据库模块为 AShare Agent 投资分析系统提供统一的数据存储和检索服务。该模块基于 SQLite 数据库，设计了完整的金融数据存储架构，支持股票价格数据、新闻信息、技术指标、财务指标、宏观分析、情感分析等多种数据类型的高效存储和管理。

### 核心特性

- **统一数据访问接口**: 通过 `DataService` 类提供一致的数据操作 API
- **多数据源支持**: 支持来自 akshare、在线搜索等多种数据源
- **智能缓存管理**: 内置缓存机制，避免重复数据获取，提升系统性能
- **扩展性设计**: 模块化架构，易于添加新的数据类型和功能
- **事务安全**: 使用上下文管理器确保数据库操作的安全性
- **高性能查询**: 通过索引优化，支持高效的数据检索

## 架构设计

### 数据库架构

数据库采用分层设计，包含以下核心组件：

```
src/database/
├── __init__.py          # 模块初始化
├── models.py            # 数据模型定义
├── data_service.py      # 数据服务层
├── schema.sql           # 数据库架构定义
└── README.md           # 本文档
```

### 核心类结构

1. **DatabaseManager**: 数据库连接和基础操作管理
2. **数据模型类**: 针对不同数据类型的专门操作类
3. **DataService**: 统一的数据访问服务接口

## 数据模型与架构

### 1. 股票新闻数据 (`stock_news`)

存储股票相关新闻信息，支持多种新闻来源和检索方法。

**关键字段:**
- `ticker`: 股票代码
- `date`: 新闻日期
- `method`: 获取方法 (online_search等)
- `title`: 新闻标题
- `content`: 新闻内容
- `publish_time`: 发布时间
- `source`: 新闻来源
- `url`: 新闻链接

**用途:** 为宏观分析师和情感分析提供新闻数据支持

### 2. 股票价格数据 (`stock_price_data`)

存储股票的历史价格数据，支持多个时间周期。

**关键字段:**
- `ticker`: 股票代码
- `date`: 交易日期
- `period`: 数据周期 (daily/weekly/monthly)
- `open_price`, `high_price`, `low_price`, `close_price`: OHLC 价格数据
- `volume`: 成交量
- `turnover`: 成交额
- `data_source`: 数据源 (默认 akshare)

**用途:** 为技术分析和回测系统提供价格数据

### 3. 技术指标数据 (`technical_indicators`)

存储各种技术指标的计算结果。

**关键字段:**
- `ticker`: 股票代码
- `date`: 计算日期
- `indicator_name`: 指标名称 (MA5/MA10/MACD/RSI/BB等)
- `indicator_value`: 指标值
- `indicator_params`: 指标参数 (JSON格式)
- `period`: 计算周期

**用途:** 为技术分析师提供预计算的技术指标数据

### 4. 财务指标数据 (`financial_metrics`)

存储公司财务报表数据和关键财务指标。

**关键字段:**
- `ticker`: 股票代码
- `report_date`: 报告期
- `report_type`: 报告类型 (quarterly/annual)
- `metric_name`: 指标名称
- `metric_value`: 指标值
- `unit`: 单位

**用途:** 为基本面分析提供财务数据支持

### 5. 宏观分析缓存 (`macro_analysis_cache`)

缓存宏观经济分析结果，避免重复分析。

**关键字段:**
- `analysis_key`: 分析标识
- `analysis_type`: 分析类型 (news/summary/policy)
- `date`: 分析日期
- `macro_environment`: 宏观环境评估
- `impact_on_stock`: 对股票影响
- `key_factors`: 关键因素 (JSON数组)
- `reasoning`: 推理过程

**用途:** 为宏观分析师提供缓存机制，提升分析效率

### 6. 情感分析缓存 (`sentiment_cache`)

缓存新闻和内容的情感分析结果。

**关键字段:**
- `content_key`: 内容标识 (MD5哈希)
- `ticker`: 股票代码
- `sentiment_score`: 情感分数 (-1到1)
- `sentiment_label`: 情感标签 (positive/negative/neutral)
- `confidence_score`: 置信度分数

**用途:** 为情感分析师提供缓存支持

### 7. Agent 管理 (`agents`)

管理系统中的各种 Agent 实例。

**关键字段:**
- `name`: Agent名称
- `display_name`: 显示名称
- `agent_type`: Agent类型 (analysis/trading/risk)
- `status`: 状态 (active/inactive)
- `config`: 配置信息 (JSON格式)

### 8. Agent 决策记录 (`agent_decisions`)

记录各 Agent 的决策过程和结果。

**关键字段:**
- `run_id`: 运行ID
- `agent_name`: Agent名称
- `ticker`: 股票代码
- `decision_type`: 决策类型 (buy/sell/hold/analysis)
- `decision_data`: 决策数据 (JSON格式)
- `confidence_score`: 置信度
- `reasoning`: 推理过程

## 数据服务功能

### DataService 类

`DataService` 是数据库模块的核心接口，提供统一的数据访问服务。

#### 主要功能分类:

1. **股票新闻服务**
   - `save_stock_news()`: 保存股票新闻数据
   - `get_stock_news()`: 获取指定日期的股票新闻
   - `get_stock_news_range()`: 获取日期范围内的股票新闻
   - `get_stock_news_smart()`: 智能获取新闻，支持范围扩展

2. **股票价格数据服务**
   - `save_stock_price()`: 保存股票价格数据
   - `get_stock_price()`: 获取价格数据

3. **技术指标服务**
   - `save_technical_indicator()`: 保存技术指标
   - `get_technical_indicators()`: 获取技术指标数据

4. **财务指标服务**
   - `save_financial_metric()`: 保存财务指标
   - `get_financial_metrics()`: 获取财务指标数据

5. **宏观分析服务**
   - `save_macro_analysis()`: 保存宏观分析结果
   - `get_macro_analysis()`: 获取宏观分析结果
   - `get_macro_analysis_by_date()`: 按日期获取宏观分析

6. **情感分析服务**
   - `save_sentiment_analysis()`: 保存情感分析结果
   - `get_sentiment_analysis()`: 获取情感分析结果
   - `get_sentiment_by_ticker_date()`: 按股票和日期获取情感分析

7. **缓存管理服务**
   - `is_data_cached()`: 检查数据是否已缓存
   - `set_cache_config()`: 设置缓存配置

## 使用示例

### 1. 基本初始化

```python
from src.database.data_service import get_data_service

# 获取全局数据服务实例
data_service = get_data_service()

# 或者指定数据库路径
from src.database.data_service import DataService
data_service = DataService("custom/path/to/database.db")
```

### 2. 股票新闻操作

```python
# 保存股票新闻
news_data = [
    {
        'title': '某公司发布季报',
        'content': '公司业绩超预期...',
        'publish_time': '2024-01-15 10:30:00',
        'source': 'sina.com.cn',
        'url': 'https://example.com/news/1'
    }
]

count = data_service.save_stock_news(
    ticker='000001',
    date='2024-01-15',
    method='online_search',
    query='000001 股票 新闻',
    news_data=news_data
)
print(f"保存了 {count} 条新闻")

# 获取股票新闻
news_list = data_service.get_stock_news('000001', '2024-01-15')
for news in news_list:
    print(f"标题: {news['title']}")
    print(f"来源: {news['source']}")
```

### 3. 股票价格数据操作

```python
# 保存股票价格数据
price_data = {
    'open': 10.50,
    'high': 11.20,
    'low': 10.30,
    'close': 11.00,
    'volume': 1000000,
    'turnover': 10800000
}

success = data_service.save_stock_price(
    ticker='000001',
    date='2024-01-15',
    price_data=price_data
)

# 获取价格数据
prices = data_service.get_stock_price(
    ticker='000001',
    start_date='2024-01-01',
    end_date='2024-01-31'
)

for price in prices:
    print(f"日期: {price['date']}, 收盘价: {price['close_price']}")
```

### 4. 宏观分析缓存

```python
# 保存宏观分析结果
analysis_key = "重要政策发布|2024-01-15 14:00:00"
success = data_service.save_macro_analysis(
    analysis_key=analysis_key,
    date='2024-01-15',
    analysis_type='news',
    macro_environment='positive',
    impact_on_stock='positive',
    key_factors=['政策利好', '市场预期上升'],
    reasoning='政策发布对市场产生积极影响...'
)

# 获取宏观分析结果
analysis = data_service.get_macro_analysis(analysis_key, 'news')
if analysis:
    print(f"宏观环境: {analysis['macro_environment']}")
    print(f"股票影响: {analysis['impact_on_stock']}")
```

### 5. 情感分析缓存

```python
# 保存情感分析结果
content = "公司业绩超预期，市场反应积极"
success = data_service.save_sentiment_analysis(
    content=content,
    sentiment_score=0.8,
    sentiment_label='positive',
    ticker='000001',
    date='2024-01-15',
    confidence_score=0.95
)

# 获取情感分析结果
sentiment = data_service.get_sentiment_analysis(content, '000001')
if sentiment:
    print(f"情感分数: {sentiment['sentiment_score']}")
    print(f"情感标签: {sentiment['sentiment_label']}")
```

### 6. 智能数据检查

```python
# 检查是否有足够的新闻数据
has_enough_news = data_service.has_sufficient_data_for_date(
    ticker='000001',
    date='2024-01-15',
    min_news=5
)

if has_enough_news:
    print("已有足够的新闻数据，无需重复获取")
else:
    print("需要获取更多新闻数据")

# 智能获取新闻（优先使用缓存，不足时扩展范围）
news_list = data_service.get_stock_news_smart(
    ticker='000001',
    date='2024-01-15',
    max_news=10
)
print(f"获取到 {len(news_list)} 条新闻")
```

## 配置和设置

### 1. 数据库初始化

数据库会在首次使用时自动初始化，创建所有必要的表和索引。

```python
from src.database.models import DatabaseManager

# 手动初始化数据库
db_manager = DatabaseManager("data/ashare_agent.db")
db_manager.init_database()  # 执行 schema.sql 中的建表语句
```

### 2. 自定义数据库路径

```python
from src.database.data_service import initialize_data_service

# 初始化自定义路径的数据服务
data_service = initialize_data_service("custom/path/database.db")
```

### 3. 缓存配置

```python
# 设置缓存过期时间
data_service.set_cache_config(
    cache_type='macro_analysis',
    cache_key='news_analysis_key',
    expiry_hours=48,  # 48小时过期
    metadata={'source': 'online_search', 'version': '1.0'}
)

# 检查缓存是否有效
is_valid = data_service.is_data_cached('macro_analysis', 'news_analysis_key')
```

## API 参考

### DatabaseManager

#### 构造函数
```python
DatabaseManager(db_path: str = "data/ashare_agent.db")
```

#### 主要方法
- `init_database()`: 初始化数据库架构
- `get_connection()`: 获取数据库连接上下文管理器
- `execute_query(query: str, params: tuple = ())`: 执行查询
- `execute_update(query: str, params: tuple = ())`: 执行更新操作

### DataService

#### 构造函数
```python
DataService(db_path: str = "data/ashare_agent.db")
```

#### 股票新闻方法
- `save_stock_news(ticker, date, method, query, news_data) -> int`
- `get_stock_news(ticker, date) -> List[Dict]`
- `get_stock_news_range(ticker, start_date, end_date) -> List[Dict]`
- `get_stock_news_smart(ticker, date, max_news=10) -> List[Dict]`

#### 股票价格方法
- `save_stock_price(ticker, date, price_data, period='daily', data_source='akshare') -> bool`
- `get_stock_price(ticker, start_date, end_date, period='daily') -> List[Dict]`

#### 技术指标方法
- `save_technical_indicator(ticker, date, indicator_name, indicator_value, indicator_params=None, period='daily') -> bool`
- `get_technical_indicators(ticker, indicator_names, start_date, end_date, period='daily') -> List[Dict]`

#### 财务指标方法
- `save_financial_metric(ticker, report_date, metric_name, metric_value, unit=None, report_type='quarterly', data_source='akshare') -> bool`
- `get_financial_metrics(ticker, metric_names, report_type='quarterly', limit=10) -> List[Dict]`

#### 宏观分析方法
- `save_macro_analysis(analysis_key, date, analysis_type='news', **kwargs) -> bool`
- `get_macro_analysis(analysis_key, analysis_type='news') -> Optional[Dict]`
- `get_macro_analysis_by_date(date, analysis_type='summary') -> List[Dict]`

#### 情感分析方法
- `save_sentiment_analysis(content, sentiment_score, sentiment_label, **kwargs) -> bool`
- `get_sentiment_analysis(content, ticker=None) -> Optional[Dict]`
- `get_sentiment_by_ticker_date(ticker, date) -> List[Dict]`

#### 缓存管理方法
- `is_data_cached(cache_type, cache_key) -> bool`
- `set_cache_config(cache_type, cache_key, expiry_hours=24, metadata=None) -> bool`

#### 数据检查方法
- `has_stock_news(ticker, date, min_count=1) -> bool`
- `has_macro_analysis(news_key) -> bool`
- `has_sentiment_analysis(content) -> bool`
- `has_sufficient_data_for_date(ticker, date, min_news=5) -> bool`

## 与其他模块的集成

### 1. 与 Agent 模块集成

数据库模块为各种 Agent 提供数据支持：

```python
# 在 macro_analyst.py 中使用
from src.database.data_service import get_data_service

def macro_analyst_agent(state):
    data_service = get_data_service()
    
    # 获取新闻数据
    news_list = data_service.get_stock_news_smart(
        ticker=state["data"]["ticker"],
        date=state["data"]["end_date"],
        max_news=100
    )
    
    # 检查是否有宏观分析缓存
    analysis_key = f"macro_analysis_{ticker}_{date}"
    cached_analysis = data_service.get_macro_analysis(analysis_key)
    
    if not cached_analysis:
        # 进行新的分析并保存
        analysis_result = perform_macro_analysis(news_list)
        data_service.save_macro_analysis(analysis_key, date, **analysis_result)
```

### 2. 与新闻爬虫集成

```python
# 在 news_crawler.py 中使用
from src.database.data_service import get_data_service

def get_stock_news(symbol, max_news=50, date=None):
    data_service = get_data_service()
    
    # 检查本地缓存
    if data_service.has_sufficient_data_for_date(symbol, date, max_news):
        return data_service.get_stock_news_smart(symbol, date, max_news)
    
    # 获取新的新闻数据
    new_news = fetch_news_from_online(symbol, date)
    data_service.save_stock_news(
        ticker=symbol,
        date=date,
        method='online_search',
        query=build_search_query(symbol, date),
        news_data=new_news
    )
    
    return data_service.get_stock_news_smart(symbol, date, max_news)
```

### 3. 与回测系统集成

```python
# 在 backtesting 模块中使用
from src.database.data_service import get_data_service

class BacktestEngine:
    def __init__(self):
        self.data_service = get_data_service()
    
    def get_historical_prices(self, ticker, start_date, end_date):
        return self.data_service.get_stock_price(ticker, start_date, end_date)
    
    def get_technical_indicators(self, ticker, indicators, start_date, end_date):
        return self.data_service.get_technical_indicators(
            ticker, indicators, start_date, end_date
        )
```

## 性能优化

### 1. 索引优化

数据库包含针对常用查询的索引：

```sql
-- 股票新闻查询优化
CREATE INDEX idx_stock_news_ticker_date ON stock_news(ticker, date);

-- 价格数据查询优化  
CREATE INDEX idx_stock_price_ticker_date ON stock_price_data(ticker, date);

-- 技术指标查询优化
CREATE INDEX idx_technical_indicators_ticker_date ON technical_indicators(ticker, date);
```

### 2. 批量操作

对于大量数据的插入，建议使用批量操作：

```python
# 批量保存新闻数据
news_batch = []  # 大量新闻数据
data_service.save_stock_news(ticker, date, method, query, news_batch)
```

### 3. 连接池管理

使用上下文管理器确保数据库连接的正确释放：

```python
with data_service.db_manager.get_connection() as conn:
    # 执行数据库操作
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stock_news WHERE ticker = ?", (ticker,))
    results = cursor.fetchall()
```

## 错误处理

### 1. 数据库连接错误

```python
try:
    data_service = DataService("invalid/path/database.db")
except Exception as e:
    logger.error(f"数据库初始化失败: {e}")
    # 使用默认路径重试
    data_service = DataService()
```

### 2. 数据完整性错误

```python
try:
    success = data_service.save_stock_news(ticker, date, method, query, news_data)
    if not success:
        logger.warning("部分新闻数据保存失败，可能存在重复数据")
except Exception as e:
    logger.error(f"保存新闻数据时发生错误: {e}")
```

### 3. 缓存失效处理

```python
# 检查缓存并处理失效情况
cached_analysis = data_service.get_macro_analysis(analysis_key)
if not cached_analysis or not data_service.is_data_cached('macro_analysis', analysis_key):
    # 缓存失效，重新分析
    new_analysis = perform_analysis()
    data_service.save_macro_analysis(analysis_key, date, **new_analysis)
```

## 最佳实践

### 1. 数据一致性

- 使用事务确保数据的一致性
- 定期检查和清理过期数据
- 使用唯一约束防止重复数据

### 2. 性能优化

- 合理使用缓存机制，避免重复计算
- 对于频繁查询的数据，考虑创建专门的索引
- 定期分析查询性能，优化慢查询

### 3. 数据备份

```python
# 定期备份数据库
import shutil
from datetime import datetime

def backup_database():
    backup_path = f"backups/database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2("data/ashare_agent.db", backup_path)
    print(f"数据库已备份到: {backup_path}")
```

### 4. 监控和日志

```python
import logging

# 设置数据库操作日志
logger = logging.getLogger('database')

# 在关键操作中添加日志
def save_with_logging(operation_name, func, *args, **kwargs):
    try:
        result = func(*args, **kwargs)
        logger.info(f"{operation_name} 成功: {result}")
        return result
    except Exception as e:
        logger.error(f"{operation_name} 失败: {e}")
        raise
```

## 常见问题解答

### Q: 如何处理数据库文件损坏？

A: 数据库模块会自动检测和修复轻微的数据库问题。对于严重损坏，建议：
1. 从备份中恢复数据库文件
2. 重新初始化数据库并重新导入数据
3. 检查磁盘空间和文件权限

### Q: 如何迁移到新的数据库架构？

A: 数据库架构更新时：
1. 备份现有数据库
2. 运行数据迁移脚本
3. 验证数据完整性
4. 更新应用程序代码

### Q: 如何优化查询性能？

A: 查询性能优化建议：
1. 使用适当的索引
2. 限制查询结果集大小
3. 使用 EXPLAIN 分析查询计划
4. 定期更新数据库统计信息

### Q: 如何处理并发访问？

A: SQLite 支持多读一写的并发模式，对于高并发场景建议：
1. 使用连接池管理
2. 实现适当的重试机制
3. 考虑使用 WAL 模式提升并发性能

通过这个数据库模块，AShare Agent 系统能够高效地管理和检索各种金融数据，为智能投资分析提供可靠的数据基础。