-- A股代理系统数据库架构
-- 创建时间: 2025-06-30
-- 支持扩展的多数据源、多时间序列的金融数据存储

-- 股票新闻表
CREATE TABLE IF NOT EXISTS stock_news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,                    -- 股票代码
    date TEXT NOT NULL,                      -- 新闻日期 YYYY-MM-DD
    method TEXT NOT NULL,                    -- 获取方法 (online_search等)
    query TEXT,                              -- 搜索查询
    title TEXT NOT NULL,                     -- 新闻标题
    content TEXT,                            -- 新闻内容
    publish_time TEXT,                       -- 发布时间
    source TEXT,                             -- 新闻来源
    url TEXT,                                -- 新闻链接
    keyword TEXT,                            -- 关键词
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date, title, url)         -- 防止重复数据
);

-- 股票价格数据表 (支持多个时间周期)
CREATE TABLE IF NOT EXISTS stock_price_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,                    -- 股票代码
    date TEXT NOT NULL,                      -- 交易日期 YYYY-MM-DD
    period TEXT NOT NULL DEFAULT 'daily',   -- 数据周期 (daily/weekly/monthly)
    open_price REAL,                         -- 开盘价
    high_price REAL,                         -- 最高价
    low_price REAL,                          -- 最低价
    close_price REAL,                        -- 收盘价
    volume INTEGER,                          -- 成交量
    turnover REAL,                           -- 成交额
    data_source TEXT DEFAULT 'akshare',     -- 数据源
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date, period)             -- 防止重复数据
);

-- 技术指标数据表 (扩展性设计)
CREATE TABLE IF NOT EXISTS technical_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,                    -- 股票代码
    date TEXT NOT NULL,                      -- 计算日期 YYYY-MM-DD
    indicator_name TEXT NOT NULL,            -- 指标名称 (MA5/MA10/MACD/RSI/BB等)
    indicator_value REAL,                    -- 指标值
    indicator_params TEXT,                   -- 指标参数 (JSON格式)
    period TEXT DEFAULT 'daily',            -- 计算周期
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date, indicator_name, period) -- 防止重复数据
);

-- 财务指标数据表
CREATE TABLE IF NOT EXISTS financial_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,                    -- 股票代码
    report_date TEXT NOT NULL,               -- 报告期 YYYY-MM-DD
    report_type TEXT DEFAULT 'quarterly',   -- 报告类型 (quarterly/annual)
    metric_name TEXT NOT NULL,               -- 指标名称
    metric_value REAL,                       -- 指标值
    unit TEXT,                               -- 单位
    data_source TEXT DEFAULT 'akshare',     -- 数据源
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, report_date, report_type, metric_name) -- 防止重复数据
);

-- 宏观分析缓存表 (增强版)
CREATE TABLE IF NOT EXISTS macro_analysis_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_key TEXT NOT NULL,             -- 分析标识 (新闻标题|发布时间)
    analysis_type TEXT DEFAULT 'news',     -- 分析类型 (news/summary/policy等)
    date TEXT NOT NULL,                      -- 分析日期 YYYY-MM-DD
    macro_environment TEXT,                  -- 宏观环境 (neutral/positive/negative)
    impact_on_stock TEXT,                    -- 对股票影响 (neutral/positive/negative)
    key_factors TEXT,                        -- 关键因素 (JSON数组)
    reasoning TEXT,                          -- 推理过程
    content TEXT,                            -- 完整分析内容
    retrieved_news_count INTEGER DEFAULT 0, -- 检索的新闻数量
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(analysis_key, analysis_type)     -- 防止重复分析
);

-- 情感分析缓存表 (增强版)
CREATE TABLE IF NOT EXISTS sentiment_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT,                             -- 股票代码 (可为空，用于全市场情感)
    content_key TEXT NOT NULL,               -- 内容标识
    content_type TEXT DEFAULT 'news',       -- 内容类型 (news/report/social等)
    date TEXT NOT NULL,                      -- 分析日期 YYYY-MM-DD
    sentiment_score REAL,                    -- 情感分数 (-1到1)
    sentiment_label TEXT,                    -- 情感标签 (positive/negative/neutral)
    analysis_content TEXT,                   -- 分析内容
    source_count INTEGER DEFAULT 1,         -- 来源数量
    confidence_score REAL,                  -- 置信度分数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_key, ticker)              -- 防止重复分析
);

