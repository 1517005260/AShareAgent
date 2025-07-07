from langchain_core.messages import HumanMessage
from src.utils.logging_config import setup_logger

from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from src.utils.api_utils import agent_endpoint, log_llm_interaction

import json

# 初始化 logger
logger = setup_logger('fundamentals_agent')

##### Fundamental Agent #####


@agent_endpoint("fundamentals", "基本面分析师，分析公司财务指标、盈利能力和增长潜力")
def fundamentals_agent(state: AgentState):
    """Responsible for fundamental analysis"""
    show_workflow_status("Fundamentals Analyst")
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]
    metrics = data["financial_metrics"][0]

    # Initialize signals list for different fundamental aspects
    signals = []
    reasoning = {}

    # 1. Profitability Analysis
    return_on_equity = metrics.get("return_on_equity", None)
    net_margin = metrics.get("net_margin", None)
    operating_margin = metrics.get("operating_margin", None)

    thresholds = [
        (return_on_equity, 0.15),  # Strong ROE above 15%
        (net_margin, 0.20),  # Healthy profit margins
        (operating_margin, 0.15)  # Strong operating efficiency
    ]
    profitability_score = sum(
        metric is not None and metric > threshold
        for metric, threshold in thresholds
    )

    signals.append('bullish' if profitability_score >=
                   2 else 'bearish' if profitability_score == 0 else 'neutral')
    # 修复百分比显示问题：确保数值在合理范围内
    def format_percentage(value, name):
        if value is None:
            return f"{name}: N/A"
        # 检查是否为极端异常值
        if abs(value) > 10.0:  # 大于1000%的值视为异常
            return f"{name}: N/A (异常值)"
        # 检查是否为极端负增长（可能是数据质量问题）
        if value < -1.0:  # 过小的值可能有问题，特别是对于收入和利润增长
            return f"{name}: N/A (数据异常)"
        # 如果值已经是小数形式(如0.1563)，直接格式化为百分比
        return f"{name}: {value:.2%}"
    
    reasoning["profitability_signal"] = {
        "signal": signals[0],
        "details": format_percentage(metrics.get('return_on_equity'), "ROE") + 
                  ", " + format_percentage(metrics.get('net_margin'), "Net Margin") +
                  ", " + format_percentage(metrics.get('operating_margin'), "Op Margin")
    }

    # 2. Growth Analysis
    revenue_growth = metrics.get("revenue_growth", None)
    earnings_growth = metrics.get("earnings_growth", None)
    book_value_growth = metrics.get("book_value_growth", None)

    thresholds = [
        (revenue_growth, 0.10),  # 10% revenue growth
        (earnings_growth, 0.10),  # 10% earnings growth
        (book_value_growth, 0.10)  # 10% book value growth
    ]
    growth_score = sum(
        metric is not None and metric > threshold
        for metric, threshold in thresholds
    )

    signals.append('bullish' if growth_score >=
                   2 else 'bearish' if growth_score == 0 else 'neutral')
    reasoning["growth_signal"] = {
        "signal": signals[1],
        "details": format_percentage(metrics.get('revenue_growth'), "Revenue Growth") +
                  ", " + format_percentage(metrics.get('earnings_growth'), "Earnings Growth")
    }

    # 3. Financial Health
    current_ratio = metrics.get("current_ratio", None)
    debt_to_equity = metrics.get("debt_to_equity", None)
    free_cash_flow_per_share = metrics.get("free_cash_flow_per_share", None)
    earnings_per_share = metrics.get("earnings_per_share", None)

    health_score = 0
    if current_ratio and current_ratio > 1.5:  # Strong liquidity
        health_score += 1
    if debt_to_equity and debt_to_equity < 0.5:  # Conservative debt levels
        health_score += 1
    if (free_cash_flow_per_share and earnings_per_share and
            free_cash_flow_per_share > earnings_per_share * 0.8):  # Strong FCF conversion
        health_score += 1

    signals.append('bullish' if health_score >=
                   2 else 'bearish' if health_score == 0 else 'neutral')
    def format_ratio(value, name):
        if value is None or value == 0:
            return f"{name}: N/A"
        return f"{name}: {value:.2f}"
    
    reasoning["financial_health_signal"] = {
        "signal": signals[2],
        "details": format_ratio(metrics.get('current_ratio'), "Current Ratio") +
                  ", " + format_ratio(metrics.get('debt_to_equity'), "D/E")
    }

    # 4. Price to X ratios
    pe_ratio = metrics.get("pe_ratio", None)
    price_to_book = metrics.get("price_to_book", None)
    price_to_sales = metrics.get("price_to_sales", None)

    thresholds = [
        (pe_ratio, 25),  # Reasonable P/E ratio
        (price_to_book, 3),  # Reasonable P/B ratio
        (price_to_sales, 5)  # Reasonable P/S ratio
    ]
    price_ratio_score = sum(
        metric is not None and metric < threshold
        for metric, threshold in thresholds
    )

    signals.append('bullish' if price_ratio_score >=
                   2 else 'bearish' if price_ratio_score == 0 else 'neutral')
    reasoning["price_ratios_signal"] = {
        "signal": signals[3],
        "details": format_ratio(pe_ratio, "P/E") +
                  ", " + format_ratio(price_to_book, "P/B") +
                  ", " + format_ratio(price_to_sales, "P/S")
    }

    # Determine overall signal
    bullish_signals = signals.count('bullish')
    bearish_signals = signals.count('bearish')

    if bullish_signals > bearish_signals:
        overall_signal = 'bullish'
    elif bearish_signals > bullish_signals:
        overall_signal = 'bearish'
    else:
        overall_signal = 'neutral'

    # Calculate confidence level
    total_signals = len(signals)
    confidence = max(bullish_signals, bearish_signals) / total_signals

    message_content = {
        "signal": overall_signal,
        "confidence": f"{round(confidence * 100)}%",
        "reasoning": reasoning
    }

    # Create the fundamental analysis message
    message = HumanMessage(
        content=json.dumps(message_content),
        name="fundamentals_agent",
    )

    # Print the reasoning if the flag is set
    if show_reasoning:
        show_agent_reasoning(message_content, "Fundamental Analysis Agent")
    
    # 始终保存推理信息到metadata供API使用
    state["metadata"]["agent_reasoning"] = message_content

    show_workflow_status("Fundamentals Analyst", "completed")
    # logger.info(f"--- DEBUG: fundamentals_agent RETURN messages: {[msg.name for msg in [message]]} ---")
    return {
        "messages": [message],
        "data": {
            **data,
            "fundamental_analysis": message_content
        },
        "metadata": state["metadata"],
    }
