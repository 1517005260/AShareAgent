from typing import List, Optional, Set
from collections import deque
import threading

from .base import BaseLogStorage
from backend.schemas import LLMInteractionLog, AgentExecutionLog

# Define a maximum size for the in-memory log to prevent unbounded growth
MAX_LOG_SIZE = 1000


class InMemoryLogStorage(BaseLogStorage):
    """In-memory storage for LLM interaction logs using a deque."""

    def __init__(self):
        # Use a deque for efficient appends and pops from both ends
        # Set maxlen for automatic discarding of old logs
        self._logs: deque[LLMInteractionLog] = deque(maxlen=MAX_LOG_SIZE)
        # Create a separate deque for agent execution logs
        self._agent_logs: deque[AgentExecutionLog] = deque(maxlen=MAX_LOG_SIZE)
        # Use locks for thread safety, as both the main app and backend might access this
        self._logs_lock = threading.Lock()
        self._agent_logs_lock = threading.Lock()

    def add_log(self, log: LLMInteractionLog) -> None:
        """Adds a log entry, ensuring thread safety."""
        with self._logs_lock:
            self._logs.append(log)

    def get_logs(
        self,
        agent_name: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[LLMInteractionLog]:
        """Retrieves logs with optional filtering, ensuring thread safety."""
        with self._logs_lock:
            # Convert deque to list for easier filtering
            logs = list(self._logs)

        # Apply filters
        if agent_name:
            logs = [log for log in logs if log.agent_name == agent_name]
        if run_id:
            logs = [log for log in logs if log.run_id == run_id]

        # Apply limit (retrieve the most recent 'limit' logs after filtering)
        if limit is not None and limit > 0:
            logs = logs[-limit:]
        elif limit == 0:
            return []  # Return empty list if limit is 0

        return logs

    def add_agent_log(self, log: AgentExecutionLog) -> None:
        """添加Agent执行日志，确保线程安全"""
        with self._agent_logs_lock:
            self._agent_logs.append(log)

    def get_agent_logs(
        self,
        agent_name: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[AgentExecutionLog]:
        """获取Agent执行日志，可选过滤，确保线程安全"""
        with self._agent_logs_lock:
            # 转换为列表便于过滤
            logs = list(self._agent_logs)

        # 应用过滤器
        if agent_name:
            logs = [log for log in logs if log.agent_name == agent_name]
        if run_id:
            logs = [log for log in logs if log.run_id == run_id]

        # 应用限制（获取过滤后的最近'limit'条日志）
        if limit is not None and limit > 0:
            logs = logs[-limit:]
        elif limit == 0:
            return []  # 如果limit为0，返回空列表

        return logs

    def get_unique_run_ids(self) -> List[str]:
        """获取所有唯一的运行ID列表"""
        run_ids = set()

        # 从LLM交互日志中收集
        with self._logs_lock:
            for log in self._logs:
                if log.run_id:
                    run_ids.add(log.run_id)

        # 从Agent执行日志中收集
        with self._agent_logs_lock:
            for log in self._agent_logs:
                if log.run_id:
                    run_ids.add(log.run_id)

        # 按时间顺序返回（这里简化为字母顺序）
        return sorted(list(run_ids))
