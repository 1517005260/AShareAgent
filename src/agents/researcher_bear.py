from langchain_core.messages import HumanMessage
from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from src.utils.api_utils import agent_endpoint, log_llm_interaction
import json
import ast


@agent_endpoint("researcher_bear", "空方研究员，从看空角度分析市场数据并提出风险警示")
def researcher_bear_agent(state: AgentState):
    """Analyzes signals from a bearish perspective and generates cautionary investment thesis."""
    show_workflow_status("Bearish Researcher")
    show_reasoning = state["metadata"]["show_reasoning"]

    # Fetch messages from analysts with safe fallback
    technical_message = next(
        (msg for msg in state["messages"] if msg.name == "technical_analyst_agent"), None)
    fundamentals_message = next(
        (msg for msg in state["messages"] if msg.name == "fundamentals_agent"), None)
    sentiment_message = next(
        (msg for msg in state["messages"] if msg.name == "sentiment_agent"), None)
    valuation_message = next(
        (msg for msg in state["messages"] if msg.name == "valuation_agent"), None)
    
    # Create default messages if any are missing
    default_signal = json.dumps({"signal": "neutral", "confidence": 0.5, "reasoning": "No data available"})
    if not technical_message:
        technical_message = HumanMessage(content=default_signal, name="technical_analyst_agent")
    if not fundamentals_message:
        fundamentals_message = HumanMessage(content=default_signal, name="fundamentals_agent")
    if not sentiment_message:
        sentiment_message = HumanMessage(content=default_signal, name="sentiment_agent")
    if not valuation_message:
        valuation_message = HumanMessage(content=default_signal, name="valuation_agent")

    try:
        fundamental_signals = json.loads(fundamentals_message.content)
        technical_signals = json.loads(technical_message.content)
        sentiment_signals = json.loads(sentiment_message.content)
        valuation_signals = json.loads(valuation_message.content)
    except Exception as e:
        fundamental_signals = ast.literal_eval(fundamentals_message.content)
        technical_signals = ast.literal_eval(technical_message.content)
        sentiment_signals = ast.literal_eval(sentiment_message.content)
        valuation_signals = ast.literal_eval(valuation_message.content)

    # Enhanced A-share specific bearish analysis
    bearish_points = []
    weighted_scores = []
    risk_factors = []
    
    # A股特色风险权重配置
    weights = {
        'fundamental': 0.35,  # 基本面风险权重高
        'technical': 0.25,    # 技术风险适应T+1
        'valuation': 0.25,    # 估值风险
        'sentiment': 0.15     # 情绪风险
    }

    def _parse_confidence(confidence_value):
        """统一解析置信度值"""
        if isinstance(confidence_value, str):
            return float(confidence_value.replace('%', '')) / 100
        return float(confidence_value) if confidence_value else 0.0

    # Enhanced Technical Risk Analysis
    tech_confidence = _parse_confidence(technical_signals.get('confidence', 0))
    if technical_signals["signal"] == "bearish":
        risk_level = "高风险" if tech_confidence > 0.7 else "中等风险"
        bearish_points.append(f"技术面呈现{risk_level}下跌信号，置信度{tech_confidence:.1%}")
        # A股特色：考虑跌停板风险
        if tech_confidence > 0.8:
            bearish_points.append("技术面急跌，存在跌停板风险")
            risk_factors.append("limit_down_risk")
        weighted_scores.append(tech_confidence * weights['technical'])
    else:
        # 技术上涨中的隐藏风险
        if tech_confidence > 0.7:
            bearish_points.append("技术面过度乐观，回调风险加大")
            weighted_scores.append(0.6 * weights['technical'])
            risk_factors.append("pullback_risk")
        else:
            bearish_points.append("技术上涨动能不足，需警惕反转")
            weighted_scores.append(0.4 * weights['technical'])

    # Enhanced Fundamental Risk Analysis
    fund_confidence = _parse_confidence(fundamental_signals.get('confidence', 0))
    if fundamental_signals["signal"] == "bearish":
        severity = "严重" if fund_confidence > 0.8 else "明显" if fund_confidence > 0.6 else "轻微"
        bearish_points.append(f"基本面{severity}恶化，风险置信度{fund_confidence:.1%}")
        # A股特色：政策风险敏感性
        if 'policy_risk' in fundamental_signals.get('reasoning', {}):
            bearish_points.append("面临政策风险，业绩可能持续压制")
            risk_factors.append("policy_risk")
        weighted_scores.append(fund_confidence * weights['fundamental'])
    else:
        # 基本面向好中的隐藏风险
        if fund_confidence > 0.7:
            bearish_points.append("基本面过度乐观，业绩兑现风险")
            weighted_scores.append(0.5 * weights['fundamental'])
            risk_factors.append("earnings_risk")
        else:
            bearish_points.append("基本面改善限制，增长可持续性存疑")
            weighted_scores.append(0.3 * weights['fundamental'])

    # Enhanced Valuation Risk Analysis  
    val_confidence = _parse_confidence(valuation_signals.get('confidence', 0))
    if valuation_signals["signal"] == "bearish":
        bubble_level = "严重泡沫" if val_confidence > 0.8 else "高估" if val_confidence > 0.6 else "偏高"
        bearish_points.append(f"估值{bubble_level}，回归风险{val_confidence:.1%}")
        # A股特色：与历史估值比较
        bearish_points.append("相比历史估值水平明显偏高")
        weighted_scores.append(val_confidence * weights['valuation'])
        risk_factors.append("valuation_risk")
    else:
        if val_confidence > 0.6:
            bearish_points.append("估值合理但增长预期过高")
            weighted_scores.append(0.4 * weights['valuation'])
        else:
            bearish_points.append("估值低但基本面支撑不足")
            weighted_scores.append(0.3 * weights['valuation'])

    # Enhanced Sentiment Risk Analysis
    sent_confidence = _parse_confidence(sentiment_signals.get('confidence', 0))
    if sentiment_signals["signal"] == "bearish":
        panic_level = "恐慌" if sent_confidence > 0.7 else "悲观"
        bearish_points.append(f"市场情绪{panic_level}，抛售压力{sent_confidence:.1%}")
        weighted_scores.append(sent_confidence * weights['sentiment'])
        risk_factors.append("sentiment_risk")
    else:
        # 情绪高涨时的反向风险
        if sent_confidence > 0.8:
            bearish_points.append("市场情绪过度乐观，反转风险加大")
            weighted_scores.append(0.7 * weights['sentiment'])
            risk_factors.append("euphoria_risk")
        else:
            bearish_points.append("市场情绪稳定但缺乏上涨动力")
            weighted_scores.append(0.3 * weights['sentiment'])

    # Calculate sophisticated risk score
    weighted_confidence = sum(weighted_scores)
    risk_concentration = len(set(risk_factors)) / 4.0  # 风险分散度
    avg_confidence = weighted_confidence * (1 + risk_concentration * 0.2)  # 风险集中度调整

    # A股特色风险逻辑
    def _generate_ashare_risk_logic(risk_factors, tech_signals, fund_signals):
        """生成A股特色风险逻辑"""
        logic_parts = []
        
        # 技术面A股风险
        if "limit_down_risk" in risk_factors:
            logic_parts.append("技术面存在跌停板风险")
        
        # 基本面政策风险
        if "policy_risk" in risk_factors:
            logic_parts.append("面临政策不确定性风险")
        
        # 流动性风险
        if "euphoria_risk" in risk_factors:
            logic_parts.append("市场情绪过热，流动性风险加大")
        
        # 综合风险
        if len(risk_factors) >= 3:
            logic_parts.append("多重风险叠加，需谨慎对待")
        
        return "；".join(logic_parts) if logic_parts else "存在潜在下行风险"
    
    risk_logic = _generate_ashare_risk_logic(risk_factors, technical_signals, fundamental_signals)
    
    message_content = {
        "perspective": "bearish",
        "confidence": min(avg_confidence, 0.95),  # 限制过度悲观
        "thesis_points": bearish_points,
        "reasoning": f"基于A股市场特色的风险分析：{risk_logic}",
        "risk_weights": weights,
        "risk_factors": risk_factors,
        "risk_concentration": risk_concentration,
        "ashare_risks": {
            "limit_down_risk": "limit_down_risk" in risk_factors,
            "policy_sensitivity": "policy_risk" in risk_factors,
            "liquidity_crunch": technical_signals.get('volume_analysis', {}).get('liquidity_stress', False),
            "margin_pressure": sentiment_signals.get('margin_sentiment', 0.5) > 0.7
        }
    }

    message = HumanMessage(
        content=json.dumps(message_content),
        name="researcher_bear_agent",
    )

    if show_reasoning:
        show_agent_reasoning(message_content, "Bearish Researcher")
    
    # 始终保存推理信息到metadata供API使用
    state["metadata"]["agent_reasoning"] = message_content

    show_workflow_status("Bearish Researcher", "completed")
    return {
        "messages": state["messages"] + [message],
        "data": state["data"],
        "metadata": state["metadata"],
    }
