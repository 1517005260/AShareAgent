from langchain_core.messages import HumanMessage
from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from src.utils.api_utils import agent_endpoint, log_llm_interaction
import json
import ast


@agent_endpoint("researcher_bull", "多方研究员，从看多角度分析市场数据并提出投资论点")
def researcher_bull_agent(state: AgentState):
    """Analyzes signals from a bullish perspective and generates optimistic investment thesis."""
    show_workflow_status("Bullish Researcher")
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

    # Enhanced A-share specific bullish analysis
    bullish_points = []
    weighted_scores = []
    signal_strengths = []
    
    # A股特色权重配置
    weights = {
        'fundamental': 0.35,  # A股基本面权重更高
        'technical': 0.25,    # 技术分析适应T+1
        'valuation': 0.25,    # 估值重要性
        'sentiment': 0.15     # 情绪影响
    }

    def _parse_confidence(confidence_value):
        """统一解析置信度值"""
        if isinstance(confidence_value, str):
            return float(confidence_value.replace('%', '')) / 100
        return float(confidence_value) if confidence_value else 0.0

    # Enhanced Technical Analysis with A-share characteristics
    tech_confidence = _parse_confidence(technical_signals.get('confidence', 0))
    if technical_signals["signal"] == "bullish":
        # 强化技术信号分析
        strength = "强势" if tech_confidence > 0.7 else "温和"
        bullish_points.append(f"技术面呈现{strength}看多信号，置信度{tech_confidence:.1%}")
        # A股特色：考虑涨跌停板影响
        if tech_confidence > 0.8:
            bullish_points.append("技术突破明显，可能触及涨停板")
        weighted_scores.append(tech_confidence * weights['technical'])
        signal_strengths.append(tech_confidence)
    else:
        # 更细致的弱势分析
        if tech_confidence < 0.3:
            bullish_points.append("技术面暂时走弱，但可能构筑底部区域")
            weighted_scores.append(0.4 * weights['technical'])  # 提高反转预期
        else:
            bullish_points.append("技术面中性偏弱，等待突破机会")
            weighted_scores.append(0.3 * weights['technical'])
        signal_strengths.append(0.4)

    # Enhanced Fundamental Analysis
    fund_confidence = _parse_confidence(fundamental_signals.get('confidence', 0))
    if fundamental_signals["signal"] == "bullish":
        quality = "优秀" if fund_confidence > 0.8 else "良好" if fund_confidence > 0.6 else "一般"
        bullish_points.append(f"基本面{quality}，盈利能力{fund_confidence:.1%}置信度")
        # A股特色：政策敏感性分析
        if 'policy_support' in fundamental_signals.get('reasoning', {}):
            bullish_points.append("受益于政策支持，基本面改善预期强烈")
        weighted_scores.append(fund_confidence * weights['fundamental'])
        signal_strengths.append(fund_confidence)
    else:
        # 寻找基本面改善催化剂
        if fund_confidence > 0.4:
            bullish_points.append("基本面虽有压力，但具备改善潜力")
            weighted_scores.append(0.5 * weights['fundamental'])
        else:
            bullish_points.append("基本面承压，需要关注拐点信号")
            weighted_scores.append(0.3 * weights['fundamental'])
        signal_strengths.append(0.4)

    # Enhanced Valuation Analysis
    val_confidence = _parse_confidence(valuation_signals.get('confidence', 0))
    if valuation_signals["signal"] == "bullish":
        value_level = "严重低估" if val_confidence > 0.8 else "低估" if val_confidence > 0.6 else "相对低估"
        bullish_points.append(f"估值{value_level}，安全边际{val_confidence:.1%}")
        # A股特色：与历史估值比较
        bullish_points.append("相比历史估值中枢具备投资价值")
        weighted_scores.append(val_confidence * weights['valuation'])
        signal_strengths.append(val_confidence)
    else:
        if val_confidence < 0.4:
            bullish_points.append("估值偏高但成长性可能支撑")
            weighted_scores.append(0.3 * weights['valuation'])
        else:
            bullish_points.append("估值合理，等待业绩兑现")
            weighted_scores.append(0.5 * weights['valuation'])
        signal_strengths.append(0.4)

    # Enhanced Sentiment Analysis
    sent_confidence = _parse_confidence(sentiment_signals.get('confidence', 0))
    if sentiment_signals["signal"] == "bullish":
        mood = "高涨" if sent_confidence > 0.7 else "积极"
        bullish_points.append(f"市场情绪{mood}，资金流入预期{sent_confidence:.1%}")
        weighted_scores.append(sent_confidence * weights['sentiment'])
        signal_strengths.append(sent_confidence)
    else:
        # 情绪低迷时寻找反转机会
        if sent_confidence < 0.3:
            bullish_points.append("市场情绪过度悲观，存在反转机会")
            weighted_scores.append(0.6 * weights['sentiment'])  # 反向指标
        else:
            bullish_points.append("市场情绪谨慎，需要催化剂")
            weighted_scores.append(0.3 * weights['sentiment'])
        signal_strengths.append(0.4)

    # Calculate sophisticated confidence score
    weighted_confidence = sum(weighted_scores)
    signal_consistency = 1 - (max(signal_strengths) - min(signal_strengths)) * 0.3  # 信号一致性调整
    avg_confidence = weighted_confidence * signal_consistency

    # A股特色投资逻辑
    def _generate_ashare_logic(strengths, tech_signals, fund_signals):
        """生成A股特色投资逻辑"""
        logic_parts = []
        
        # 技术面A股特色
        if max(strengths) > 0.7:
            logic_parts.append("技术面突破明确，符合A股强势特征")
        
        # 基本面政策导向
        if 'policy' in str(fund_signals).lower():
            logic_parts.append("受益政策导向，符合A股投资主线")
        
        # 流动性考量
        if min(strengths) > 0.4:
            logic_parts.append("各项指标均衡，适合A股波动环境")
        
        return "；".join(logic_parts) if logic_parts else "综合分析显示投资机会"
    
    investment_logic = _generate_ashare_logic(signal_strengths, technical_signals, fundamental_signals)
    
    message_content = {
        "perspective": "bullish",
        "confidence": min(avg_confidence, 0.95),  # 限制过度自信
        "thesis_points": bullish_points,
        "reasoning": f"基于A股市场特色的多头分析：{investment_logic}",
        "signal_weights": weights,
        "signal_consistency": signal_consistency,
        "ashare_factors": {
            "policy_sensitivity": 'policy' in str(fundamental_signals).lower(),
            "liquidity_risk": technical_signals.get('volume_analysis', {}).get('liquidity_score', 0.5),
            "institutional_flow": sentiment_signals.get('institutional_sentiment', 0.5)
        }
    }

    message = HumanMessage(
        content=json.dumps(message_content),
        name="researcher_bull_agent",
    )

    if show_reasoning:
        show_agent_reasoning(message_content, "Bullish Researcher")
        # 保存推理信息到metadata供API使用
        state["metadata"]["agent_reasoning"] = message_content

    show_workflow_status("Bullish Researcher", "completed")
    return {
        "messages": state["messages"] + [message],
        "data": state["data"],
        "metadata": state["metadata"],
    }
