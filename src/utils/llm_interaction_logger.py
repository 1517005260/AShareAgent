import functools
import io
import sys
import logging
from contextvars import ContextVar
from typing import Any, Callable, List, Optional, Dict, Tuple
from datetime import datetime, UTC

from backend.schemas import LLMInteractionLog, AgentExecutionLog
from backend.storage.base import BaseLogStorage
from src.agents.state import AgentState
from src.utils.serialization import serialize_agent_state

# --- Context Variables ---
# These variables hold state specific to the current execution context (e.g., a single agent run within a workflow).

# Holds the BaseLogStorage instance for the current run. Initialized in main.py.
log_storage_context: ContextVar[Optional[BaseLogStorage]] = ContextVar(
    "log_storage_context", default=None
)

# Holds the name of the agent currently being executed. Set by the decorator.
current_agent_name_context: ContextVar[Optional[str]] = ContextVar(
    "current_agent_name_context", default=None
)

# Holds the unique ID for the entire workflow run. Set in main.py and passed via state.
current_run_id_context: ContextVar[Optional[str]] = ContextVar(
    "current_run_id_context", default=None
)


# --- Output Capture Utility ---

class OutputCapture:
    """捕获标准输出和日志的工具类"""

    def __init__(self):
        self.outputs = []
        self.stdout_buffer = io.StringIO()
        self.old_stdout = None
        self.log_handler = None
        self.old_log_level = None

    def __enter__(self):
        # 捕获标准输出
        self.old_stdout = sys.stdout
        sys.stdout = self.stdout_buffer

        # 捕获日志
        self.log_handler = logging.StreamHandler(io.StringIO())
        self.log_handler.setLevel(logging.INFO)
        root_logger = logging.getLogger()
        self.old_log_level = root_logger.level
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(self.log_handler)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 恢复标准输出并捕获内容
        sys.stdout = self.old_stdout
        stdout_content = self.stdout_buffer.getvalue()
        if stdout_content.strip():
            self.outputs.append(stdout_content)

        # 恢复日志并捕获内容
        log_content = self.log_handler.stream.getvalue()
        if log_content.strip():
            self.outputs.append(log_content)

        # 清理日志处理器
        root_logger = logging.getLogger()
        root_logger.removeHandler(self.log_handler)
        root_logger.setLevel(self.old_log_level)


# --- Wrapper for LLM Calls ---

def wrap_llm_call(original_llm_func: Callable) -> Callable:
    """Wraps an LLM call function (like get_chat_completion) to log interactions.

    Reads context variables set by the agent decorator to get agent name,
    run ID, and the storage instance.

    Args:
        original_llm_func: The original function that makes the LLM call.

    Returns:
        A wrapped function that logs the interaction before returning the original result.
    """

    @functools.wraps(original_llm_func)
    def wrapper(*args, **kwargs) -> Any:
        # Retrieve context information
        storage = log_storage_context.get()
        agent_name = current_agent_name_context.get()
        run_id = current_run_id_context.get()

        # Proceed with the original call even if context is missing, but don't log
        if not storage or not agent_name:
            # Maybe log a warning here if desired
            return original_llm_func(*args, **kwargs)

        # Assume the first argument is usually the list of messages or prompt
        # This might need adjustment if the wrapped function signature varies
        request_data = args[0] if args else kwargs.get(
            'messages', kwargs)  # Adapt based on common usage

        # Execute the original LLM call
        response_data = original_llm_func(*args, **kwargs)

        # Create and store the log entry
        log_entry = LLMInteractionLog(
            agent_name=agent_name,
            run_id=run_id,  # run_id can be None if not set
            request_data=request_data,  # Consider serializing complex objects if needed
            response_data=response_data,  # Consider serializing complex objects if needed
            # Explicit timestamp in case storage adds its own
            timestamp=datetime.now(UTC)
        )
        storage.add_log(log_entry)

        return response_data

    return wrapper


# --- Decorator for Agent Functions ---

def log_agent_execution(agent_name: str):
    """Decorator for agent functions to set logging context variables.

    Retrieves the run_id from the agent state's metadata.

    Args:
        agent_name: The name of the agent being decorated.
    """

    def decorator(agent_func: Callable[[AgentState], AgentState]):
        @functools.wraps(agent_func)
        def wrapper(state: AgentState) -> AgentState:
            # Retrieve run_id from state metadata (set in main.py)
            run_id = state.get("metadata", {}).get("run_id")
            storage = log_storage_context.get()

            # 设置上下文变量
            agent_token = current_agent_name_context.set(agent_name)
            run_id_token = current_run_id_context.set(run_id)

            # 捕获开始时间和输入状态
            timestamp_start = datetime.now(UTC)
            serialized_input = serialize_agent_state(state)

            # 准备输出捕获
            output_capture = OutputCapture()
            result_state = None
            error = None

            try:
                # 使用输出捕获器
                with output_capture:
                    # 执行原始Agent函数
                    result_state = agent_func(state)

                # 成功执行，记录日志
                timestamp_end = datetime.now(UTC)
                terminal_outputs = output_capture.outputs

                if storage and result_state:
                    # 序列化输出状态
                    serialized_output = serialize_agent_state(result_state)

                    # 提取推理详情（如果有）
                    reasoning_details = None
                    if result_state.get("metadata", {}).get("show_reasoning", False):
                        if "agent_reasoning" in result_state.get("metadata", {}):
                            reasoning_details = result_state["metadata"]["agent_reasoning"]

                    # 创建日志条目
                    log_entry = AgentExecutionLog(
                        agent_name=agent_name,
                        run_id=run_id,
                        timestamp_start=timestamp_start,
                        timestamp_end=timestamp_end,
                        input_state=serialized_input,
                        output_state=serialized_output,
                        reasoning_details=reasoning_details,
                        terminal_outputs=terminal_outputs
                    )

                    # 存储日志
                    storage.add_agent_log(log_entry)
            except Exception as e:
                # 记录错误
                error = str(e)
                # 重新抛出异常，让上层处理
                raise
            finally:
                # 清理上下文变量
                current_agent_name_context.reset(agent_token)
                current_run_id_context.reset(run_id_token)

                # 如果出现错误但存储可用，记录错误日志
                if error and storage:
                    timestamp_end = datetime.now(UTC)
                    log_entry = AgentExecutionLog(
                        agent_name=agent_name,
                        run_id=run_id,
                        timestamp_start=timestamp_start,
                        timestamp_end=timestamp_end,
                        input_state=serialized_input,
                        output_state={"error": error},
                        reasoning_details=None,
                        terminal_outputs=output_capture.outputs
                    )
                    storage.add_agent_log(log_entry)

            return result_state
        return wrapper
    return decorator

# Helper to set the global storage instance (called from main.py)


def set_global_log_storage(storage: BaseLogStorage):
    log_storage_context.set(storage)
