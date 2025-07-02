"""
测试研究员agents的功能

测试researcher_bull和researcher_bear的决策逻辑
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage

from src.agents.researcher_bull import researcher_bull_agent  
from src.agents.researcher_bear import researcher_bear_agent


class TestResearcherBullAgent:
    """测试多头研究员"""
    
    def test_agent_registration(self):
        """测试agent是否正确注册"""
        # 检查函数是否存在
        assert callable(researcher_bull_agent)
        # 检查是否有正确的装饰器属性
        assert hasattr(researcher_bull_agent, '__wrapped__') or hasattr(researcher_bull_agent, 'endpoint_name')
    
    def test_bullish_signal_interpretation(self, mock_agent_state, sample_financial_data):
        """测试看多信号解读"""
        # 准备测试状态
        state = mock_agent_state.copy()
        
        # 创建模拟的分析师消息
        technical_msg = HumanMessage(
            content=json.dumps({"signal": "bullish", "confidence": 0.8}),
            name="technical_analyst_agent"
        )
        fundamental_msg = HumanMessage(
            content=json.dumps({"signal": "bullish", "confidence": 0.75}),
            name="fundamentals_agent"
        )
        sentiment_msg = HumanMessage(
            content=json.dumps({"signal": "neutral", "confidence": 0.6}),
            name="sentiment_agent"
        )
        valuation_msg = HumanMessage(
            content=json.dumps({"signal": "bullish", "confidence": 0.7}),
            name="valuation_agent"
        )
        
        state["messages"] = [technical_msg, fundamental_msg, sentiment_msg, valuation_msg]
        
        # 执行测试
        result = researcher_bull_agent(state)
        
        # 验证结果
        assert "messages" in result
        assert len(result["messages"]) == len(state["messages"]) + 1
        
        # 检查新消息
        new_message = result["messages"][-1]
        assert new_message.name == "researcher_bull_agent"
        
        # 解析消息内容
        content = json.loads(new_message.content)
        assert content["perspective"] == "bullish"
        assert isinstance(content["confidence"], float)
        assert 0 <= content["confidence"] <= 1
        assert "thesis_points" in content
        assert isinstance(content["thesis_points"], list)
    
    def test_bearish_signal_reinterpretation(self, mock_agent_state):
        """测试对看空信号的重新解读"""
        state = mock_agent_state.copy()
        
        # 创建看空信号的模拟消息
        technical_msg = HumanMessage(
            content=json.dumps({"signal": "bearish", "confidence": 0.7}),
            name="technical_analyst_agent"
        )
        fundamental_msg = HumanMessage(
            content=json.dumps({"signal": "bearish", "confidence": 0.6}),
            name="fundamentals_agent"
        )
        sentiment_msg = HumanMessage(
            content=json.dumps({"signal": "bearish", "confidence": 0.8}),
            name="sentiment_agent"
        )
        valuation_msg = HumanMessage(
            content=json.dumps({"signal": "bearish", "confidence": 0.5}),
            name="valuation_agent"
        )
        
        state["messages"] = [technical_msg, fundamental_msg, sentiment_msg, valuation_msg]
        
        result = researcher_bull_agent(state)
        
        # 验证多头研究员仍然能找到看多理由
        new_message = result["messages"][-1]
        content = json.loads(new_message.content)
        
        assert content["perspective"] == "bullish"
        assert len(content["thesis_points"]) > 0
        # 多头研究员应该将不利信号重新解读为机会
        thesis_text = " ".join(content["thesis_points"]).lower()
        assert any(keyword in thesis_text for keyword in ["机会", "opportunity", "potential", "买入"])
    
    def test_ashare_specific_features(self, mock_agent_state):
        """测试A股特色功能"""
        state = mock_agent_state.copy()
        
        # 创建包含A股特色的信号
        fundamental_msg = HumanMessage(
            content=json.dumps({
                "signal": "bullish", 
                "confidence": 0.8,
                "reasoning": {"policy_support": True}
            }),
            name="fundamentals_agent"
        )
        technical_msg = HumanMessage(
            content=json.dumps({"signal": "bullish", "confidence": 0.9}),
            name="technical_analyst_agent"
        )
        sentiment_msg = HumanMessage(
            content=json.dumps({"signal": "bullish", "confidence": 0.7}),
            name="sentiment_agent"
        )
        valuation_msg = HumanMessage(
            content=json.dumps({"signal": "bullish", "confidence": 0.6}),
            name="valuation_agent"
        )
        
        state["messages"] = [technical_msg, fundamental_msg, sentiment_msg, valuation_msg]
        
        result = researcher_bull_agent(state)
        new_message = result["messages"][-1]
        content = json.loads(new_message.content)
        
        # 检查A股特色因素
        assert "ashare_factors" in content
        assert "policy_sensitivity" in content["ashare_factors"]
        assert "signal_weights" in content
        
        # 验证A股权重配置
        weights = content["signal_weights"]
        assert weights["fundamental"] == 0.35  # A股基本面权重更高
        assert weights["technical"] == 0.25    # 适应T+1
        

class TestResearcherBearAgent:
    """测试空头研究员"""
    
    def test_bearish_signal_interpretation(self, mock_agent_state):
        """测试看空信号解读"""
        state = mock_agent_state.copy()
        
        # 创建看空信号
        technical_msg = HumanMessage(
            content=json.dumps({"signal": "bearish", "confidence": 0.8}),
            name="technical_analyst_agent"
        )
        fundamental_msg = HumanMessage(
            content=json.dumps({"signal": "bearish", "confidence": 0.75}),
            name="fundamentals_agent"
        )
        sentiment_msg = HumanMessage(
            content=json.dumps({"signal": "bearish", "confidence": 0.7}),
            name="sentiment_agent"
        )
        valuation_msg = HumanMessage(
            content=json.dumps({"signal": "bearish", "confidence": 0.9}),
            name="valuation_agent"
        )
        
        state["messages"] = [technical_msg, fundamental_msg, sentiment_msg, valuation_msg]
        
        result = researcher_bear_agent(state)
        
        # 验证结果
        new_message = result["messages"][-1]
        content = json.loads(new_message.content)
        
        assert content["perspective"] == "bearish"
        assert isinstance(content["confidence"], float)
        assert "thesis_points" in content
        assert "risk_factors" in content
    
    def test_bullish_signal_risk_identification(self, mock_agent_state):
        """测试对看多信号中风险的识别"""
        state = mock_agent_state.copy()
        
        # 创建强烈看多信号
        technical_msg = HumanMessage(
            content=json.dumps({"signal": "bullish", "confidence": 0.9}),
            name="technical_analyst_agent"
        )
        fundamental_msg = HumanMessage(
            content=json.dumps({"signal": "bullish", "confidence": 0.8}),
            name="fundamentals_agent"
        )
        sentiment_msg = HumanMessage(
            content=json.dumps({"signal": "bullish", "confidence": 0.85}),
            name="sentiment_agent"
        )
        valuation_msg = HumanMessage(
            content=json.dumps({"signal": "bullish", "confidence": 0.7}),
            name="valuation_agent"
        )
        
        state["messages"] = [technical_msg, fundamental_msg, sentiment_msg, valuation_msg]
        
        result = researcher_bear_agent(state)
        new_message = result["messages"][-1]
        content = json.loads(new_message.content)
        
        # 空头研究员应该在强劲信号中找到风险
        assert content["perspective"] == "bearish"
        assert len(content["thesis_points"]) > 0
        
        # 检查是否识别了过度乐观的风险
        thesis_text = " ".join(content["thesis_points"]).lower()
        risk_indicators = ["过度", "风险", "回调", "overvalued", "risk"]
        assert any(indicator in thesis_text for indicator in risk_indicators)
    
    def test_risk_concentration_analysis(self, mock_agent_state):
        """测试风险集中度分析"""
        state = mock_agent_state.copy()
        
        # 创建多重风险信号
        technical_msg = HumanMessage(
            content=json.dumps({"signal": "bearish", "confidence": 0.85}),
            name="technical_analyst_agent"
        )
        fundamental_msg = HumanMessage(
            content=json.dumps({
                "signal": "bearish", 
                "confidence": 0.8,
                "reasoning": {"policy_risk": True}
            }),
            name="fundamentals_agent"
        )
        sentiment_msg = HumanMessage(
            content=json.dumps({"signal": "bearish", "confidence": 0.9}),
            name="sentiment_agent"
        )
        valuation_msg = HumanMessage(
            content=json.dumps({"signal": "bearish", "confidence": 0.95}),
            name="valuation_agent"
        )
        
        state["messages"] = [technical_msg, fundamental_msg, sentiment_msg, valuation_msg]
        
        result = researcher_bear_agent(state)
        new_message = result["messages"][-1]
        content = json.loads(new_message.content)
        
        # 检查风险集中度分析
        assert "risk_concentration" in content
        assert "risk_factors" in content
        assert isinstance(content["risk_factors"], list)
        
        # 多重风险应该导致更高的风险集中度
        assert content["risk_concentration"] > 0


class TestResearcherAgentsComparison:
    """测试研究员对比分析"""
    
    def test_opposing_perspectives(self, mock_agent_state):
        """测试相同数据下的对立观点"""
        state = mock_agent_state.copy()
        
        # 创建中性偏多的信号
        technical_msg = HumanMessage(
            content=json.dumps({"signal": "bullish", "confidence": 0.6}),
            name="technical_analyst_agent"
        )
        fundamental_msg = HumanMessage(
            content=json.dumps({"signal": "neutral", "confidence": 0.5}),
            name="fundamentals_agent"
        )
        sentiment_msg = HumanMessage(
            content=json.dumps({"signal": "bearish", "confidence": 0.55}),
            name="sentiment_agent"
        )
        valuation_msg = HumanMessage(
            content=json.dumps({"signal": "bullish", "confidence": 0.65}),
            name="valuation_agent"
        )
        
        state["messages"] = [technical_msg, fundamental_msg, sentiment_msg, valuation_msg]
        
        # 获取多头和空头观点
        bull_result = researcher_bull_agent(state)
        bear_result = researcher_bear_agent(state)
        
        bull_content = json.loads(bull_result["messages"][-1].content)
        bear_content = json.loads(bear_result["messages"][-1].content)
        
        # 验证对立观点
        assert bull_content["perspective"] == "bullish"
        assert bear_content["perspective"] == "bearish"
        
        # 两个研究员应该都能找到支持自己观点的理由
        assert len(bull_content["thesis_points"]) > 0
        assert len(bear_content["thesis_points"]) > 0
        
        # 验证信心水平的合理性
        assert 0 <= bull_content["confidence"] <= 1
        assert 0 <= bear_content["confidence"] <= 1
    
    @pytest.mark.parametrize("signal_strength", [
        {"tech": 0.9, "fund": 0.85, "sent": 0.8, "val": 0.9},  # 强劲信号
        {"tech": 0.3, "fund": 0.4, "sent": 0.35, "val": 0.2},  # 弱势信号
        {"tech": 0.6, "fund": 0.5, "sent": 0.55, "val": 0.6},  # 中性信号
    ])
    def test_confidence_calibration(self, mock_agent_state, signal_strength):
        """测试置信度校准"""
        state = mock_agent_state.copy()
        
        # 创建不同强度的信号
        messages = []
        for agent_name, confidence in zip(
            ["technical_analyst_agent", "fundamentals_agent", "sentiment_agent", "valuation_agent"],
            [signal_strength["tech"], signal_strength["fund"], signal_strength["sent"], signal_strength["val"]]
        ):
            signal = "bullish" if confidence > 0.6 else "bearish" if confidence < 0.4 else "neutral"
            msg = HumanMessage(
                content=json.dumps({"signal": signal, "confidence": confidence}),
                name=agent_name
            )
            messages.append(msg)
        
        state["messages"] = messages
        
        # 测试两个研究员的响应
        bull_result = researcher_bull_agent(state)
        bear_result = researcher_bear_agent(state)
        
        bull_confidence = json.loads(bull_result["messages"][-1].content)["confidence"]
        bear_confidence = json.loads(bear_result["messages"][-1].content)["confidence"]
        
        # 验证置信度的合理性
        assert 0 <= bull_confidence <= 1
        assert 0 <= bear_confidence <= 1
        
        # 在强劲的多头信号下，多头研究员应该更自信
        if all(c > 0.7 for c in signal_strength.values()):
            assert bull_confidence > bear_confidence
        # 在强劲的空头信号下，空头研究员应该更自信  
        elif all(c < 0.4 for c in signal_strength.values()):
            assert bear_confidence > bull_confidence