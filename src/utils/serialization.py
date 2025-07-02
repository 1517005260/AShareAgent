"""
序列化工具 - 用于将复杂的Python对象转换为JSON可序列化格式
"""

import json
from typing import Any, Dict
from datetime import datetime, UTC


def serialize_agent_state(state: Dict) -> Dict:
    """
    将AgentState对象转换为JSON可序列化的字典

    Args:
        state: Agent状态字典，可能包含不可JSON序列化的对象

    Returns:
        转换后的JSON友好字典
    """
    if not state:
        return {}

    try:
        return _convert_to_serializable(state)
    except Exception as e:
        # 如果序列化失败，至少返回一个有用的错误信息
        return {
            "error": f"无法序列化状态: {str(e)}",
            "serialization_error": True,
            "timestamp": datetime.now(UTC).isoformat()
        }


def _convert_to_serializable(obj: Any) -> Any:
    """递归地将对象转换为JSON可序列化格式"""
    if hasattr(obj, 'to_dict'):  # 处理Pandas Series/DataFrame
        return obj.to_dict()
    elif hasattr(obj, 'content') and hasattr(obj, 'type'):  # 可能是LangChain消息
        return {
            "content": _convert_to_serializable(obj.content),
            "type": obj.type
        }
    elif hasattr(obj, '__dict__'):  # 处理自定义对象
        return _convert_to_serializable(obj.__dict__)
    elif isinstance(obj, (int, float, bool, str, type(None))):
        return obj
    elif isinstance(obj, (list, tuple)):
        return [_convert_to_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {str(key): _convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return str(obj)  # 回退到字符串表示
