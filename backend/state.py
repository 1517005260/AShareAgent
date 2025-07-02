"""
API状态管理模块

此模块提供全局API状态管理功能，用于跟踪Agent状态、运行历史等
"""

import threading
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, UTC
from concurrent.futures import ThreadPoolExecutor, Future

from .models.api_models import RunInfo

logger = logging.getLogger("api_state")


class ApiState:
    """API状态管理类，存储全局共享状态"""

    def __init__(self):
        self._lock = threading.RLock()
        self._agent_data: Dict[str, Dict] = {}
        self._runs: Dict[str, RunInfo] = {}
        self._current_run_id: Optional[str] = None
        self._executor = ThreadPoolExecutor(max_workers=5)
        self._analysis_tasks: Dict[str, Future] = {}  # 跟踪分析任务

    @property
    def current_run_id(self) -> Optional[str]:
        """获取当前运行ID"""
        with self._lock:
            return self._current_run_id

    @current_run_id.setter
    def current_run_id(self, run_id: str):
        """设置当前运行ID"""
        with self._lock:
            self._current_run_id = run_id

    def register_agent(self, agent_name: str, description: str = ""):
        """注册一个Agent"""
        with self._lock:
            if agent_name not in self._agent_data:
                self._agent_data[agent_name] = {
                    "info": {
                        "name": agent_name,
                        "description": description,
                        "state": "idle",
                        "last_run": None
                    },
                    "latest": {
                        "input_state": None,
                        "output_state": None,
                        "llm_request": None,
                        "llm_response": None,
                        "reasoning": None,
                        "timestamp": None
                    },
                    "history": []  # 保存历史执行记录
                }

    def update_agent_state(self, agent_name: str, state: str):
        """更新Agent状态"""
        with self._lock:
            if agent_name in self._agent_data:
                self._agent_data[agent_name]["info"]["state"] = state
                if state in ["completed", "error"]:
                    self._agent_data[agent_name]["info"]["last_run"] = datetime.now(
                        UTC)

    def update_agent_data(self, agent_name: str, field: str, data: Any):
        """更新Agent数据"""
        with self._lock:
            if agent_name in self._agent_data:
                self._agent_data[agent_name]["latest"][field] = data
                self._agent_data[agent_name]["latest"]["timestamp"] = datetime.now(
                    UTC)

                # 添加到历史记录
                if self._current_run_id:
                    history_entry = {
                        "run_id": self._current_run_id,
                        "timestamp": datetime.now(UTC),
                        field: data
                    }
                    self._agent_data[agent_name]["history"].append(
                        history_entry)

    def get_agent_info(self, agent_name: str) -> Optional[Dict]:
        """获取Agent信息"""
        with self._lock:
            if agent_name in self._agent_data:
                return self._agent_data[agent_name]["info"]
            return None

    def get_agent_data(self, agent_name: str, field: str = None) -> Optional[Dict]:
        """获取Agent数据"""
        with self._lock:
            if agent_name in self._agent_data:
                if field:
                    return self._agent_data[agent_name]["latest"].get(field)
                return self._agent_data[agent_name]["latest"]
            return None

    def get_all_agents(self) -> List[Dict]:
        """获取所有Agent信息"""
        with self._lock:
            return [data["info"] for data in self._agent_data.values()]

    def register_run(self, run_id: str):
        """注册新的运行"""
        with self._lock:
            self._runs[run_id] = RunInfo(
                run_id=run_id,
                start_time=datetime.now(UTC),
                status="running"
            )
            self._current_run_id = run_id

    def complete_run(self, run_id: str, status: str = "completed"):
        """完成运行"""
        with self._lock:
            if run_id in self._runs:
                self._runs[run_id].end_time = datetime.now(UTC)
                self._runs[run_id].status = status

                # 更新参与的Agent列表
                agents = set()
                for agent_name, agent_data in self._agent_data.items():
                    for entry in agent_data["history"]:
                        if entry["run_id"] == run_id:
                            agents.add(agent_name)
                            break

                self._runs[run_id].agents = list(agents)

    def get_run(self, run_id: str) -> Optional[RunInfo]:
        """获取运行信息"""
        with self._lock:
            return self._runs.get(run_id)

    def get_all_runs(self) -> List[RunInfo]:
        """获取所有运行信息"""
        with self._lock:
            return list(self._runs.values())

    def register_analysis_task(self, run_id: str, future: Future):
        """注册分析任务"""
        with self._lock:
            self._analysis_tasks[run_id] = future

    def get_analysis_task(self, run_id: str) -> Optional[Future]:
        """获取分析任务"""
        with self._lock:
            return self._analysis_tasks.get(run_id)


# 创建全局API状态实例
api_state = ApiState()
