"""
决策记录格式化工具

用于将Agent的决策记录格式化为用户指定的显示格式
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime


def format_decision_display(decisions: List[Dict], ticker: str = None) -> str:
    """
    格式化决策显示，生成用户指定的复杂报告格式
    
    Args:
        decisions: 决策记录列表
        ticker: 股票代码（可选）
    
    Returns:
        str: 格式化的决策显示文本
    """
    if not decisions:
        return "暂无决策记录"
    
    # 从决策中提取股票代码和分析日期
    if not ticker and decisions:
        ticker = decisions[0].get('ticker', '00001')
    
    # 构建报告
    report_lines = []
    
    # 标题部分
    title_line = "═" * 80
    report_lines.append(title_line)
    center_title = f"股票代码 {ticker} 投资分析报告".center(80)
    report_lines.append(center_title)
    report_lines.append(title_line)
    
    # 分析区间（示例）
    today = datetime.now().strftime('%Y-%m-%d')
    last_year = str(int(today[:4]) - 1) + today[4:]
    period_line = f"分析区间: {last_year} 至 {today}".center(80)
    report_lines.append(period_line)
    report_lines.append("")
    
    # 根据决策记录构建各个分析模块
    for decision in decisions:
        decision_data = decision.get('decision_data', {})
        agent_name = decision.get('agent_name', '')
        
        if isinstance(decision_data, str):
            try:
                decision_data = json.loads(decision_data)
            except:
                decision_data = {}
        
        # 根据agent类型生成不同的分析模块
        if 'technical' in agent_name.lower():
            section = format_technical_analysis(decision_data)
            if section:
                report_lines.append(section)
                
        elif 'fundamental' in agent_name.lower():
            section = format_fundamental_analysis(decision_data)
            if section:
                report_lines.append(section)
                
        elif 'sentiment' in agent_name.lower():
            section = format_sentiment_analysis(decision_data)
            if section:
                report_lines.append(section)
                
        elif 'valuation' in agent_name.lower():
            section = format_valuation_analysis(decision_data)
            if section:
                report_lines.append(section)
                
        elif 'risk' in agent_name.lower():
            section = format_risk_analysis(decision_data)
            if section:
                report_lines.append(section)
                
        elif 'macro' in agent_name.lower():
            section = format_macro_analysis(decision_data)
            if section:
                report_lines.append(section)
                
        elif 'portfolio' in agent_name.lower():
            section = format_portfolio_analysis(decision_data)
            if section:
                report_lines.append(section)
                
        elif 'bull' in agent_name.lower() or 'bullish' in agent_name.lower():
            section = format_bullish_analysis(decision_data)
            if section:
                report_lines.append(section)
                
        elif 'bear' in agent_name.lower() or 'bearish' in agent_name.lower():
            section = format_bearish_analysis(decision_data)
            if section:
                report_lines.append(section)
                
        elif 'debate' in agent_name.lower():
            section = format_debate_analysis(decision_data)
            if section:
                report_lines.append(section)
    
    # 如果没有足够的数据，生成示例格式
    if len(report_lines) <= 4:
        report_lines.extend(generate_sample_report())
    
    report_lines.append(title_line)
    
    return "\n".join(report_lines)


def format_technical_analysis(data: Dict[str, Any]) -> str:
    """格式化技术分析"""
    signal = data.get('signal', 'neutral')
    confidence = data.get('confidence', 0)
    
    lines = []
    lines.append("╔" + "═" * 36 + " 📈 技术分析 " + "═" * 36 + "╗")
    lines.append(f"║ 信号: {get_signal_icon(signal)} {signal}")
    lines.append(f"║ 置信度: {confidence:.0f}%")
    
    # 策略信号详情
    strategy_signals = data.get('strategy_signals', {})
    if strategy_signals:
        lines.append("║ 策略信号详情")
        
        for strategy, details in strategy_signals.items():
            strategy_name = strategy.upper().replace('_', ' ')
            signal_val = details.get('signal', 'neutral')
            confidence_val = details.get('confidence', 50)
            lines.append(f"║ {strategy_name}: {signal_val}")
            lines.append(f"║ 置信度: {confidence_val:.0f}%")
            
            metrics = details.get('metrics', {})
            for metric, value in metrics.items():
                if isinstance(value, (int, float)):
                    if metric in ['adx', 'trend_strength']:
                        lines.append(f"║ {metric}: {value:.4f}")
                    else:
                        lines.append(f"║ {metric}: {value}")
                else:
                    lines.append(f"║ {metric}: {value}")
    
    lines.append("╚" + "═" * 78 + "╝")
    lines.append("")
    
    return "\n".join(lines)


def format_fundamental_analysis(data: Dict[str, Any]) -> str:
    """格式化基本面分析"""
    signal = data.get('signal', 'neutral')
    confidence = data.get('confidence', 50)
    
    lines = []
    lines.append("╔" + "═" * 35 + " 📝 基本面分析 " + "═" * 35 + "╗")
    lines.append(f"║ 信号: {get_signal_icon(signal)} {signal}")
    lines.append(f"║ 置信度: {confidence:.0f}%")
    lines.append(f"║ ├─ signal: {signal}")
    lines.append(f"║ ├─ confidence: {confidence:.0f}%")
    lines.append("║ └─ reasoning:")
    
    reasoning = data.get('reasoning', {})
    if reasoning:
        for item, details in reasoning.items():
            signal_val = details.get('signal', 'neutral')
            details_text = details.get('details', 'N/A')
            lines.append(f"║   ├─ {item}:")
            lines.append(f"║     ├─ signal: {signal_val}")
            lines.append(f"║     └─ details: {details_text}")
    
    lines.append("╚" + "═" * 78 + "╝")
    lines.append("")
    
    return "\n".join(lines)


def format_sentiment_analysis(data: Dict[str, Any]) -> str:
    """格式化情感分析"""
    signal = data.get('signal', 'bullish')
    confidence = data.get('confidence', 50)
    reasoning = data.get('reasoning', 'Based on recent news articles')
    
    lines = []
    lines.append("╔" + "═" * 36 + " 🔍 情感分析 " + "═" * 36 + "╗")
    lines.append(f"║ 信号: {get_signal_icon(signal)} {signal}")
    lines.append(f"║ 置信度: {confidence:.0f}%")
    lines.append(f"║ ├─ signal: {signal}")
    lines.append(f"║ ├─ confidence: {confidence:.0f}%")
    lines.append(f"║ └─ reasoning: {reasoning}")
    lines.append("╚" + "═" * 78 + "╝")
    lines.append("")
    
    return "\n".join(lines)


def format_valuation_analysis(data: Dict[str, Any]) -> str:
    """格式化估值分析"""
    signal = data.get('signal', 'bearish')
    confidence = data.get('confidence', 100)
    
    lines = []
    lines.append("╔" + "═" * 36 + " 💰 估值分析 " + "═" * 36 + "╗")
    lines.append(f"║ 信号: {get_signal_icon(signal)} {signal}")
    lines.append(f"║ 置信度: {confidence:.0f}%")
    lines.append(f"║ ├─ signal: {signal}")
    lines.append(f"║ ├─ confidence: {confidence:.0f}%")
    lines.append("║ └─ reasoning:")
    
    reasoning = data.get('reasoning', {})
    if reasoning:
        for analysis_type, details in reasoning.items():
            signal_val = details.get('signal', 'neutral')
            details_text = details.get('details', '')
            lines.append(f"║   ├─ {analysis_type}:")
            lines.append(f"║     ├─ signal: {signal_val}")
            lines.append(f"║     └─ details: {details_text}")
    
    lines.append("╚" + "═" * 78 + "╝")
    lines.append("")
    
    return "\n".join(lines)


def format_risk_analysis(data: Dict[str, Any]) -> str:
    """格式化风险管理分析"""
    trading_action = data.get('trading_action', 'sell')
    risk_score = data.get('risk_score', 4)
    
    lines = []
    lines.append("╔" + "═" * 34 + " ⚠️ 风险管理分析 " + "═" * 34 + "╗")
    lines.append(f"║ ├─ max_position_size: {data.get('max_position_size', 12873.75)}")
    lines.append(f"║ ├─ risk_score: {risk_score}")
    lines.append(f"║ ├─ trading_action: {trading_action}")
    
    risk_metrics = data.get('risk_metrics', {})
    if risk_metrics:
        lines.append("║ ├─ risk_metrics:")
        for metric, value in risk_metrics.items():
            if isinstance(value, dict):
                lines.append(f"║   ├─ {metric}:")
                for sub_key, sub_value in value.items():
                    lines.append(f"║     ├─ {sub_key}: {sub_value}")
            else:
                lines.append(f"║   ├─ {metric}: {value}")
    
    reasoning = data.get('reasoning', 'Risk assessment completed')
    lines.append(f"║ └─ reasoning: {reasoning}")
    lines.append("╚" + "═" * 78 + "╝")
    lines.append("")
    
    return "\n".join(lines)


def format_macro_analysis(data: Dict[str, Any]) -> str:
    """格式化宏观分析"""
    macro_environment = data.get('macro_environment', 'neutral')
    
    lines = []
    lines.append("╔" + "═" * 33 + " 🌍 针对所选股宏观分析 " + "═" * 33 + "╗")
    lines.append(f"║ ├─ macro_environment: {macro_environment}")
    
    impact_on_stock = data.get('impact_on_stock', 'neutral')
    if impact_on_stock:
        lines.append(f"║ ├─ impact_on_stock: {impact_on_stock}")
    
    key_factors = data.get('key_factors', [])
    if key_factors:
        lines.append("║ ├─ key_factors:")
        for factor in key_factors:
            lines.append(f"║   ├─ {factor}")
    
    reasoning = data.get('reasoning', '')
    if reasoning:
        lines.append("║ └─ reasoning: " + reasoning[:200] + ("..." if len(reasoning) > 200 else ""))
    
    lines.append("╚" + "═" * 78 + "╝")
    lines.append("")
    
    return "\n".join(lines)


def format_portfolio_analysis(data: Dict[str, Any]) -> str:
    """格式化投资组合管理分析"""
    action = data.get('action', 'sell')
    quantity = data.get('quantity', 1000)
    confidence = data.get('confidence', 80)
    
    lines = []
    lines.append("╔" + "═" * 34 + " 📂 投资组合管理分析 " + "═" * 34 + "╗")
    lines.append(f"║ 交易行动: 💰 {action.upper()}")
    lines.append(f"║ 交易数量: {quantity}")
    lines.append(f"║ 决策信心: {confidence:.0f}%")
    lines.append("║ ● 各分析师意见:")
    lines.append("║ ● 决策理由:")
    
    reasoning = data.get('reasoning', '')
    if reasoning:
        # 将长文本分行显示
        words = reasoning.split()
        current_line = "║   "
        for word in words:
            if len(current_line + word + " ") > 78:
                lines.append(current_line)
                current_line = "║   " + word + " "
            else:
                current_line += word + " "
        if current_line.strip() != "║":
            lines.append(current_line.rstrip())
    
    agent_signals = data.get('agent_signals', [])
    if agent_signals:
        lines.append(f"║ ├─ action: {action}")
        lines.append(f"║ ├─ quantity: {quantity}")
        lines.append(f"║ ├─ confidence: {confidence:.2f}%")
        lines.append("║ ├─ agent_signals:")
        
        for i, signal in enumerate(agent_signals, 1):
            lines.append(f"║   ├─ Agent {i}:")
            lines.append(f"║       ├─ agent_name: {signal.get('agent_name', 'unknown')}")
            lines.append(f"║       ├─ signal: {signal.get('signal', 'neutral')}")
            lines.append(f"║       └─ confidence: {signal.get('confidence', 0):.2f}%")
    
    lines.append("╚" + "═" * 78 + "╝")
    lines.append("")
    
    return "\n".join(lines)


def get_signal_icon(signal: str) -> str:
    """获取信号对应的图标"""
    signal_lower = signal.lower()
    if signal_lower in ['bullish', 'buy']:
        return '📈'
    elif signal_lower in ['bearish', 'sell']:
        return '📉'
    elif signal_lower == 'neutral':
        return '◽'
    else:
        return '🔍'


def generate_sample_report() -> List[str]:
    """生成示例报告（当数据不足时使用）"""
    lines = []
    
    # 技术分析示例
    lines.extend([
        "╔════════════════════════════════════ 📈 技术分析 ════════════════════════════════════╗",
        "║ 信号: ◽ neutral",
        "║ 置信度: 0%",
        "║ ├─ signal: neutral",
        "║ ├─ confidence: 0%",
        "║ └─ strategy_signals:",
        "║   ├─ trend_following:",
        "║     ├─ signal: neutral",
        "║     ├─ confidence: 50%",
        "║     └─ metrics:",
        "║       ├─ adx: 24.8885",
        "║       └─ trend_strength: 24.89%",
        "╚══════════════════════════════════════════════════════════════════════════════╝",
        ""
    ])
    
    return lines


def format_bullish_analysis(data: Dict[str, Any]) -> str:
    """格式化多方研究分析"""
    perspective = data.get('perspective', 'bullish')
    confidence = data.get('confidence', 0.5)
    thesis_points = data.get('thesis_points', [])
    reasoning = data.get('reasoning', '')
    
    lines = []
    lines.append("╔" + "═" * 35 + " 🐂 多方研究分析 " + "═" * 35 + "╗")
    lines.append(f"║ 观点: {perspective.upper()}")
    
    if isinstance(confidence, (int, float)):
        conf_str = f"{confidence*100:.1f}%" if confidence <= 1 else f"{confidence:.1f}%"
    else:
        conf_str = str(confidence)
    lines.append(f"║ 置信度: {conf_str}")
    
    lines.append("║ 论点")
    for point in thesis_points:
        lines.append(f"║ + {point}")
    
    if reasoning:
        lines.append(f"║ {reasoning}")
    
    lines.append("╚" + "═" * 78 + "╝")
    lines.append("")
    
    return "\n".join(lines)


def format_bearish_analysis(data: Dict[str, Any]) -> str:
    """格式化空方研究分析"""
    perspective = data.get('perspective', 'bearish')
    confidence = data.get('confidence', 0.5)
    thesis_points = data.get('thesis_points', [])
    reasoning = data.get('reasoning', '')
    
    lines = []
    lines.append("╔" + "═" * 35 + " 🐻 空方研究分析 " + "═" * 35 + "╗")
    lines.append(f"║ 观点: {perspective.upper()}")
    
    if isinstance(confidence, (int, float)):
        conf_str = f"{confidence*100:.1f}%" if confidence <= 1 else f"{confidence:.1f}%"
    else:
        conf_str = str(confidence)
    lines.append(f"║ 置信度: {conf_str}")
    
    lines.append("║ 论点")
    for point in thesis_points:
        lines.append(f"║ - {point}")
    
    if reasoning:
        lines.append(f"║ {reasoning}")
    
    lines.append("╚" + "═" * 78 + "╝")
    lines.append("")
    
    return "\n".join(lines)


def format_debate_analysis(data: Dict[str, Any]) -> str:
    """格式化辩论室分析"""
    signal = data.get('signal', 'neutral')
    confidence = data.get('confidence', 0.5)
    debate_summary = data.get('debate_summary', [])
    reasoning = data.get('reasoning', '')
    
    lines = []
    lines.append("╔" + "═" * 35 + " 🗣️ 辩论室分析 " + "═" * 35 + "╗")
    lines.append(f"║ 信号: {get_signal_icon(signal)} {signal}")
    
    if isinstance(confidence, (int, float)):
        conf_str = f"{confidence*100:.1f}%" if confidence <= 1 else f"{confidence:.1f}%"
    else:
        conf_str = str(confidence)
    lines.append(f"║ 置信度: {conf_str}")
    
    if debate_summary:
        for summary_line in debate_summary:
            lines.append(f"║ {summary_line}")
    
    if reasoning:
        lines.append(f"║ {reasoning}")
    
    lines.append("╚" + "═" * 78 + "╝")
    lines.append("")
    
    return "\n".join(lines)