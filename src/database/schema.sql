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

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,             -- 用户名
    email TEXT NOT NULL UNIQUE,                -- 邮箱
    password_hash TEXT NOT NULL,               -- 密码哈希
    full_name TEXT,                            -- 全名
    phone TEXT,                                -- 电话
    is_active BOOLEAN DEFAULT 1,               -- 是否激活
    is_superuser BOOLEAN DEFAULT 0,            -- 是否超级管理员
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,                      -- 最后登录时间
    login_count INTEGER DEFAULT 0             -- 登录次数
);

-- 角色表
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,                -- 角色名称
    display_name TEXT NOT NULL,               -- 显示名称
    description TEXT,                         -- 描述
    is_active BOOLEAN DEFAULT 1,              -- 是否激活
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 权限表
CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,                -- 权限名称
    display_name TEXT NOT NULL,               -- 显示名称
    description TEXT,                         -- 描述
    resource TEXT NOT NULL,                   -- 资源类型 (analysis/portfolio/user/system)
    action TEXT NOT NULL,                     -- 操作类型 (create/read/update/delete/execute)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER,                      -- 分配者ID
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users(id),
    UNIQUE(user_id, role_id)
);

-- 角色权限关联表
CREATE TABLE IF NOT EXISTS role_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER,                       -- 授权者ID
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users(id),
    UNIQUE(role_id, permission_id)
);

-- 用户投资组合表
CREATE TABLE IF NOT EXISTS user_portfolios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,                       -- 组合名称
    description TEXT,                         -- 组合描述
    initial_capital REAL NOT NULL,            -- 初始资金
    current_value REAL,                       -- 当前价值
    cash_balance REAL,                        -- 现金余额
    risk_level TEXT DEFAULT 'medium',         -- 风险等级 (low/medium/high)
    is_active BOOLEAN DEFAULT 1,              -- 是否激活
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 用户持仓表
CREATE TABLE IF NOT EXISTS user_holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,                     -- 股票代码
    quantity INTEGER NOT NULL,                -- 持仓数量
    avg_cost REAL NOT NULL,                   -- 平均成本
    current_price REAL,                       -- 当前价格
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES user_portfolios(id) ON DELETE CASCADE,
    UNIQUE(portfolio_id, ticker)
);

-- 用户交易记录表
CREATE TABLE IF NOT EXISTS user_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,                     -- 股票代码
    transaction_type TEXT NOT NULL,           -- 交易类型 (buy/sell)
    quantity INTEGER NOT NULL,                -- 交易数量
    price REAL NOT NULL,                      -- 交易价格
    commission REAL DEFAULT 0,                -- 手续费
    total_amount REAL NOT NULL,               -- 总金额
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,                               -- 备注
    FOREIGN KEY (portfolio_id) REFERENCES user_portfolios(id) ON DELETE CASCADE
);

-- 用户分析任务表
CREATE TABLE IF NOT EXISTS user_analysis_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    task_id TEXT NOT NULL UNIQUE,             -- 任务ID
    ticker TEXT NOT NULL,                     -- 股票代码
    task_type TEXT DEFAULT 'analysis',        -- 任务类型 (analysis/backtest)
    status TEXT DEFAULT 'pending',            -- 状态 (pending/running/completed/failed)
    parameters TEXT,                          -- 任务参数 (JSON格式)
    result TEXT,                              -- 分析结果 (JSON格式)
    error_message TEXT,                       -- 错误信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,                     -- 开始时间
    completed_at TIMESTAMP,                  -- 完成时间
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 用户回测任务表
CREATE TABLE IF NOT EXISTS user_backtest_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    task_id TEXT NOT NULL UNIQUE,             -- 任务ID
    ticker TEXT NOT NULL,                     -- 股票代码
    start_date TEXT NOT NULL,                 -- 回测开始日期
    end_date TEXT NOT NULL,                   -- 回测结束日期
    status TEXT DEFAULT 'pending',            -- 状态 (pending/running/completed/failed)
    parameters TEXT,                          -- 回测参数 (JSON格式)
    result TEXT,                              -- 回测结果 (JSON格式)
    error_message TEXT,                       -- 错误信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,                     -- 开始时间
    completed_at TIMESTAMP,                  -- 完成时间
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT NOT NULL UNIQUE,          -- 配置键
    config_value TEXT,                        -- 配置值
    config_type TEXT DEFAULT 'string',        -- 配置类型 (string/number/boolean/json)
    description TEXT,                         -- 描述
    is_sensitive BOOLEAN DEFAULT 0,           -- 是否敏感信息
    category TEXT DEFAULT 'general',          -- 分类
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,                          -- 操作用户ID (可为空，系统操作)
    action TEXT NOT NULL,                     -- 操作类型
    resource TEXT,                            -- 操作资源
    resource_id TEXT,                         -- 资源ID
    details TEXT,                             -- 详细信息 (JSON格式)
    ip_address TEXT,                          -- IP地址
    user_agent TEXT,                          -- 用户代理
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- API调用统计表
CREATE TABLE IF NOT EXISTS api_usage_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    endpoint TEXT NOT NULL,                   -- API端点
    method TEXT NOT NULL,                     -- HTTP方法
    status_code INTEGER,                      -- 响应状态码
    response_time REAL,                       -- 响应时间(毫秒)
    request_size INTEGER,                     -- 请求大小(字节)
    response_size INTEGER,                    -- 响应大小(字节)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 初始化默认角色和权限
