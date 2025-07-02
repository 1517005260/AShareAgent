"""
测试base_agent.py的基础功能

测试基础Agent类的通用功能，如LLM调用、JSON解析、数据验证等
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage

from src.agents.base_agent import BaseAgent, AnalysisResult, validate_financial_data, validate_price_data


class ConcreteTestAgent(BaseAgent):
    """用于测试的具体Agent实现"""
    def analyze(self, state):
        return {"signal": "neutral", "confidence": 0.5}


class TestBaseAgent:
    """测试BaseAgent基类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.agent = ConcreteTestAgent("test_agent", "测试agent")
    
    def test_init(self):
        """测试初始化"""
        assert self.agent.agent_name == "test_agent"
        assert self.agent.description == "测试agent"
        assert self.agent.logger is not None
    
    @patch('src.agents.base_agent.get_chat_completion')
    def test_safe_llm_call_success(self, mock_llm):
        """测试成功的LLM调用"""
        mock_llm.return_value = "test response"
        
        messages = [{"role": "user", "content": "test"}]
        result = self.agent.safe_llm_call(messages)
        
        assert result == "test response"
        mock_llm.assert_called_once_with(messages)
    
    @patch('src.agents.base_agent.get_chat_completion')
    def test_safe_llm_call_none_response(self, mock_llm):
        """测试LLM返回None的情况"""
        mock_llm.return_value = None
        
        messages = [{"role": "user", "content": "test"}]
        fallback = {"signal": "neutral", "confidence": 0.5}
        result = self.agent.safe_llm_call(messages, fallback)
        
        expected = json.dumps(fallback, ensure_ascii=False)
        assert result == expected
    
    @patch('src.agents.base_agent.get_chat_completion')
    def test_safe_llm_call_exception(self, mock_llm):
        """测试LLM调用异常"""
        mock_llm.side_effect = Exception("API Error")
        
        messages = [{"role": "user", "content": "test"}]
        result = self.agent.safe_llm_call(messages)
        
        # 应该返回默认的错误响应
        result_data = json.loads(result)
        assert result_data["signal"] == "neutral"
        assert "分析失败" in result_data["reasoning"]
    
    def test_safe_json_parse_valid(self):
        """测试有效JSON解析"""
        json_str = '{"signal": "bullish", "confidence": 0.8}'
        result = self.agent.safe_json_parse(json_str)
        
        assert result["signal"] == "bullish"
        assert result["confidence"] == 0.8
    
    def test_safe_json_parse_invalid(self):
        """测试无效JSON解析"""
        invalid_json = '{"signal": "bullish", "confidence":}'
        fallback = {"error": "parse_failed"}
        result = self.agent.safe_json_parse(invalid_json, fallback)
        
        assert result == fallback
    
    def test_safe_json_parse_ast_fallback(self):
        """测试AST回退解析"""
        # 这种格式JSON解析会失败，但AST可以解析
        ast_parseable = "{'signal': 'bullish', 'confidence': 0.8}"
        result = self.agent.safe_json_parse(ast_parseable)
        
        assert result["signal"] == "bullish"
        assert result["confidence"] == 0.8
    
    def test_validate_data_success(self):
        """测试数据验证成功"""
        data = {"pe_ratio": 12.5, "market_cap": 1000000000}
        required_fields = ["pe_ratio", "market_cap"]
        
        is_valid = self.agent.validate_data(data, required_fields)
        assert is_valid is True
    
    def test_validate_data_missing_fields(self):
        """测试缺少必需字段"""
        data = {"pe_ratio": 12.5}
        required_fields = ["pe_ratio", "market_cap"]
        
        is_valid = self.agent.validate_data(data, required_fields)
        assert is_valid is False
    
    def test_create_message(self):
        """测试创建消息"""
        content = '{"signal": "bullish"}'
        message = self.agent.create_message(content)
        
        assert isinstance(message, HumanMessage)
        assert message.content == content
        assert message.name == "test_agent"
    
    def test_create_message_custom_name(self):
        """测试创建自定义名称消息"""
        content = '{"signal": "bullish"}'
        custom_name = "custom_agent"
        message = self.agent.create_message(content, custom_name)
        
        assert message.name == custom_name


