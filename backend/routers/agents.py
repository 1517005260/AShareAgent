"""
Agent相关路由模块

此模块提供与Agent状态、信息和数据相关的API端点
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from ..models.api_models import (
    ApiResponse, AgentInfo, AgentCreateRequest, AgentUpdateRequest, 
    AgentDecisionInfo, DecisionDisplayRequest
)
from ..state import api_state
from ..utils.api_utils import serialize_for_api
from ..utils.decision_formatter import format_decision_display
from src.database.models import DatabaseManager, AgentModel, AgentDecisionModel

logger = logging.getLogger("agents_router")

# 创建路由器
router = APIRouter(prefix="/api/agents", tags=["Agents"])

# 初始化数据库管理器
db_manager = DatabaseManager()
agent_model = AgentModel(db_manager)
decision_model = AgentDecisionModel(db_manager)


@router.get("/", response_model=List[AgentInfo])
async def list_agents():
    """获取所有Agent列表"""
    agents = api_state.get_all_agents()
    return agents


# Agent管理相关API (必须在参数化路由之前定义)
@router.get("/manage", response_model=ApiResponse[List[Dict]])
async def get_managed_agents():
    """获取管理的Agent列表"""
    try:
        agents = agent_model.get_all_agents()
        return ApiResponse(
            success=True,
            message="获取Agent列表成功",
            data=agents
        )
    except Exception as e:
        logger.error(f"获取Agent列表时出错: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"获取Agent列表时出错: {str(e)}",
            data=[]
        )


# Agent决策记录相关API (必须在参数化路由之前定义)
@router.get("/decisions", response_model=ApiResponse[List[Dict]])
async def get_decisions(
    run_id: str = None,
    agent_name: str = None,
    ticker: str = None,
    limit: int = 50
):
    """获取Agent决策记录"""
    try:
        if run_id:
            decisions = decision_model.get_decisions_by_run(run_id)
        elif agent_name:
            decisions = decision_model.get_decisions_by_agent(agent_name, limit)
        elif ticker:
            decisions = decision_model.get_decisions_by_ticker(ticker, limit)
        else:
            decisions = decision_model.get_recent_decisions(limit)
        
        return ApiResponse(
            success=True,
            message="获取决策记录成功",
            data=decisions
        )
    except Exception as e:
        logger.error(f"获取决策记录时出错: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"获取决策记录时出错: {str(e)}",
            data=[]
        )


@router.get("/decisions/{run_id}/formatted", response_model=ApiResponse[str])
async def get_formatted_decision(run_id: str):
    """获取格式化的决策显示"""
    try:
        decisions = decision_model.get_decisions_by_run(run_id)
        if not decisions:
            return ApiResponse(
                success=False,
                message="未找到该运行的决策记录",
                data=""
            )
        
        # 使用专门的格式化工具
        ticker = decisions[0].get('ticker') if decisions else None
        formatted_text = format_decision_display(decisions, ticker)
        
        return ApiResponse(
            success=True,
            message="获取格式化决策成功",
            data=formatted_text
        )
    except Exception as e:
        logger.error(f"获取格式化决策时出错: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"获取格式化决策时出错: {str(e)}",
            data=""
        )


# 参数化路由必须在最后
@router.get("/{agent_name}", response_model=ApiResponse[Dict])
async def get_agent_info(agent_name: str):
    """获取指定Agent的信息"""
    info = api_state.get_agent_info(agent_name)
    if not info:
        return ApiResponse(
            success=False,
            message=f"Agent '{agent_name}' 不存在",
            data=None
        )
    return ApiResponse(data=info)


@router.get("/{agent_name}/latest_input", response_model=ApiResponse[Dict])
async def get_latest_input(agent_name: str):
    """获取Agent的最新输入状态"""
    data = api_state.get_agent_data(agent_name, "input_state")
    return ApiResponse(data=serialize_for_api(data))


@router.get("/{agent_name}/latest_output", response_model=ApiResponse[Dict])
async def get_latest_output(agent_name: str):
    """获取Agent的最新输出状态"""
    data = api_state.get_agent_data(agent_name, "output_state")
    return ApiResponse(data=serialize_for_api(data))


@router.get("/{agent_name}/reasoning", response_model=ApiResponse[Dict])
async def get_reasoning(agent_name: str):
    """获取Agent的推理详情"""
    try:
        # 获取数据
        data = api_state.get_agent_data(agent_name, "reasoning")

        # 如果数据不存在
        if data is None:
            return ApiResponse(
                success=False,
                message=f"没有找到{agent_name}的推理记录",
                data={"message": f"Agent {agent_name} 没有推理数据"}
            )

        # 尝试解析和序列化数据
        serialized_data = serialize_for_api(data)

        # 确保结果是字典类型
        if not isinstance(serialized_data, dict):
            # 如果不是字典，包装为字典返回
            return ApiResponse(
                data={"content": serialized_data, "type": "raw_content"}
            )

        return ApiResponse(data=serialized_data)
    except Exception as e:
        # 记录错误并返回友好的错误信息
        logger.error(f"序列化{agent_name}的推理数据时出错: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"无法处理{agent_name}的推理数据: {str(e)}",
            data={"error": str(e), "original_type": str(type(data))}
        )


@router.get("/{agent_name}/latest_llm_request", response_model=ApiResponse[Dict])
async def get_latest_llm_request(agent_name: str):
    """获取Agent的最新LLM请求"""
    try:
        data = api_state.get_agent_data(agent_name, "llm_request")

        # 确保返回有意义的数据
        if data is None:
            return ApiResponse(
                success=True,
                message=f"没有找到{agent_name}的LLM请求记录",
                data={"message": f"没有找到{agent_name}的LLM请求记录"}
            )

        # 尝试解析和序列化数据
        serialized_data = serialize_for_api(data)

        # 确保结果是字典类型
        if not isinstance(serialized_data, dict):
            # 如果不是字典，包装为字典返回
            serialized_data = {
                "content": serialized_data, "type": "raw_content"}

        return ApiResponse(data=serialized_data)
    except Exception as e:
        logger.error(f"处理{agent_name}的LLM请求数据时出错: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"无法处理{agent_name}的LLM请求数据: {str(e)}",
            data={"error": str(e)}
        )


@router.get("/{agent_name}/latest_llm_response", response_model=ApiResponse[Dict])
async def get_latest_llm_response(agent_name: str):
    """获取Agent的最新LLM响应"""
    try:
        data = api_state.get_agent_data(agent_name, "llm_response")

        # 确保返回有意义的数据
        if data is None:
            return ApiResponse(
                success=True,
                message=f"没有找到{agent_name}的LLM响应记录",
                data={"message": f"没有找到{agent_name}的LLM响应记录"}
            )

        # 尝试解析和序列化数据
        serialized_data = serialize_for_api(data)

        # 确保结果是字典类型
        if not isinstance(serialized_data, dict):
            # 如果不是字典，包装为字典返回
            serialized_data = {
                "content": serialized_data, "type": "raw_content"}

        return ApiResponse(data=serialized_data)
    except Exception as e:
        logger.error(f"处理{agent_name}的LLM响应数据时出错: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"无法处理{agent_name}的LLM响应数据: {str(e)}",
            data={"error": str(e)}
        )


# Agent管理相关API (create endpoint)
@router.post("/manage", response_model=ApiResponse[Dict])
async def create_agent(request: AgentCreateRequest):
    """创建新的Agent"""
    try:
        success = agent_model.create_agent(
            name=request.name,
            display_name=request.display_name,
            description=request.description,
            agent_type=request.agent_type,
            status=request.status,
            config=request.config
        )
        
        if success:
            return ApiResponse(
                success=True,
                message=f"Agent '{request.name}' 创建成功",
                data={"name": request.name}
            )
        else:
            return ApiResponse(
                success=False,
                message=f"创建Agent失败",
                data=None
            )
    except Exception as e:
        logger.error(f"创建Agent时出错: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"创建Agent时出错: {str(e)}",
            data=None
        )


@router.put("/manage/{agent_name}", response_model=ApiResponse[Dict])
async def update_agent(agent_name: str, request: AgentUpdateRequest):
    """更新Agent信息"""
    try:
        agent = agent_model.get_agent_by_name(agent_name)
        if not agent:
            return ApiResponse(
                success=False,
                message=f"Agent '{agent_name}' 不存在",
                data=None
            )
        
        # 更新状态
        if request.status is not None:
            agent_model.update_agent_status(agent_name, request.status)
        
        # 更新配置
        if request.config is not None:
            agent_model.update_agent_config(agent_name, request.config)
        
        return ApiResponse(
            success=True,
            message=f"Agent '{agent_name}' 更新成功",
            data={"name": agent_name}
        )
    except Exception as e:
        logger.error(f"更新Agent时出错: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"更新Agent时出错: {str(e)}",
            data=None
        )


# 这部分已经移到前面了，删除重复的代码
