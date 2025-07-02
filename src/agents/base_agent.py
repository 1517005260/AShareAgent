"""
基础Agent类，提供通用功能以减少代码重复
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from langchain_core.messages import HumanMessage

from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from src.utils.llm_clients import get_chat_completion
from src.utils.api_utils import agent_endpoint, log_llm_interaction

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """所有Agent的基类，提供通用功能"""
    
    def __init__(self, agent_name: str, description: str):
        self.agent_name = agent_name
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")
    
    @abstractmethod
    def analyze(self, state: AgentState) -> Dict[str, Any]:
        """子类必须实现的分析方法"""
        pass
    
    def safe_llm_call(self, messages: List[Dict[str, str]], 
                     fallback_response: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """安全的LLM调用，包含错误处理和重试机制"""
        try:
            response = get_chat_completion(messages)
            if response is None:
                self.logger.warning(f"{self.agent_name}: LLM返回None响应")
                return self._get_fallback_response(fallback_response)
            return response
        except Exception as e:
            self.logger.error(f"{self.agent_name}: LLM调用失败: {str(e)}")
            return self._get_fallback_response(fallback_response)
    
    def _get_fallback_response(self, fallback_response: Optional[Dict[str, Any]]) -> str:
        """获取后备响应"""
        if fallback_response:
            return json.dumps(fallback_response, ensure_ascii=False)
        return json.dumps({
            "signal": "neutral",
            "confidence": 0.0,
            "reasoning": f"{self.agent_name}分析失败，返回中性信号"
        }, ensure_ascii=False)
    
    def safe_json_parse(self, content: str, fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """安全的JSON解析"""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                # 尝试使用ast.literal_eval
                import ast
                return ast.literal_eval(content)
            except (ValueError, SyntaxError) as e:
                self.logger.error(f"{self.agent_name}: JSON解析失败: {str(e)}")
                self.logger.error(f"失败的内容前200字符: {content[:200]}...")
                return fallback or {"error": "解析失败"}
    
    def validate_data(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """验证数据是否包含必需字段"""
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            self.logger.error(f"{self.agent_name}: 缺少必需字段: {missing_fields}")
            return False
        return True
    
    def create_message(self, content: str, name: Optional[str] = None) -> HumanMessage:
        """创建标准化的消息"""
        return HumanMessage(
            content=content,
            name=name or self.agent_name
        )
    
    def log_reasoning(self, reasoning_data: Dict[str, Any], state: AgentState):
        """记录推理过程"""
        if state["metadata"].get("show_reasoning", False):
            show_agent_reasoning(reasoning_data, self.agent_name)
            state["metadata"]["agent_reasoning"] = reasoning_data


def create_agent_endpoint(agent_class):
    """装饰器工厂，为BaseAgent子类创建endpoint"""
    def decorator(agent_instance):
        @agent_endpoint(agent_instance.agent_name, agent_instance.description)
        def wrapper(state: AgentState):
            show_workflow_status(agent_instance.agent_name)
            return agent_instance.analyze(state)
        return wrapper
    return decorator


class AnalysisResult:
    """标准化的分析结果类"""
    
    def __init__(self, signal: str, confidence: float, reasoning: str, 
                 additional_data: Optional[Dict[str, Any]] = None):
        self.signal = signal  # "bullish", "bearish", "neutral"
        self.confidence = confidence  # 0.0 - 1.0
        self.reasoning = reasoning
        self.additional_data = additional_data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "signal": self.signal,
            "confidence": self.confidence,
            "reasoning": self.reasoning
        }
        result.update(self.additional_data)
        return result
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


# 常用的验证函数
def validate_financial_data(financial_metrics: List[Dict[str, Any]]) -> bool:
    """验证财务数据的完整性"""
    if not financial_metrics or len(financial_metrics) == 0:
        return False
    
    # 检查第一个财务指标字典是否包含基本字段
    first_metric = financial_metrics[0]
    required_fields = ['pe_ratio', 'market_cap']  # 基本必需字段
    
    return all(field in first_metric for field in required_fields)


def validate_price_data(prices: List[Dict[str, Any]]) -> bool:
    """验证价格数据的完整性"""
    if not prices or len(prices) == 0:
        return False
    
    # 检查是否包含基本的OHLCV数据
    required_fields = ['close', 'open', 'high', 'low', 'volume']
    return all(field in prices[0] for field in required_fields)