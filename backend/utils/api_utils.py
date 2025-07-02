"""
API工具函数模块

提供API服务使用的各种工具函数，如序列化、格式化等
"""

import json
from typing import Any, Dict


def safe_parse_json(data):
    """
    安全地解析可能是字符串形式的 JSON 数据

    如果输入是字符串并包含 JSON 内容，尝试解析为字典
    否则返回原始数据
    """
    if not isinstance(data, str):
        return data

    # 如果是字符串，尝试解析为 JSON
    try:
        # 如果字符串包含代码块格式，先清理一下
        if data.startswith("```") and "```" in data:
            # 去除 markdown 代码块标记
            lines = data.split("\n")
            # 找到真正的 JSON 开始行和结束行
            start_idx = 0
            end_idx = len(lines)
            for i, line in enumerate(lines):
                if line.startswith("```") and i == 0:
                    start_idx = 1
                elif line.startswith("```") and i > 0:
                    end_idx = i
                    break

            # 提取 JSON 内容
            json_content = "\n".join(lines[start_idx:end_idx])
            return json.loads(json_content)

        # 直接尝试解析
        return json.loads(data)
    except (json.JSONDecodeError, ValueError):
        # 如果解析失败，返回原始字符串
        return data


def serialize_for_api(obj: Any) -> Any:
    """将任意对象转换为API友好的格式，确保可JSON序列化"""
    if obj is None:
        return None

    # 首先尝试解析可能的 JSON 字符串
    obj = safe_parse_json(obj)

    if isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_api(x) for x in obj]
    elif isinstance(obj, dict):
        return {str(k): serialize_for_api(v) for k, v in obj.items()}
    elif hasattr(obj, 'dict') and callable(getattr(obj, 'dict')):
        # 处理Pydantic模型
        return serialize_for_api(obj.dict())
    elif hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
        # 处理有to_dict方法的对象
        return serialize_for_api(obj.to_dict())
    elif hasattr(obj, '__dict__'):
        # 处理一般Python对象
        return serialize_for_api(obj.__dict__)
    else:
        # 其他情况转为字符串
        return str(obj)


def format_llm_request(request_data: Any) -> Dict:
    """格式化LLM请求数据为可读格式"""
    if request_data is None:
        return {"message": "没有记录LLM请求"}

    # 先尝试解析可能的JSON字符串
    request_data = safe_parse_json(request_data)

    # 处理元组，通常是*args形式
    if isinstance(request_data, tuple):
        # 如果元组中有消息列表
        if len(request_data) > 0 and isinstance(request_data[0], list):
            messages = request_data[0]
            # 尝试将消息整理为统一格式
            formatted_messages = []
            message_texts = []

            for msg in messages:
                if isinstance(msg, dict):
                    formatted_msg = msg
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    message_texts.append(f"[{role}] {content}")
                elif hasattr(msg, 'type') and hasattr(msg, 'content'):
                    # 处理LangChain消息
                    formatted_msg = {
                        "role": msg.type,
                        "content": msg.content
                    }
                    message_texts.append(f"[{msg.type}] {msg.content}")
                else:
                    # 其他类型
                    formatted_msg = {"content": str(msg)}
                    message_texts.append(str(msg))

                formatted_messages.append(formatted_msg)

            return {
                "messages": formatted_messages,
                "formatted": "\n".join(message_texts)
            }
        # 处理其他参数形式
        return {"args": [serialize_for_api(arg) for arg in request_data]}

    # 处理字典，通常是**kwargs形式
    if isinstance(request_data, dict):
        return serialize_for_api(request_data)

    # 如果是列表，可能是消息列表
    if isinstance(request_data, list):
        try:
            # 尝试按消息列表处理
            formatted_messages = []
            message_texts = []

            for msg in request_data:
                if isinstance(msg, dict):
                    formatted_msg = msg
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    message_texts.append(f"[{role}] {content}")
                elif hasattr(msg, 'type') and hasattr(msg, 'content'):
                    # 处理LangChain消息
                    formatted_msg = {
                        "role": msg.type,
                        "content": msg.content
                    }
                    message_texts.append(f"[{msg.type}] {msg.content}")
                else:
                    # 其他类型
                    formatted_msg = {"content": str(msg)}
                    message_texts.append(str(msg))

                formatted_messages.append(formatted_msg)

            return {
                "messages": formatted_messages,
                "formatted": "\n".join(message_texts)
            }
        except Exception:
            # 如果无法处理为消息列表，按一般列表处理
            return {"items": [serialize_for_api(item) for item in request_data]}

    # 默认情况
    return {"data": serialize_for_api(request_data)}


def format_llm_response(response_data: Any) -> Dict:
    """格式化LLM响应数据为可读格式"""
    if response_data is None:
        return {"message": "没有记录LLM响应"}

    # 先尝试解析可能的JSON字符串
    response_data = safe_parse_json(response_data)

    # 处理有content属性的对象（如Gemini响应）
    if hasattr(response_data, 'text'):
        return {
            "text": response_data.text,
            "original": serialize_for_api(response_data)
        }

    # 处理字符串（直接返回的文本）
    if isinstance(response_data, str):
        return {"text": response_data}

    # 处理字典（可能是API响应）
    if isinstance(response_data, dict):
        if "choices" in response_data and isinstance(response_data["choices"], list):
            # 可能是OpenAI风格的响应
            try:
                messages = []
                for choice in response_data["choices"]:
                    if "message" in choice:
                        messages.append(choice["message"])

                if messages:
                    return {
                        "messages": messages,
                        "original": serialize_for_api(response_data)
                    }
            except Exception:
                pass

        # 一般的字典响应
        return serialize_for_api(response_data)

    # 处理字典或其他复杂对象
    return serialize_for_api(response_data)
