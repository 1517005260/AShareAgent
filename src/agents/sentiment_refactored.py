"""
重构后的情感分析Agent，展示如何使用BaseAgent基类
"""
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

from langchain_core.messages import HumanMessage

from src.agents.base_agent import BaseAgent, AnalysisResult, create_agent_endpoint
from src.agents.state import AgentState
from src.tools.news_crawler import get_stock_news, get_news_sentiment
from src.utils.exceptions import MarketDataError, DataValidationError, ErrorRecoveryStrategy


class SentimentAgent(BaseAgent):
    """重构后的情感分析Agent"""
    
    def __init__(self):
        super().__init__("sentiment", "情感分析师，分析市场新闻和社交媒体情绪")
    
    def analyze(self, state: AgentState) -> Dict[str, Any]:
        """执行情感分析"""
        try:
            data = state["data"]
            symbol = data["ticker"]
            
            # 验证必需数据
            if not self.validate_data(data, ["ticker"]):
                raise DataValidationError("缺少必需的ticker信息")
            
            self.logger.info(f"正在分析股票: {symbol}")
            
            # 获取参数
            num_of_news = data.get("num_of_news", 20)
            end_date = data.get("end_date")
            
            # 获取和处理新闻数据
            news_data = self._get_and_filter_news(symbol, num_of_news, end_date)
            
            # 计算情感分数
            sentiment_score = self._calculate_sentiment(news_data, num_of_news)
            
            # 生成分析结果
            analysis_result = self._generate_analysis_result(sentiment_score, news_data)
            
            # 创建消息
            message = self.create_message(analysis_result.to_json())
            
            # 记录推理过程
            reasoning_data = {
                "symbol": symbol,
                "news_count": len(news_data),
                "sentiment_score": sentiment_score,
                "signal": analysis_result.signal,
                "confidence": analysis_result.confidence
            }
            self.log_reasoning(reasoning_data, state)
            
            return {
                "messages": state["messages"] + [message],
                "data": state["data"],
                "metadata": state["metadata"]
            }
            
        except Exception as e:
            return self._handle_error(e, state)
    
    def _get_and_filter_news(self, symbol: str, num_of_news: int, end_date: str = None) -> List[Dict[str, Any]]:
        """获取并过滤新闻数据"""
        try:
            # 获取新闻数据
            news_list = get_stock_news(symbol, max_news=num_of_news, date=end_date)
            
            if not news_list:
                self.logger.warning(f"未获取到{symbol}的新闻数据")
                return []
            
            # 过滤7天内的新闻
            cutoff_date = datetime.now() - timedelta(days=7)
            recent_news = []
            
            for news in news_list:
                if self._is_recent_news(news, cutoff_date):
                    recent_news.append(news)
            
            self.logger.info(f"获取到{len(recent_news)}条近期新闻")
            return recent_news
            
        except Exception as e:
            raise MarketDataError(f"获取新闻数据失败: {str(e)}", ticker=symbol, data_type="news")
    
    def _is_recent_news(self, news: Dict[str, Any], cutoff_date: datetime) -> bool:
        """检查新闻是否为近期新闻"""
        if 'publish_time' not in news:
            # 如果没有发布时间，默认包含
            return True
        
        try:
            news_date = datetime.strptime(news['publish_time'], '%Y-%m-%d %H:%M:%S')
            return news_date > cutoff_date
        except ValueError:
            # 时间格式解析失败，默认包含
            self.logger.warning(f"无法解析新闻时间格式: {news.get('publish_time')}")
            return True
    
    def _calculate_sentiment(self, news_data: List[Dict[str, Any]], num_of_news: int) -> float:
        """计算情感分数"""
        try:
            if not news_data:
                self.logger.warning("没有新闻数据用于情感分析")
                return 0.0
            
            sentiment_score = get_news_sentiment(news_data, num_of_news=num_of_news)
            self.logger.info(f"计算得到情感分数: {sentiment_score}")
            return sentiment_score
            
        except Exception as e:
            self.logger.error(f"情感分析计算失败: {str(e)}")
            return 0.0  # 返回中性分数
    
    def _generate_analysis_result(self, sentiment_score: float, news_data: List[Dict[str, Any]]) -> AnalysisResult:
        """生成分析结果"""
        # 根据情感分数确定信号和置信度
        if sentiment_score >= 0.5:
            signal = "bullish"
            confidence = min(sentiment_score, 1.0)
        elif sentiment_score <= -0.5:
            signal = "bearish"
            confidence = min(abs(sentiment_score), 1.0)
        else:
            signal = "neutral"
            confidence = 0.5 + abs(sentiment_score) * 0.5  # 中性信号的置信度基于偏离程度
        
        reasoning = self._generate_reasoning(sentiment_score, len(news_data), signal)
        
        additional_data = {
            "sentiment_score": sentiment_score,
            "news_count": len(news_data),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        return AnalysisResult(signal, confidence, reasoning, additional_data)
    
    def _generate_reasoning(self, sentiment_score: float, news_count: int, signal: str) -> str:
        """生成推理说明"""
        base_reasoning = f"基于{news_count}条近期新闻的情感分析，整体情感分数为{sentiment_score:.3f}。"
        
        if signal == "bullish":
            return base_reasoning + "市场情绪偏向积极，建议关注买入机会。"
        elif signal == "bearish":
            return base_reasoning + "市场情绪偏向消极，建议谨慎操作或考虑减仓。"
        else:
            return base_reasoning + "市场情绪相对中性，建议保持现有仓位。"
    
    def _handle_error(self, error: Exception, state: AgentState) -> Dict[str, Any]:
        """处理错误并返回安全的状态"""
        self.logger.error(f"情感分析失败: {str(error)}")
        
        # 创建错误恢复结果
        fallback_result = ErrorRecoveryStrategy.get_default_analysis_result(
            self.agent_name, str(error)
        )
        
        message = self.create_message(json.dumps(fallback_result, ensure_ascii=False))
        
        return {
            "messages": state["messages"] + [message],
            "data": state["data"],
            "metadata": state["metadata"]
        }


# 创建装饰后的函数以保持兼容性
sentiment_agent_instance = SentimentAgent()

@create_agent_endpoint(SentimentAgent)
def sentiment_agent_refactored(state: AgentState):
    """重构后的情感分析Agent入口点"""
    return sentiment_agent_instance.analyze(state)