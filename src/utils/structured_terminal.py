"""
结构化终端输出模块

此模块提供了一个简单但灵活的系统，用于收集和格式化agent数据，
然后在工作流结束时以美观、结构化的格式一次性展示。

完全独立于后端，只负责终端输出的格式化。
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.utils.logging_config import setup_logger

# 设置日志记录器
logger = setup_logger('structured_terminal')

# 格式化符号
SYMBOLS = {
    "border": "═",
    "header_left": "╔",
    "header_right": "╗",
    "footer_left": "╚",
    "footer_right": "╝",
    "separator": "─",
    "vertical": "║",
    "tree_branch": "├─",
    "tree_last": "└─",
    "section_prefix": "● ",
    "bullet": "• ",
}

# 状态图标
STATUS_ICONS = {
    "bearish": "📉",
    "bullish": "📈",
    "neutral": "◽",
    "hold": "⏸️",
    "buy": "🛒",
    "sell": "💰",
    "completed": "✅",
    "in_progress": "🔄",
    "error": "❌",
    "warning": "⚠️",
}

# Agent图标和名称映射
AGENT_MAP = {
    "market_data_agent": {"icon": "📊", "name": "市场数据"},
    "technical_analyst_agent": {"icon": "📈", "name": "技术"},
    "fundamentals_agent": {"icon": "📝", "name": "基本面"},
    "sentiment_agent": {"icon": "🔍", "name": "情感"},
    "valuation_agent": {"icon": "💰", "name": "估值"},
    "researcher_bull_agent": {"icon": "🐂", "name": "多方研究"},
    "researcher_bear_agent": {"icon": "🐻", "name": "空方研究"},
    "debate_room_agent": {"icon": "🗣️", "name": "辩论室"},
    "risk_management_agent": {"icon": "⚠️", "name": "风险管理"},
    "macro_analyst_agent": {"icon": "🌍", "name": "针对所选股宏观"},
    "macro_news_agent": {"icon": "📰", "name": "宏观新闻"},
    "portfolio_management_agent": {"icon": "📂", "name": "投资组合管理"}
}

# Agent显示顺序
AGENT_ORDER = [
    "market_data_agent",
    "technical_analyst_agent",
    "fundamentals_agent",
    "sentiment_agent",
    "valuation_agent",
    "researcher_bull_agent",
    "researcher_bear_agent",
    "debate_room_agent",
    "risk_management_agent",
    "macro_analyst_agent",
    "macro_news_agent",
    "portfolio_management_agent"
]


class StructuredTerminalOutput:
    """结构化终端输出类"""

    def __init__(self):
        """初始化"""
        self.data = {}
        self.metadata = {}

    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        self.metadata[key] = value

    def add_agent_data(self, agent_name: str, data: Any) -> None:
        """添加agent数据"""
        self.data[agent_name] = data

    def _format_value(self, value: Any, key: str = "") -> str:
        """格式化单个值"""
        if isinstance(value, bool):
            # 对于风险相关字段，❌表示无风险，显示为🟢低风险更直观
            if any(risk_word in key.lower() for risk_word in ['risk', 'pressure', 'crunch', 'sensitivity']):
                return "🟢" if not value else "🔴"  # False=低风险=绿色，True=高风险=红色
            else:
                return "✅" if value else "❌"  # 其他布尔值保持原逻辑
        elif isinstance(value, (int, float)):
            # 对百分比值进行特殊处理
            if -1 <= value <= 1 and isinstance(value, float):
                return f"{value:.2%}"
            elif isinstance(value, float):
                # 限制浮点数的小数位数，根据数值大小选择合适的精度
                if abs(value) >= 100:
                    return f"{value:.2f}"
                else:
                    return f"{value:.4f}"
            return str(value)
        elif value is None:
            return "N/A"
        else:
            return str(value)

    def _format_dict_as_tree(self, data: Dict[str, Any], indent: int = 0) -> List[str]:
        """将字典格式化为树形结构"""
        result = []
        items = list(data.items())

        for i, (key, value) in enumerate(items):
            is_last = i == len(items) - 1
            prefix = SYMBOLS["tree_last"] if is_last else SYMBOLS["tree_branch"]
            indent_str = "  " * indent

            if isinstance(value, dict) and value:
                result.append(f"{indent_str}{prefix} {key}:")
                result.extend(self._format_dict_as_tree(value, indent + 1))
            elif isinstance(value, list) and value:
                result.append(f"{indent_str}{prefix} {key}:")
                for j, item in enumerate(value):
                    sub_is_last = j == len(value) - 1
                    sub_prefix = SYMBOLS["tree_last"] if sub_is_last else SYMBOLS["tree_branch"]
                    if isinstance(item, dict):
                        result.append(
                            f"{indent_str}  {sub_prefix} Agent {j+1}:")
                        result.extend(
                            ["  " + line for line in self._format_dict_as_tree(item, indent + 2)])
                    else:
                        result.append(f"{indent_str}  {sub_prefix} {item}")
            else:
                formatted_value = self._format_value(value, key)
                result.append(f"{indent_str}{prefix} {key}: {formatted_value}")

        return result

    def _format_agent_section(self, agent_name: str, data: Any) -> List[str]:
        """格式化agent部分"""
        result = []

        # 获取agent信息
        agent_info = AGENT_MAP.get(
            agent_name, {"icon": "🔄", "name": agent_name})
        icon = agent_info["icon"]
        display_name = agent_info["name"]

        # 创建标题
        width = 80
        title = f"{icon} {display_name}分析"
        result.append(
            f"{SYMBOLS['header_left']}{SYMBOLS['border'] * ((width - len(title) - 2) // 2)} {title} {SYMBOLS['border'] * ((width - len(title) - 2) // 2)}{SYMBOLS['header_right']}")

        # 添加内容
        if isinstance(data, dict):
            # 特殊处理portfolio_management_agent
            if agent_name == "portfolio_management_agent":
                # 尝试提取action和confidence
                if "action" in data:
                    action = data.get("action", "")
                    action_icon = STATUS_ICONS.get(action.lower(), "")
                    result.append(
                        f"{SYMBOLS['vertical']} 交易行动: {action_icon} {action.upper() if action else ''}")

                if "quantity" in data:
                    quantity = data.get("quantity", 0)
                    result.append(f"{SYMBOLS['vertical']} 交易数量: {quantity}")

                if "confidence" in data:
                    conf = data.get("confidence", 0)
                    if isinstance(conf, (int, float)) and conf <= 1:
                        conf_str = f"{conf*100:.0f}%"
                    else:
                        conf_str = str(conf)
                    result.append(f"{SYMBOLS['vertical']} 决策信心: {conf_str}")

                # 显示各个Agent的信号
                if "agent_signals" in data:
                    result.append(
                        f"{SYMBOLS['vertical']} {SYMBOLS['section_prefix']}各分析师意见:")

                    for signal_info in data["agent_signals"]:
                        agent = signal_info.get("agent_name", signal_info.get("agent", ""))
                        signal = signal_info.get("signal", "")
                        conf = signal_info.get("confidence", 1.0)

                        # 跳过空信号
                        if not agent or not signal:
                            continue

                        # 获取信号图标
                        signal_icon = STATUS_ICONS.get(signal.lower(), "")

                        # 格式化置信度
                        if isinstance(conf, (int, float)) and conf <= 1:
                            conf_str = f"{conf*100:.0f}%"
                        else:
                            conf_str = str(conf)

                        result.append(
                            f"{SYMBOLS['vertical']}   • {agent}: {signal_icon} {signal} (置信度: {conf_str})")

                # 显示决策理由
                if "reasoning" in data:
                    reasoning = data["reasoning"]
                    result.append(
                        f"{SYMBOLS['vertical']} {SYMBOLS['section_prefix']}决策理由:")
                    if isinstance(reasoning, str):
                        # 将长文本拆分为多行，每行不超过width-4个字符
                        words = reasoning.split()
                        current_line = f"{SYMBOLS['vertical']}   "
                        for word in words:
                            if len(current_line + word + " ") > width:
                                result.append(current_line.rstrip())
                                current_line = f"{SYMBOLS['vertical']}   " + word + " "
                            else:
                                current_line += word + " "
                        if current_line.strip() != f"{SYMBOLS['vertical']}":
                            result.append(current_line.rstrip())
                
                # 显示其他详细字段
                remaining_data = {k: v for k, v in data.items() 
                                if k not in ["action", "quantity", "confidence", "agent_signals", "reasoning"]}
                if remaining_data:
                    tree_lines = self._format_dict_as_tree(remaining_data)
                    for line in tree_lines:
                        result.append(f"{SYMBOLS['vertical']} {line}")
            else:
                # 标准处理其他agent
                # 特殊处理researcher agents
                if agent_name in ["researcher_bull_agent", "researcher_bear_agent"]:
                    # 显示观点和置信度
                    if "perspective" in data:
                        perspective = data.get("perspective", "")
                        result.append(f"{SYMBOLS['vertical']} 观点:  {perspective.upper()}")
                    
                    if "confidence" in data:
                        conf = data.get("confidence", "")
                        if isinstance(conf, (int, float)) and conf <= 1:
                            conf_str = f"{conf*100:.1f}%"
                        else:
                            conf_str = str(conf)
                        result.append(f"{SYMBOLS['vertical']} 置信度: {conf_str}")
                    
                    # 显示论点
                    if "thesis_points" in data:
                        thesis_points = data.get("thesis_points", [])
                        result.append(f"{SYMBOLS['vertical']} 论点")
                        for point in thesis_points:
                            result.append(f"{SYMBOLS['vertical']} +")
                            result.append(f"{SYMBOLS['vertical']} + {point}")
                    
                    # 显示推理
                    if "reasoning" in data:
                        reasoning = data.get("reasoning", "")
                        result.append(f"{SYMBOLS['vertical']} {reasoning}")
                    
                    # 不显示重复的详细数据，直接返回
                elif agent_name == "technical_analyst_agent":
                    # 特殊处理技术分析
                    if "signal" in data:
                        signal = data.get("signal", "")
                        signal_icon = STATUS_ICONS.get(signal.lower(), "")
                        result.append(f"{SYMBOLS['vertical']} 信号: {signal_icon} {signal}")

                    if "confidence" in data:
                        conf = data.get("confidence", "")
                        if isinstance(conf, (int, float)) and conf <= 1:
                            conf_str = f"{conf*100:.0f}%"
                        else:
                            conf_str = str(conf)
                        result.append(f"{SYMBOLS['vertical']} 置信度: {conf_str}")
                    
                    # 显示策略信号详情
                    if "strategy_signals" in data:
                        result.append(f"{SYMBOLS['vertical']} 策略信号详情")
                        strategy_signals = data.get("strategy_signals", {})
                        for strategy, details in strategy_signals.items():
                            strategy_name = strategy.upper().replace('_', ' ')
                            signal = details.get('signal', 'neutral')
                            confidence = details.get('confidence', 50)
                            
                            # 安全地格式化置信度
                            if isinstance(confidence, (int, float)):
                                conf_str = f"{confidence:.0f}%"
                            elif isinstance(confidence, str):
                                # 如果是字符串，尝试去掉%号并转换
                                try:
                                    conf_val = float(confidence.replace('%', ''))
                                    conf_str = f"{conf_val:.0f}%"
                                except:
                                    conf_str = str(confidence)
                            else:
                                conf_str = str(confidence)
                                
                            result.append(f"{SYMBOLS['vertical']} {strategy_name}: {signal}")
                            result.append(f"{SYMBOLS['vertical']} 置信度: {conf_str}")
                            
                            # 显示指标
                            metrics = details.get('metrics', {})
                            for metric, value in metrics.items():
                                if isinstance(value, (int, float)):
                                    if metric in ['adx', 'trend_strength']:
                                        result.append(f"{SYMBOLS['vertical']} {metric}: {value:.4f}")
                                    else:
                                        result.append(f"{SYMBOLS['vertical']} {metric}: {value}")
                                else:
                                    result.append(f"{SYMBOLS['vertical']} {metric}: {value}")
                else:
                    # 提取信号和置信度（如果有）
                    if "signal" in data:
                        signal = data.get("signal", "")
                        signal_icon = STATUS_ICONS.get(signal.lower(), "")
                        result.append(
                            f"{SYMBOLS['vertical']} 信号: {signal_icon} {signal}")

                    if "confidence" in data:
                        conf = data.get("confidence", "")
                        if isinstance(conf, (int, float)) and conf <= 1:
                            conf_str = f"{conf*100:.0f}%"
                        else:
                            conf_str = str(conf)
                        result.append(f"{SYMBOLS['vertical']} 置信度: {conf_str}")

            # 添加其他数据 (但跳过特殊处理的agents的详细数据)
            if agent_name not in ["researcher_bull_agent", "researcher_bear_agent", "technical_analyst_agent"]:
                tree_lines = self._format_dict_as_tree(data)
                for line in tree_lines:
                    result.append(f"{SYMBOLS['vertical']} {line}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                prefix = SYMBOLS["tree_last"] if i == len(
                    data) - 1 else SYMBOLS["tree_branch"]
                result.append(f"{SYMBOLS['vertical']} {prefix} {item}")
        else:
            result.append(f"{SYMBOLS['vertical']} {data}")

        # 添加底部
        result.append(
            f"{SYMBOLS['footer_left']}{SYMBOLS['border'] * (width - 2)}{SYMBOLS['footer_right']}")

        return result

    def generate_output(self) -> str:
        """生成格式化输出"""
        width = 80
        result = []

        # 添加标题
        ticker = self.metadata.get("ticker", "未知")
        title = f"股票代码 {ticker} 投资分析报告"
        result.append(SYMBOLS["border"] * width)
        result.append(f"{title:^{width}}")
        result.append(SYMBOLS["border"] * width)

        # 添加日期范围（如果有）
        if "start_date" in self.metadata and "end_date" in self.metadata:
            date_range = f"分析区间: {self.metadata['start_date']} 至 {self.metadata['end_date']}"
            result.append(f"{date_range:^{width}}")
            result.append("")

        # 按顺序添加每个agent的输出
        for agent_name in AGENT_ORDER:
            if agent_name in self.data:
                result.extend(self._format_agent_section(
                    agent_name, self.data[agent_name]))
                result.append("")  # 添加空行

        # 添加结束分隔线
        result.append(SYMBOLS["border"] * width)

        return "\n".join(result)

    def print_output(self) -> None:
        """打印格式化输出"""
        output = self.generate_output()
        # 使用INFO级别记录，确保在控制台可见
        logger.info("\n" + output)


# 创建全局实例
terminal = StructuredTerminalOutput()


def extract_agent_data(state: Dict[str, Any], agent_name: str) -> Any:
    """
    从状态中提取指定agent的数据

    Args:
        state: 工作流状态
        agent_name: agent名称

    Returns:
        提取的agent数据
    """
    # 特殊处理portfolio_management_agent
    if agent_name == "portfolio_management_agent":
        # 尝试从最后一条消息中获取数据
        messages = state.get("messages", [])
        if messages and hasattr(messages[-1], "content"):
            content = messages[-1].content
            # 尝试解析JSON
            if isinstance(content, str):
                try:
                    # 如果是JSON字符串，尝试解析
                    if content.strip().startswith('{') and content.strip().endswith('}'):
                        return json.loads(content)
                    # 如果是JSON字符串包含在其他文本中，尝试提取并解析
                    json_start = content.find('{')
                    json_end = content.rfind('}')
                    if json_start >= 0 and json_end > json_start:
                        json_str = content[json_start:json_end+1]
                        return json.loads(json_str)
                except json.JSONDecodeError:
                    # 如果解析失败，返回原始内容
                    return {"message": content}
            return {"message": content}

    # 首先尝试从metadata中的all_agent_reasoning获取
    metadata = state.get("metadata", {})
    all_reasoning = metadata.get("all_agent_reasoning", {})

    # 查找匹配的agent数据
    for name, data in all_reasoning.items():
        if agent_name in name:
            return data

    # 如果在all_agent_reasoning中找不到，尝试从agent_reasoning获取
    if agent_name == metadata.get("current_agent_name") and "agent_reasoning" in metadata:
        return metadata["agent_reasoning"]

    # 尝试从messages中获取
    messages = state.get("messages", [])
    for message in messages:
        if hasattr(message, "name") and message.name and agent_name in message.name:
            # 尝试解析消息内容
            try:
                if hasattr(message, "content"):
                    content = message.content
                    # 尝试解析JSON
                    if isinstance(content, str) and (content.startswith('{') or content.startswith('[')):
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError:
                            pass
                    return content
            except Exception:
                pass

    # 如果都找不到，返回None
    return None


def process_final_state(state: Dict[str, Any]) -> None:
    """
    处理最终状态，提取所有agent的数据

    Args:
        state: 工作流的最终状态
    """
    # 提取元数据
    data = state.get("data", {})

    # 设置元数据
    terminal.set_metadata("ticker", data.get("ticker", "未知"))
    if "start_date" in data and "end_date" in data:
        terminal.set_metadata("start_date", data["start_date"])
        terminal.set_metadata("end_date", data["end_date"])

    # 提取每个agent的数据
    for agent_name in AGENT_ORDER:
        agent_data = extract_agent_data(state, agent_name)
        if agent_data:
            terminal.add_agent_data(agent_name, agent_data)


def print_structured_output(state: Dict[str, Any]) -> None:
    """
    处理最终状态并打印结构化输出

    Args:
        state: 工作流的最终状态
    """
    try:
        # 处理最终状态
        process_final_state(state)

        # 打印输出
        terminal.print_output()
    except Exception as e:
        logger.error(f"生成结构化输出时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
