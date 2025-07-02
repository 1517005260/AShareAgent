"""
工作流相关路由模块

此模块提供与工作流状态、执行和管理相关的API端点
"""

from fastapi import APIRouter
from typing import Dict

from ..models.api_models import ApiResponse
from ..state import api_state

# 创建路由器
router = APIRouter(prefix="/api/workflow", tags=["Workflow"])


@router.get("/status", response_model=ApiResponse[Dict])
async def get_workflow_status():
    """获取当前正在运行的工作流状态 (基于内存状态)

    此接口查询内存中的 api_state 对象，返回当前正在执行的工作流的实时状态，
    包括运行ID、开始时间以及活跃Agent的状态。
    如果当前没有工作流在运行，则返回 'idle' 状态。
    注意：此状态信息仅反映当前情况，并在服务重启后丢失。
    """
    current_run_id = api_state.current_run_id
    if not current_run_id:
        return ApiResponse(
            data={
                "status": "idle",
                "message": "当前没有运行中的工作流"
            }
        )

    run = api_state.get_run(current_run_id)
    agents = api_state.get_all_agents()

    return ApiResponse(
        data={
            "status": run.status,
            "run_id": current_run_id,
            "start_time": run.start_time,
            "agents": [a for a in agents if a["state"] != "idle"]
        }
    )
