"""
测试辩论室agent的功能

测试辩论室对多空观点的整合和决策逻辑
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage

from src.agents.debate_room import debate_room_agent


class TestDebateRoomAgent:
    """测试辩论室功能"""
    
    def test_basic_debate_processing(self, mock_agent_state):
        """测试基本辩论处理"""
        state = mock_agent_state.copy()
        
        # 创建多空研究员消息
        bull_msg = HumanMessage(
            content=json.dumps({
                "perspective": "bullish",
                "confidence": 0.75,
                "thesis_points": ["技术面突破", "基本面改善", "估值合理"],
                "reasoning": "综合分析显示看多机会"
            }),
            name="researcher_bull_agent"
        )
        
        bear_msg = HumanMessage(
            content=json.dumps({
                "perspective": "bearish", 
                "confidence": 0.65,
                "thesis_points": ["技术面存在回调风险", "估值偏高", "市场情绪过热"],
                "reasoning": "存在多重风险因素"
            }),
            name="researcher_bear_agent"
        )
        
        state["messages"] = [bull_msg, bear_msg]
        
        with patch('src.agents.debate_room.get_chat_completion') as mock_llm:
            mock_llm.return_value = json.dumps({
                "analysis": "多空双方都有合理观点，但看多论据更充分",
                "score": 0.3,
                "reasoning": "技术面和基本面支撑较强"
            })
            
            result = debate_room_agent(state)
        
        # 验证结果
        assert "messages" in result
        new_message = result["messages"][-1]
        assert new_message.name == "debate_room_agent"
        
        content = json.loads(new_message.content)
        assert "signal" in content
        assert "confidence" in content
        assert "reasoning" in content
        assert content["signal"] in ["bullish", "bearish", "neutral"]
    
    def test_ashare_specific_adjustments(self, mock_agent_state):
        """测试A股特色调整"""
        state = mock_agent_state.copy()
        
        # 创建包含政策因素的研究员消息
        bull_msg = HumanMessage(
            content=json.dumps({
                "perspective": "bullish",
                "confidence": 0.7,
                "thesis_points": ["受益政策支持"],
                "reasoning": "政策导向明确，基本面改善预期强烈"
            }),
            name="researcher_bull_agent"
        )
        
        bear_msg = HumanMessage(
            content=json.dumps({
                "perspective": "bearish",
                "confidence": 0.6,
                "thesis_points": ["流动性担忧"],
                "reasoning": "存在流动性风险和估值压力"
            }),
            name="researcher_bear_agent"
        )
        
        state["messages"] = [bull_msg, bear_msg]
        
        with patch('src.agents.debate_room.get_chat_completion') as mock_llm:
            mock_llm.return_value = json.dumps({
                "analysis": "政策因素是重要考量",
                "score": 0.2,
                "reasoning": "政策支持但需关注执行"
            })
            
            result = debate_room_agent(state)
        
        content = json.loads(result["messages"][-1].content)
        
        # 检查A股特色因素
        assert "ashare_factors" in content
        ashare_factors = content["ashare_factors"]
        assert "policy_sensitivity" in ashare_factors
        assert "liquidity_concerns" in ashare_factors
        assert "adaptive_threshold" in ashare_factors
    
    def test_balanced_debate_neutral_decision(self, mock_agent_state):
        """测试均衡辩论的中性决策"""
        state = mock_agent_state.copy()
        
        # 创建势均力敌的辩论
        bull_msg = HumanMessage(
            content=json.dumps({
                "perspective": "bullish",
                "confidence": 0.65,
                "thesis_points": ["技术面支撑", "政策利好"],
                "reasoning": "多重利好因素"
            }),
            name="researcher_bull_agent"
        )
        
        bear_msg = HumanMessage(
            content=json.dumps({
                "perspective": "bearish",
                "confidence": 0.68,
                "thesis_points": ["估值偏高", "经济担忧"],
                "reasoning": "风险因素不容忽视"
            }),
            name="researcher_bear_agent"
        )
        
        state["messages"] = [bull_msg, bear_msg]
        
        with patch('src.agents.debate_room.get_chat_completion') as mock_llm:
            # LLM返回中性评估
            mock_llm.return_value = json.dumps({
                "analysis": "双方观点都有道理，难以明确倾向",
                "score": 0.05,  # 接近中性
                "reasoning": "需要更多信息才能做出判断"
            })
            
            result = debate_room_agent(state)
        
        content = json.loads(result["messages"][-1].content)
        
        # 在势均力敌的情况下应该是中性决策
        assert content["signal"] == "neutral"
        assert "均衡" in content["reasoning"] or "balanced" in content["reasoning"].lower()
    
    def test_extreme_volatility_handling(self, mock_agent_state):
        """测试极端波动性处理"""
        state = mock_agent_state.copy()
        
        # 创建极端对立的观点
        bull_msg = HumanMessage(
            content=json.dumps({
                "perspective": "bullish",
                "confidence": 0.95,  # 极度乐观
                "thesis_points": ["技术面完美突破"],
                "reasoning": "所有指标都显示强烈看多"
            }),
            name="researcher_bull_agent"
        )
        
        bear_msg = HumanMessage(
            content=json.dumps({
                "perspective": "bearish",
                "confidence": 0.05,  # 极度悲观
                "thesis_points": ["系统性风险"],
                "reasoning": "所有指标都显示危险"
            }),
            name="researcher_bear_agent"
        )
        
        state["messages"] = [bull_msg, bear_msg]
        
        with patch('src.agents.debate_room.get_chat_completion') as mock_llm:
            mock_llm.return_value = json.dumps({
                "analysis": "观点分歧极大，需要谨慎",
                "score": 0.1,
                "reasoning": "市场可能存在不确定性"
            })
            
            result = debate_room_agent(state)
        
        content = json.loads(result["messages"][-1].content)
        
        # 检查是否识别了高波动性
        assert "ashare_factors" in content
        ashare_factors = content["ashare_factors"]
        assert ashare_factors["volatility_level"] > 0.8  # 应该识别为高波动
        
        # 决策质量应该反映分歧
        decision_quality = content["decision_quality"]
        assert decision_quality["consensus_strength"] < 0.5  # 共识度低
    
    def test_llm_failure_fallback(self, mock_agent_state):
        """测试LLM失败时的回退机制"""
        state = mock_agent_state.copy()
        
        bull_msg = HumanMessage(
            content=json.dumps({
                "perspective": "bullish",
                "confidence": 0.7,
                "thesis_points": ["基本面良好"],
                "reasoning": "综合看多"
            }),
            name="researcher_bull_agent"
        )
        
        bear_msg = HumanMessage(
            content=json.dumps({
                "perspective": "bearish",
                "confidence": 0.6,
                "thesis_points": ["风险偏高"],
                "reasoning": "需要谨慎"
            }),
            name="researcher_bear_agent"
        )
        
        state["messages"] = [bull_msg, bear_msg]
        
        with patch('src.agents.debate_room.get_chat_completion') as mock_llm:
            # 模拟LLM调用失败
            mock_llm.side_effect = Exception("API调用失败")
            
            result = debate_room_agent(state)
        
        # 即使LLM失败，也应该能产生合理的决策
        assert "messages" in result
        content = json.loads(result["messages"][-1].content)
        
        assert "signal" in content
        assert content["signal"] in ["bullish", "bearish", "neutral"]
        # 基于原始置信度差异的决策
        assert content["bull_confidence"] == 0.7
        assert content["bear_confidence"] == 0.6
    
    @patch('src.agents.debate_room.get_chat_completion')
    def test_adaptive_threshold_adjustment(self, mock_llm, mock_agent_state):
        """测试自适应阈值调整"""
        mock_llm.return_value = json.dumps({
            "analysis": "中等强度信号",
            "score": 0.15,
            "reasoning": "偏向看多但不明确"
        })
        
        state = mock_agent_state.copy()
        
        # 测试高波动性情况
        high_volatility_bull = HumanMessage(
            content=json.dumps({
                "perspective": "bullish",
                "confidence": 0.9,
                "thesis_points": ["极强信号"],
                "reasoning": "强烈看多"
            }),
            name="researcher_bull_agent"
        )
        
        high_volatility_bear = HumanMessage(
            content=json.dumps({
                "perspective": "bearish",
                "confidence": 0.1,
                "thesis_points": ["极弱信号"],
                "reasoning": "强烈看空"
            }),
            name="researcher_bear_agent"
        )
        
        state["messages"] = [high_volatility_bull, high_volatility_bear]
        
        result = debate_room_agent(state)
        content = json.loads(result["messages"][-1].content)
        
        # 高波动性应该导致更高的决策阈值
        assert "ashare_factors" in content
        adaptive_threshold = content["ashare_factors"]["adaptive_threshold"]
        assert adaptive_threshold > 0.1  # 应该比基础阈值更高
    
    def test_decision_quality_metrics(self, mock_agent_state):
        """测试决策质量指标"""
        state = mock_agent_state.copy()
        
        bull_msg = HumanMessage(
            content=json.dumps({
                "perspective": "bullish",
                "confidence": 0.75,
                "thesis_points": ["技术面良好"],
                "reasoning": "看多理由充分"
            }),
            name="researcher_bull_agent"
        )
        
        bear_msg = HumanMessage(
            content=json.dumps({
                "perspective": "bearish",
                "confidence": 0.65,
                "thesis_points": ["估值担忧"],
                "reasoning": "存在风险"
            }),
            name="researcher_bear_agent"
        )
        
        state["messages"] = [bull_msg, bear_msg]
        
        with patch('src.agents.debate_room.get_chat_completion') as mock_llm:
            mock_llm.return_value = json.dumps({
                "analysis": "均衡分析",
                "score": 0.2,
                "reasoning": "适度偏多"
            })
            
            result = debate_room_agent(state)
        
        content = json.loads(result["messages"][-1].content)
        
        # 检查决策质量指标
        assert "decision_quality" in content
        quality = content["decision_quality"]
        
        assert "consensus_strength" in quality
        assert "argument_balance" in quality
        assert "llm_agreement" in quality
        
        # 验证指标的合理范围
        assert 0 <= quality["consensus_strength"] <= 1
        assert 0 <= quality["argument_balance"] <= 1
        assert 0 <= quality["llm_agreement"] <= 1
    
    def test_missing_researcher_handling(self, mock_agent_state):
        """测试缺少研究员消息的处理"""
        state = mock_agent_state.copy()
        
        # 只有多头研究员，缺少空头研究员
        bull_msg = HumanMessage(
            content=json.dumps({
                "perspective": "bullish",
                "confidence": 0.8,
                "thesis_points": ["强烈看多"],
                "reasoning": "技术面突破"
            }),
            name="researcher_bull_agent"
        )
        
        state["messages"] = [bull_msg]
        
        # 应该抛出异常或处理错误
        with pytest.raises(ValueError, match="Missing required.*researcher"):
            debate_room_agent(state)