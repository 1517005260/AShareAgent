"""
数据服务层 - 提供统一的数据访问接口
用于替代原有的JSON文件操作
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import hashlib

from .models import (
    DatabaseManager,
    StockNewsModel,
    StockPriceModel,
    TechnicalIndicatorModel,
    FinancialMetricModel,
    MacroAnalysisModel,
    SentimentCacheModel,
    AnalysisResultModel,
    CacheConfigModel
)


class DataService:
    """数据服务 - 统一的数据访问接口"""
    
    def __init__(self, db_path: str = "data/ashare_agent.db"):
        """初始化数据服务"""
        self.db_manager = DatabaseManager(db_path)
        
        # 初始化各个数据模型
        self.stock_news = StockNewsModel(self.db_manager)
        self.stock_price = StockPriceModel(self.db_manager)
        self.technical_indicator = TechnicalIndicatorModel(self.db_manager)
        self.financial_metric = FinancialMetricModel(self.db_manager)
        self.macro_analysis = MacroAnalysisModel(self.db_manager)
        self.sentiment_cache = SentimentCacheModel(self.db_manager)
        self.analysis_result = AnalysisResultModel(self.db_manager)
        self.cache_config = CacheConfigModel(self.db_manager)
    
    # ===== 股票新闻相关方法 =====
    
    def save_stock_news(self, ticker: str, date: str, method: str, query: str, 
                       news_data: List[Dict[str, Any]]) -> int:
        """保存股票新闻数据"""
        return self.stock_news.insert_news(ticker, date, method, query, news_data)
    
    def get_stock_news(self, ticker: str, date: str) -> List[Dict[str, Any]]:
        """获取股票新闻数据"""
        return self.stock_news.get_news_by_ticker_date(ticker, date)
    
    def get_stock_news_range(self, ticker: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """获取股票新闻数据范围"""
        return self.stock_news.get_news_by_ticker_range(ticker, start_date, end_date)
    
    # ===== 股票价格数据相关方法 =====
    
    def save_stock_price(self, ticker: str, date: str, price_data: Dict[str, Any],
                        period: str = 'daily', data_source: str = 'akshare') -> bool:
        """保存股票价格数据"""
        return self.stock_price.save_price_data(ticker, date, price_data, period, data_source)
    
    def get_stock_price(self, ticker: str, start_date: str, end_date: str,
                       period: str = 'daily') -> List[Dict[str, Any]]:
        """获取股票价格数据"""
        return self.stock_price.get_price_data(ticker, start_date, end_date, period)
    
    # ===== 技术指标相关方法 =====
    
    def save_technical_indicator(self, ticker: str, date: str, indicator_name: str,
                                indicator_value: float, indicator_params: Dict = None,
                                period: str = 'daily') -> bool:
        """保存技术指标数据"""
        return self.technical_indicator.save_indicator(
            ticker, date, indicator_name, indicator_value, indicator_params, period
        )
    
    def get_technical_indicators(self, ticker: str, indicator_names: List[str],
                               start_date: str, end_date: str, period: str = 'daily') -> List[Dict[str, Any]]:
        """获取技术指标数据"""
        return self.technical_indicator.get_indicators(ticker, indicator_names, start_date, end_date, period)
    
    # ===== 财务指标相关方法 =====
    
    def save_financial_metric(self, ticker: str, report_date: str, metric_name: str,
                             metric_value: float, unit: str = None, report_type: str = 'quarterly',
                             data_source: str = 'akshare') -> bool:
        """保存财务指标数据"""
        return self.financial_metric.save_metric(
            ticker, report_date, metric_name, metric_value, unit, report_type, data_source
        )
    
    def get_financial_metrics(self, ticker: str, metric_names: List[str],
                             report_type: str = 'quarterly', limit: int = 10) -> List[Dict[str, Any]]:
        """获取财务指标数据"""
        return self.financial_metric.get_metrics(ticker, metric_names, report_type, limit)
    
    # ===== 宏观分析相关方法 =====
    
    def save_macro_analysis(self, analysis_key: str, date: str, analysis_type: str = 'news',
                           macro_environment: str = None, impact_on_stock: str = None,
                           key_factors: List[str] = None, reasoning: str = None,
                           content: str = None, news_count: int = 0) -> bool:
        """保存宏观分析数据"""
        return self.macro_analysis.save_analysis(
            analysis_key, date, analysis_type, macro_environment, impact_on_stock,
            key_factors, reasoning, content, news_count
        )
    
    def get_macro_analysis(self, analysis_key: str, analysis_type: str = 'news') -> Optional[Dict[str, Any]]:
        """获取宏观分析数据"""
        return self.macro_analysis.get_analysis_by_key(analysis_key, analysis_type)
    
    def get_macro_analysis_by_date(self, date: str, analysis_type: str = 'summary') -> List[Dict[str, Any]]:
        """根据日期获取宏观分析数据"""
        return self.macro_analysis.get_analysis_by_date(date, analysis_type)
    
    # ===== 情感分析相关方法 =====
    
    def save_sentiment_analysis(self, content: str, sentiment_score: float, sentiment_label: str,
                               ticker: str = None, date: str = None, analysis_content: str = None,
                               content_type: str = 'news', confidence_score: float = None) -> bool:
        """保存情感分析数据"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # 生成内容键
        content_key = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        return self.sentiment_cache.save_sentiment(
            content_key, date, sentiment_score, sentiment_label,
            analysis_content, ticker, content_type, 1, confidence_score
        )
    
    def get_sentiment_analysis(self, content: str, ticker: str = None) -> Optional[Dict[str, Any]]:
        """获取情感分析数据"""
        content_key = hashlib.md5(content.encode('utf-8')).hexdigest()
        return self.sentiment_cache.get_sentiment_by_key(content_key, ticker)
    
    def get_sentiment_by_ticker_date(self, ticker: str, date: str) -> List[Dict[str, Any]]:
        """根据股票代码和日期获取情感分析"""
        return self.sentiment_cache.get_sentiment_by_ticker_date(ticker, date)
    
    def get_sentiment_from_cache(self, content: str, ticker: str = None) -> Optional[Dict[str, Any]]:
        """从缓存获取情感分析结果 (别名方法)"""
        return self.get_sentiment_analysis(content, ticker)
    
    def save_sentiment_to_cache(self, content: str, sentiment_score: float, sentiment_label: str,
                               ticker: str = None, date: str = None, analysis_content: str = None,
                               content_type: str = 'news', confidence_score: float = None) -> bool:
        """保存情感分析到缓存 (别名方法)"""
        return self.save_sentiment_analysis(content, sentiment_score, sentiment_label,
                                          ticker, date, analysis_content, content_type, confidence_score)
    
    def get_macro_analysis_from_cache(self, analysis_key: str, analysis_type: str = 'news') -> Optional[Dict[str, Any]]:
        """从缓存获取宏观分析结果 (别名方法)"""
        return self.get_macro_analysis(analysis_key, analysis_type)
    
    def save_macro_analysis_to_cache(self, analysis_key: str, date: str, analysis_type: str = 'news',
                                    macro_environment: str = None, impact_on_stock: str = None,
                                    key_factors: List[str] = None, reasoning: str = None,
                                    content: str = None, news_count: int = 0) -> bool:
        """保存宏观分析到缓存 (别名方法)"""
        return self.save_macro_analysis(analysis_key, date, analysis_type, macro_environment, 
                                      impact_on_stock, key_factors, reasoning, content, news_count)
    
    # ===== 分析结果相关方法 =====
    
    def save_analysis_result(self, run_id: str, agent_name: str, ticker: str, analysis_date: str,
                            analysis_type: str, result_data: Dict[str, Any], 
                            confidence_score: float = None, execution_time: float = None) -> bool:
        """保存分析结果"""
        return self.analysis_result.save_result(
            run_id, agent_name, ticker, analysis_date, analysis_type,
            result_data, confidence_score, execution_time
        )
    
    def get_analysis_results(self, run_id: str) -> List[Dict[str, Any]]:
        """获取分析结果"""
        return self.analysis_result.get_results_by_run(run_id)
    
    # ===== 缓存管理相关方法 =====
    
    def is_data_cached(self, cache_type: str, cache_key: str) -> bool:
        """检查数据是否已缓存且有效"""
        return self.cache_config.is_cache_valid(cache_type, cache_key)
    
    def set_cache_config(self, cache_type: str, cache_key: str, expiry_hours: int = 24,
                        metadata: Dict[str, Any] = None) -> bool:
        """设置缓存配置"""
        return self.cache_config.set_cache_config(cache_type, cache_key, expiry_hours, metadata)
    
    # ===== JSON兼容性方法 (用于逐步迁移) =====
    
    def load_json_compatible_macro_analysis(self, news_title: str, publish_time: str) -> Optional[Dict[str, Any]]:
        """加载兼容JSON格式的宏观分析数据"""
        analysis_key = f"{news_title}|{publish_time}"
        result = self.get_macro_analysis(analysis_key, 'news')
        
        if result:
            # 转换为原JSON格式
            return {
                'macro_environment': result.get('macro_environment'),
                'impact_on_stock': result.get('impact_on_stock'),
                'key_factors': json.loads(result.get('key_factors', '[]')) if result.get('key_factors') else [],
                'reasoning': result.get('reasoning')
            }
        return None
    
    def save_json_compatible_macro_analysis(self, news_title: str, publish_time: str, 
                                          analysis_data: Dict[str, Any]) -> bool:
        """保存兼容JSON格式的宏观分析数据"""
        analysis_key = f"{news_title}|{publish_time}"
        date = datetime.now().strftime('%Y-%m-%d')
        
        return self.save_macro_analysis(
            analysis_key=analysis_key,
            date=date,
            analysis_type='news',
            macro_environment=analysis_data.get('macro_environment'),
            impact_on_stock=analysis_data.get('impact_on_stock'),
            key_factors=analysis_data.get('key_factors', []),
            reasoning=analysis_data.get('reasoning'),
            content=json.dumps(analysis_data, ensure_ascii=False)
        )
    
    def load_json_compatible_sentiment_cache(self, content: str) -> Optional[float]:
        """加载兼容JSON格式的情感分析缓存"""
        result = self.get_sentiment_analysis(content)
        return result.get('sentiment_score') if result else None
    
    # ===== 数据存在性检查方法 =====
    
    def has_stock_news(self, ticker: str, date: str, min_count: int = 1) -> bool:
        """检查是否已有足够的股票新闻数据"""
        existing_news = self.get_stock_news(ticker, date)
        return len(existing_news) >= min_count
    
    def has_macro_analysis(self, news_key: str) -> bool:
        """检查是否已有宏观分析缓存"""
        return self.get_macro_analysis_from_cache(news_key) is not None
    
    def has_sentiment_analysis(self, content: str) -> bool:
        """检查是否已有情感分析缓存"""
        return self.get_sentiment_from_cache(content) is not None
    
    def has_sufficient_data_for_date(self, ticker: str, date: str, min_news: int = 5) -> bool:
        """检查指定日期是否有足够的数据，避免重复API调用"""
        return self.has_stock_news(ticker, date, min_news)
    
    def get_stock_news_smart(self, ticker: str, date: str, max_news: int = 10) -> List[Dict[str, Any]]:
        """智能获取股票新闻，优先使用本地数据，支持日期范围查询"""
        # 首先查询指定日期的新闻
        news_list = self.get_stock_news(ticker, date)
        
        # 如果数据不足，扩展查询范围到前后几天
        if len(news_list) < max_news:
            from datetime import datetime, timedelta
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
                # 扩展到前后3天
                start_date = (target_date - timedelta(days=3)).strftime("%Y-%m-%d")
                end_date = (target_date + timedelta(days=3)).strftime("%Y-%m-%d")
                
                range_news = self.get_stock_news_range(ticker, start_date, end_date)
                print(f"扩展查询范围 {start_date} 到 {end_date}，找到 {len(range_news)} 条新闻")
                return range_news[:max_news]
            except:
                pass
        
        return news_list[:max_news]
    
    def save_json_compatible_sentiment_cache(self, content: str, sentiment_score: float) -> bool:
        """保存兼容JSON格式的情感分析缓存"""
        if sentiment_score > 0.1:
            label = 'positive'
        elif sentiment_score < -0.1:
            label = 'negative'
        else:
            label = 'neutral'
        
        return self.save_sentiment_analysis(content, sentiment_score, label)
    
    def load_json_compatible_macro_summary(self, date: str) -> Optional[Dict[str, Any]]:
        """加载兼容JSON格式的宏观总结数据"""
        results = self.get_macro_analysis_by_date(date, 'summary')
        
        if results:
            result = results[0]
            return {
                'summary_content': result.get('content'),
                'retrieved_news_count': result.get('retrieved_news_count', 0),
                'last_updated': result.get('updated_at')
            }
        return None
    
    def save_json_compatible_macro_summary(self, date: str, summary_data: Dict[str, Any]) -> bool:
        """保存兼容JSON格式的宏观总结数据"""
        analysis_key = f"macro_summary_{date}"
        
        return self.save_macro_analysis(
            analysis_key=analysis_key,
            date=date,
            analysis_type='summary',
            content=summary_data.get('summary_content'),
            news_count=summary_data.get('retrieved_news_count', 0)
        )


# 全局数据服务实例
_data_service_instance = None


def get_data_service() -> DataService:
    """获取全局数据服务实例"""
    global _data_service_instance
    if _data_service_instance is None:
        _data_service_instance = DataService()
    return _data_service_instance


def initialize_data_service(db_path: str = None):
    """初始化数据服务"""
    global _data_service_instance
    if db_path:
        _data_service_instance = DataService(db_path)
    else:
        _data_service_instance = DataService()
    return _data_service_instance