class TestAnalysisResult:
    """测试AnalysisResult类"""
    
    def test_init(self):
        """测试初始化"""
        result = AnalysisResult(
            signal="bullish",
            confidence=0.8,
            reasoning="Strong fundamentals",
            additional_data={"pe_ratio": 12.5}
        )
        
        assert result.signal == "bullish"
        assert result.confidence == 0.8
        assert result.reasoning == "Strong fundamentals"
        assert result.additional_data["pe_ratio"] == 12.5
    
    def test_to_dict(self):
        """测试转换为字典"""
        result = AnalysisResult(
            signal="bearish",
            confidence=0.6,
            reasoning="High valuation",
            additional_data={"risk_score": 8}
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["signal"] == "bearish"
        assert result_dict["confidence"] == 0.6
        assert result_dict["reasoning"] == "High valuation"
        assert result_dict["risk_score"] == 8
    
    def test_to_json(self):
        """测试转换为JSON"""
        result = AnalysisResult(
            signal="neutral",
            confidence=0.5,
            reasoning="Mixed signals"
        )
        
        json_str = result.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["signal"] == "neutral"
        assert parsed["confidence"] == 0.5
        assert parsed["reasoning"] == "Mixed signals"


class TestValidationFunctions:
    """测试验证函数"""
    
    def test_validate_financial_data_success(self):
        """测试财务数据验证成功"""
        financial_data = [
            {"pe_ratio": 12.5, "market_cap": 1000000000, "return_on_equity": 0.15}
        ]
        
        is_valid = validate_financial_data(financial_data)
        assert is_valid is True
    
    def test_validate_financial_data_empty(self):
        """测试空财务数据"""
        is_valid = validate_financial_data([])
        assert is_valid is False
        
        is_valid = validate_financial_data(None)
        assert is_valid is False
    
    def test_validate_financial_data_missing_fields(self):
        """测试缺少必需字段的财务数据"""
        financial_data = [
            {"return_on_equity": 0.15}  # 缺少pe_ratio和market_cap
        ]
        
        is_valid = validate_financial_data(financial_data)
        assert is_valid is False
    
    def test_validate_price_data_success(self):
        """测试价格数据验证成功"""
        import pandas as pd
        
        price_data = [
            {
                "close": 12.5,
                "open": 12.0,
                "high": 12.8,
                "low": 11.8,
                "volume": 1000000
            }
        ]
        
        is_valid = validate_price_data(price_data)
        assert is_valid is True
    
    def test_validate_price_data_empty(self):
        """测试空价格数据"""
        is_valid = validate_price_data([])
        assert is_valid is False
        
        is_valid = validate_price_data(None)
        assert is_valid is False
    
    def test_validate_price_data_missing_fields(self):
        """测试缺少必需字段的价格数据"""
        price_data = [
            {"close": 12.5, "open": 12.0}  # 缺少high, low, volume
        ]
        
        is_valid = validate_price_data(price_data)
        assert is_valid is False


@pytest.mark.unit
class TestBaseAgentIntegration:
    """BaseAgent集成测试"""
    
    @patch('src.agents.base_agent.get_chat_completion')
    def test_full_workflow(self, mock_llm):
        """测试完整工作流程"""
        mock_llm.return_value = json.dumps({
            "signal": "bullish",
            "confidence": 0.8,
            "reasoning": "Strong technical indicators"
        })
        
        agent = ConcreteTestAgent("integration_test", "集成测试agent")
        
        # 模拟状态
        state = {
            "messages": [],
            "data": {"stock_symbol": "000001"},
            "metadata": {"show_reasoning": True}
        }
        
        # 测试LLM调用
        messages = [{"role": "user", "content": "Analyze this stock"}]
        response = agent.safe_llm_call(messages)
        
        # 解析响应
        result = agent.safe_json_parse(response)
        
        # 验证结果
        assert result["signal"] == "bullish"
        assert result["confidence"] == 0.8
        assert "reasoning" in result
        
        # 创建消息
        message = agent.create_message(response)
        assert isinstance(message, HumanMessage)
        assert message.name == "integration_test"