INSERT OR IGNORE INTO roles (name, display_name, description) VALUES
('admin', '系统管理员', '拥有系统所有权限'),
('premium_user', '高级用户', '拥有高级分析功能权限'),
('regular_user', '普通用户', '拥有基础功能权限');

INSERT OR IGNORE INTO permissions (name, display_name, description, resource, action) VALUES
-- 用户管理权限
('user:create', '创建用户', '创建新用户账户', 'user', 'create'),
('user:read', '查看用户', '查看用户信息', 'user', 'read'),
('user:update', '修改用户', '修改用户信息', 'user', 'update'),
('user:delete', '删除用户', '删除用户账户', 'user', 'delete'),
-- 分析功能权限
('analysis:basic', '基础分析', '执行基础股票分析', 'analysis', 'execute'),
('analysis:advanced', '高级分析', '执行高级分析功能', 'analysis', 'execute'),
('analysis:history', '历史分析', '查看历史分析记录', 'analysis', 'read'),
-- 回测功能权限
('backtest:basic', '基础回测', '执行基础回测功能', 'backtest', 'execute'),
('backtest:advanced', '高级回测', '执行高级回测功能', 'backtest', 'execute'),
('backtest:history', '回测历史', '查看回测历史记录', 'backtest', 'read'),
-- 组合管理权限
('portfolio:create', '创建组合', '创建投资组合', 'portfolio', 'create'),
('portfolio:read', '查看组合', '查看投资组合', 'portfolio', 'read'),
('portfolio:update', '修改组合', '修改投资组合', 'portfolio', 'update'),
('portfolio:delete', '删除组合', '删除投资组合', 'portfolio', 'delete'),
-- 系统管理权限
('system:config', '系统配置', '管理系统配置', 'system', 'update'),
('system:monitor', '系统监控', '查看系统监控信息', 'system', 'read'),
('system:logs', '系统日志', '查看系统日志', 'system', 'read');

-- 分配默认权限给角色
INSERT OR IGNORE INTO role_permissions (role_id, permission_id) 
SELECT r.id, p.id FROM roles r, permissions p 
WHERE r.name = 'admin'; -- 管理员拥有所有权限

INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p 
WHERE r.name = 'premium_user' AND p.name IN (
    'analysis:basic', 'analysis:advanced', 'analysis:history',
    'backtest:basic', 'backtest:advanced', 'backtest:history',
    'portfolio:create', 'portfolio:read', 'portfolio:update', 'portfolio:delete'
);

INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p 
WHERE r.name = 'regular_user' AND p.name IN (
    'analysis:basic', 'analysis:history',
    'backtest:basic', 'backtest:history',
    'portfolio:create', 'portfolio:read', 'portfolio:update'
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

-- 用户认证和权限相关索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);
CREATE INDEX IF NOT EXISTS idx_permissions_resource_action ON permissions(resource, action);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON role_permissions(permission_id);

-- 用户业务相关索引
CREATE INDEX IF NOT EXISTS idx_user_portfolios_user_id ON user_portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_user_portfolios_is_active ON user_portfolios(is_active);
CREATE INDEX IF NOT EXISTS idx_user_holdings_portfolio_id ON user_holdings(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_user_holdings_ticker ON user_holdings(ticker);
CREATE INDEX IF NOT EXISTS idx_user_transactions_portfolio_id ON user_transactions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_user_transactions_ticker ON user_transactions(ticker);
CREATE INDEX IF NOT EXISTS idx_user_transactions_date ON user_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_user_analysis_tasks_user_id ON user_analysis_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_user_analysis_tasks_task_id ON user_analysis_tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_user_analysis_tasks_status ON user_analysis_tasks(status);
CREATE INDEX IF NOT EXISTS idx_user_backtest_tasks_user_id ON user_backtest_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_user_backtest_tasks_task_id ON user_backtest_tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_user_backtest_tasks_status ON user_backtest_tasks(status);
CREATE INDEX IF NOT EXISTS idx_user_backtest_tasks_ticker ON user_backtest_tasks(ticker);

-- 系统管理相关索引
CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);
CREATE INDEX IF NOT EXISTS idx_system_config_category ON system_config(category);
CREATE INDEX IF NOT EXISTS idx_system_logs_user_id ON system_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_action ON system_logs(action);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_stats_user_id ON api_usage_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_stats_endpoint ON api_usage_stats(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_usage_stats_created_at ON api_usage_stats(created_at);