-- 缓存配置表 (用于管理缓存策略)
CREATE TABLE IF NOT EXISTS cache_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_type TEXT NOT NULL,               -- 缓存类型
    cache_key TEXT NOT NULL,                -- 缓存键
    expiry_hours INTEGER DEFAULT 24,       -- 过期时间(小时)
    last_updated TIMESTAMP,                -- 最后更新时间
    is_active BOOLEAN DEFAULT 1,           -- 是否激活
    metadata TEXT,                          -- 元数据 (JSON格式)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cache_type, cache_key)
);

-- Agent管理表
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- Agent名称
    display_name TEXT NOT NULL,             -- 显示名称
    description TEXT,                       -- 描述
    agent_type TEXT NOT NULL,               -- Agent类型 (analysis/trading/risk等)
    status TEXT DEFAULT 'active',           -- 状态 (active/inactive/maintenance)
    config TEXT,                            -- 配置信息 (JSON格式)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent决策记录表
CREATE TABLE IF NOT EXISTS agent_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,                   -- 运行ID
    agent_name TEXT NOT NULL,               -- Agent名称
    ticker TEXT NOT NULL,                   -- 股票代码
    decision_type TEXT NOT NULL,            -- 决策类型 (buy/sell/hold/analysis)
    decision_data TEXT NOT NULL,            -- 决策数据 (JSON格式，包含完整的决策信息)
    confidence_score REAL,                  -- 置信度
    reasoning TEXT,                         -- 推理过程
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_name) REFERENCES agents(name)
);

-- 分析结果表 (存储各Agent的分析结果)
CREATE TABLE IF NOT EXISTS analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,                   -- 运行ID
    agent_name TEXT NOT NULL,               -- Agent名称
    ticker TEXT NOT NULL,                   -- 股票代码
    analysis_date TEXT NOT NULL,            -- 分析日期 YYYY-MM-DD
    analysis_type TEXT NOT NULL,            -- 分析类型 (technical/fundamental/sentiment等)
    result_data TEXT NOT NULL,              -- 分析结果 (JSON格式)
    confidence_score REAL,                  -- 置信度
    execution_time REAL,                    -- 执行时间(秒)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_name) REFERENCES agents(name)
);

-- 回测结果表
CREATE TABLE IF NOT EXISTS backtest_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,                   -- 回测运行ID
    ticker TEXT NOT NULL,                   -- 股票代码
    strategy_name TEXT,                     -- 策略名称
    start_date TEXT NOT NULL,               -- 开始日期
    end_date TEXT NOT NULL,                 -- 结束日期
    initial_capital REAL NOT NULL,          -- 初始资金
    final_value REAL,                       -- 最终价值
    total_return REAL,                      -- 总收益率
    sharpe_ratio REAL,                      -- 夏普比率
    max_drawdown REAL,                      -- 最大回撤
    trade_count INTEGER,                    -- 交易次数
    win_rate REAL,                          -- 胜率
    detailed_results TEXT,                  -- 详细结果 (JSON格式)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提升查询性能
CREATE INDEX IF NOT EXISTS idx_stock_news_ticker_date ON stock_news(ticker, date);
CREATE INDEX IF NOT EXISTS idx_stock_news_date ON stock_news(date);
CREATE INDEX IF NOT EXISTS idx_stock_price_ticker_date ON stock_price_data(ticker, date);
CREATE INDEX IF NOT EXISTS idx_stock_price_period ON stock_price_data(period);
CREATE INDEX IF NOT EXISTS idx_technical_indicators_ticker_date ON technical_indicators(ticker, date);
CREATE INDEX IF NOT EXISTS idx_technical_indicators_name ON technical_indicators(indicator_name);
CREATE INDEX IF NOT EXISTS idx_financial_metrics_ticker_date ON financial_metrics(ticker, report_date);
CREATE INDEX IF NOT EXISTS idx_financial_metrics_name ON financial_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_macro_analysis_date ON macro_analysis_cache(date);
CREATE INDEX IF NOT EXISTS idx_macro_analysis_type ON macro_analysis_cache(analysis_type);
CREATE INDEX IF NOT EXISTS idx_sentiment_cache_ticker_date ON sentiment_cache(ticker, date);
CREATE INDEX IF NOT EXISTS idx_sentiment_cache_type ON sentiment_cache(content_type);
CREATE INDEX IF NOT EXISTS idx_cache_config_type ON cache_config(cache_type);
CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_run_id ON agent_decisions(run_id);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_agent_name ON agent_decisions(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_ticker ON agent_decisions(ticker);
CREATE INDEX IF NOT EXISTS idx_analysis_results_run_id ON analysis_results(run_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_ticker_date ON analysis_results(ticker, analysis_date);
CREATE INDEX IF NOT EXISTS idx_backtest_results_ticker ON backtest_results(ticker);
CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy ON backtest_results(strategy_name);