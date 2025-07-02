"""
数据库模型定义
支持完整的金融数据存储和缓存管理
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
import json
import os
import hashlib


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "data/ashare_agent.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """初始化数据库，创建表结构"""
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        with self.get_connection() as conn:
            conn.executescript(schema_sql)
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以像字典一样访问
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询并返回结果"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新操作并返回影响的行数"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount


class StockNewsModel:
    """股票新闻数据模型"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def insert_news(self, ticker: str, date: str, method: str, query: str,
                    news_data: List[Dict[str, Any]]) -> int:
        """插入股票新闻数据"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            inserted_count = 0
            
            for news in news_data:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO stock_news 
                        (ticker, date, method, query, title, content, publish_time, source, url, keyword)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ticker, date, method, query,
                        news.get('title', ''), news.get('content', ''),
                        news.get('publish_time', ''), news.get('source', ''),
                        news.get('url', ''), news.get('keyword', '')
                    ))
                    if cursor.rowcount > 0:
                        inserted_count += 1
                except sqlite3.IntegrityError:
                    continue
            
            conn.commit()
            return inserted_count
    
    def get_news_by_ticker_date(self, ticker: str, date: str) -> List[Dict[str, Any]]:
        """根据股票代码和日期获取新闻"""
        return self.db_manager.execute_query("""
            SELECT * FROM stock_news 
            WHERE ticker = ? AND date = ?
            ORDER BY publish_time DESC
        """, (ticker, date))
    
    def get_news_by_ticker_range(self, ticker: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """根据股票代码和日期范围获取新闻"""
        return self.db_manager.execute_query("""
            SELECT * FROM stock_news 
            WHERE ticker = ? AND date BETWEEN ? AND ?
            ORDER BY date DESC, publish_time DESC
        """, (ticker, start_date, end_date))


class StockPriceModel:
    """股票价格数据模型"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save_price_data(self, ticker: str, date: str, price_data: Dict[str, Any], 
                       period: str = 'daily', data_source: str = 'akshare') -> bool:
        """保存股票价格数据"""
        return self.db_manager.execute_update("""
            INSERT OR REPLACE INTO stock_price_data 
            (ticker, date, period, open_price, high_price, low_price, close_price, 
             volume, turnover, data_source, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker, date, period,
            price_data.get('open'), price_data.get('high'), price_data.get('low'), price_data.get('close'),
            price_data.get('volume'), price_data.get('turnover'),
            data_source, datetime.now().isoformat()
        )) > 0
    
    def get_price_data(self, ticker: str, start_date: str, end_date: str, 
                      period: str = 'daily') -> List[Dict[str, Any]]:
        """获取股票价格数据"""
        return self.db_manager.execute_query("""
            SELECT * FROM stock_price_data 
            WHERE ticker = ? AND date BETWEEN ? AND ? AND period = ?
            ORDER BY date DESC
        """, (ticker, start_date, end_date, period))


class TechnicalIndicatorModel:
    """技术指标数据模型"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save_indicator(self, ticker: str, date: str, indicator_name: str, 
                      indicator_value: float, indicator_params: Dict = None,
                      period: str = 'daily') -> bool:
        """保存技术指标数据"""
        params_json = json.dumps(indicator_params) if indicator_params else None
        
        return self.db_manager.execute_update("""
            INSERT OR REPLACE INTO technical_indicators 
            (ticker, date, indicator_name, indicator_value, indicator_params, period, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ticker, date, indicator_name, indicator_value, params_json, period, datetime.now().isoformat())) > 0
    
    def get_indicators(self, ticker: str, indicator_names: List[str], 
                      start_date: str, end_date: str, period: str = 'daily') -> List[Dict[str, Any]]:
        """获取技术指标数据"""
        placeholders = ','.join(['?' for _ in indicator_names])
        return self.db_manager.execute_query(f"""
            SELECT * FROM technical_indicators 
            WHERE ticker = ? AND indicator_name IN ({placeholders})
            AND date BETWEEN ? AND ? AND period = ?
            ORDER BY date DESC, indicator_name
        """, (ticker, *indicator_names, start_date, end_date, period))


class FinancialMetricModel:
    """财务指标数据模型"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save_metric(self, ticker: str, report_date: str, metric_name: str,
                   metric_value: float, unit: str = None, report_type: str = 'quarterly',
                   data_source: str = 'akshare') -> bool:
        """保存财务指标数据"""
        return self.db_manager.execute_update("""
            INSERT OR REPLACE INTO financial_metrics 
            (ticker, report_date, report_type, metric_name, metric_value, unit, data_source, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ticker, report_date, report_type, metric_name, metric_value, unit, 
              data_source, datetime.now().isoformat())) > 0
    
    def get_metrics(self, ticker: str, metric_names: List[str], 
                   report_type: str = 'quarterly', limit: int = 10) -> List[Dict[str, Any]]:
        """获取财务指标数据"""
        placeholders = ','.join(['?' for _ in metric_names])
        return self.db_manager.execute_query(f"""
            SELECT * FROM financial_metrics 
            WHERE ticker = ? AND metric_name IN ({placeholders}) AND report_type = ?
            ORDER BY report_date DESC
            LIMIT ?
        """, (ticker, *metric_names, report_type, limit))


class MacroAnalysisModel:
    """宏观分析缓存模型"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save_analysis(self, analysis_key: str, date: str, analysis_type: str = 'news',
                     macro_environment: str = None, impact_on_stock: str = None,
                     key_factors: List[str] = None, reasoning: str = None,
                     content: str = None, news_count: int = 0) -> bool:
        """保存宏观分析数据"""
        key_factors_json = json.dumps(key_factors, ensure_ascii=False) if key_factors else None
        
        return self.db_manager.execute_update("""
            INSERT OR REPLACE INTO macro_analysis_cache 
            (analysis_key, analysis_type, date, macro_environment, impact_on_stock,
             key_factors, reasoning, content, retrieved_news_count, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (analysis_key, analysis_type, date, macro_environment, impact_on_stock,
              key_factors_json, reasoning, content, news_count, datetime.now().isoformat())) > 0
    
    def get_analysis_by_key(self, analysis_key: str, analysis_type: str = 'news') -> Optional[Dict[str, Any]]:
        """根据分析键获取宏观分析"""
        results = self.db_manager.execute_query("""
            SELECT * FROM macro_analysis_cache 
            WHERE analysis_key = ? AND analysis_type = ?
        """, (analysis_key, analysis_type))
        return results[0] if results else None
    
    def get_analysis_by_date(self, date: str, analysis_type: str = 'summary') -> List[Dict[str, Any]]:
        """根据日期获取宏观分析"""
        return self.db_manager.execute_query("""
            SELECT * FROM macro_analysis_cache 
            WHERE date = ? AND analysis_type = ?
            ORDER BY updated_at DESC
        """, (date, analysis_type))


class SentimentCacheModel:
    """情感分析缓存模型"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save_sentiment(self, content_key: str, date: str, sentiment_score: float,
                      sentiment_label: str, analysis_content: str = None,
                      ticker: str = None, content_type: str = 'news',
                      source_count: int = 1, confidence_score: float = None) -> bool:
        """保存情感分析结果"""
        return self.db_manager.execute_update("""
            INSERT OR REPLACE INTO sentiment_cache 
            (content_key, ticker, content_type, date, sentiment_score, sentiment_label,
             analysis_content, source_count, confidence_score, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (content_key, ticker, content_type, date, sentiment_score, sentiment_label,
              analysis_content, source_count, confidence_score, datetime.now().isoformat())) > 0
    
    def get_sentiment_by_key(self, content_key: str, ticker: str = None) -> Optional[Dict[str, Any]]:
        """根据内容键获取情感分析"""
        if ticker:
            results = self.db_manager.execute_query("""
                SELECT * FROM sentiment_cache WHERE content_key = ? AND ticker = ?
            """, (content_key, ticker))
        else:
            results = self.db_manager.execute_query("""
                SELECT * FROM sentiment_cache WHERE content_key = ?
            """, (content_key,))
        return results[0] if results else None
    
    def get_sentiment_by_ticker_date(self, ticker: str, date: str) -> List[Dict[str, Any]]:
        """根据股票代码和日期获取情感分析"""
        return self.db_manager.execute_query("""
            SELECT * FROM sentiment_cache 
            WHERE ticker = ? AND date = ?
            ORDER BY updated_at DESC
        """, (ticker, date))


class AnalysisResultModel:
    """分析结果数据模型"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save_result(self, run_id: str, agent_name: str, ticker: str, analysis_date: str,
                   analysis_type: str, result_data: Dict[str, Any], confidence_score: float = None,
                   execution_time: float = None) -> bool:
        """保存分析结果"""
        result_json = json.dumps(result_data, ensure_ascii=False)
        
        return self.db_manager.execute_update("""
            INSERT INTO analysis_results 
            (run_id, agent_name, ticker, analysis_date, analysis_type, result_data, 
             confidence_score, execution_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (run_id, agent_name, ticker, analysis_date, analysis_type, result_json,
              confidence_score, execution_time)) > 0
    
    def get_results_by_run(self, run_id: str) -> List[Dict[str, Any]]:
        """根据运行ID获取分析结果"""
        return self.db_manager.execute_query("""
            SELECT * FROM analysis_results WHERE run_id = ?
            ORDER BY created_at ASC
        """, (run_id,))


class CacheConfigModel:
    """缓存配置管理模型"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def set_cache_config(self, cache_type: str, cache_key: str, expiry_hours: int = 24,
                        metadata: Dict[str, Any] = None) -> bool:
        """设置缓存配置"""
        metadata_json = json.dumps(metadata) if metadata else None
        
        return self.db_manager.execute_update("""
            INSERT OR REPLACE INTO cache_config 
            (cache_type, cache_key, expiry_hours, last_updated, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (cache_type, cache_key, expiry_hours, datetime.now().isoformat(), metadata_json)) > 0
    
    def is_cache_valid(self, cache_type: str, cache_key: str) -> bool:
        """检查缓存是否有效"""
        results = self.db_manager.execute_query("""
            SELECT expiry_hours, last_updated FROM cache_config 
            WHERE cache_type = ? AND cache_key = ? AND is_active = 1
        """, (cache_type, cache_key))
        
        if not results:
            return False
        
        config = results[0]
        last_updated = datetime.fromisoformat(config['last_updated'])
        expiry_time = last_updated + timedelta(hours=config['expiry_hours'])
        
        return datetime.now() < expiry_time


class AgentModel:
    """Agent管理数据模型"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_agent(self, name: str, display_name: str, description: str = None,
                    agent_type: str = 'analysis', status: str = 'active',
                    config: Dict[str, Any] = None) -> bool:
        """创建Agent"""
        config_json = json.dumps(config, ensure_ascii=False) if config else None
        
        return self.db_manager.execute_update("""
            INSERT INTO agents 
            (name, display_name, description, agent_type, status, config)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, display_name, description, agent_type, status, config_json)) > 0
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """获取所有Agent"""
        return self.db_manager.execute_query("""
            SELECT * FROM agents ORDER BY created_at DESC
        """)
    
    def get_agent_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取Agent"""
        results = self.db_manager.execute_query("""
            SELECT * FROM agents WHERE name = ?
        """, (name,))
        return results[0] if results else None
    
    def update_agent_status(self, name: str, status: str) -> bool:
        """更新Agent状态"""
        return self.db_manager.execute_update("""
            UPDATE agents SET status = ?, updated_at = ? WHERE name = ?
        """, (status, datetime.now().isoformat(), name)) > 0
    
    def update_agent_config(self, name: str, config: Dict[str, Any]) -> bool:
        """更新Agent配置"""
        config_json = json.dumps(config, ensure_ascii=False)
        return self.db_manager.execute_update("""
            UPDATE agents SET config = ?, updated_at = ? WHERE name = ?
        """, (config_json, datetime.now().isoformat(), name)) > 0


class AgentDecisionModel:
    """Agent决策记录数据模型"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save_decision(self, run_id: str, agent_name: str, ticker: str, decision_type: str,
                     decision_data: Dict[str, Any], confidence_score: float = None,
                     reasoning: str = None) -> bool:
        """保存Agent决策记录"""
        decision_json = json.dumps(decision_data, ensure_ascii=False)
        
        return self.db_manager.execute_update("""
            INSERT INTO agent_decisions 
            (run_id, agent_name, ticker, decision_type, decision_data, confidence_score, reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (run_id, agent_name, ticker, decision_type, decision_json, confidence_score, reasoning)) > 0
    
    def get_decisions_by_run(self, run_id: str) -> List[Dict[str, Any]]:
        """根据运行ID获取决策记录"""
        return self.db_manager.execute_query("""
            SELECT * FROM agent_decisions WHERE run_id = ?
            ORDER BY created_at ASC
        """, (run_id,))
    
    def get_decisions_by_agent(self, agent_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """根据Agent名称获取决策记录"""
        return self.db_manager.execute_query("""
            SELECT * FROM agent_decisions WHERE agent_name = ?
            ORDER BY created_at DESC LIMIT ?
        """, (agent_name, limit))
    
    def get_recent_decisions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的决策记录"""
        return self.db_manager.execute_query("""
            SELECT ad.*, a.display_name as agent_display_name 
            FROM agent_decisions ad
            LEFT JOIN agents a ON ad.agent_name = a.name
            ORDER BY ad.created_at DESC LIMIT ?
        """, (limit,))
    
    def get_decisions_by_ticker(self, ticker: str, limit: int = 100) -> List[Dict[str, Any]]:
        """根据股票代码获取决策记录"""
        return self.db_manager.execute_query("""
            SELECT ad.*, a.display_name as agent_display_name 
            FROM agent_decisions ad
            LEFT JOIN agents a ON ad.agent_name = a.name
            WHERE ad.ticker = ? 
            ORDER BY ad.created_at DESC LIMIT ?
        """, (ticker, limit))