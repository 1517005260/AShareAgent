"""
股票分析相关路由模块

此模块提供与股票分析任务相关的API端点
"""

from fastapi import APIRouter
import uuid
import logging
from datetime import datetime, UTC
from typing import Dict

from ..models.api_models import (
    ApiResponse, StockAnalysisRequest, StockAnalysisResponse
)
from ..state import api_state
from ..services import execute_stock_analysis
from ..utils.api_utils import serialize_for_api, safe_parse_json

logger = logging.getLogger("analysis_router")

# 创建路由器
router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.post("/start", response_model=ApiResponse[StockAnalysisResponse])
async def start_stock_analysis(request: StockAnalysisRequest):
    """开始股票分析任务

    此API端点允许前端触发新的股票分析。分析将在后台进行，
    前端可通过返回的run_id查询分析状态和结果。

    参数说明:
    - ticker: 股票代码，如"002848"（必填）
    - show_reasoning: 是否显示分析推理过程，默认为true
    - num_of_news: 用于情感分析的新闻数量(1-100)，默认为5
    - initial_capital: 初始资金，默认为100000
    - initial_position: 初始持仓数量，默认为0

    分析日期说明:
    - 系统会自动使用最近一年的数据进行分析，无需手动指定日期范围

    示例请求:
    ```json
    {
        "ticker": "002848",
        "show_reasoning": true,
        "num_of_news": 5,
        "initial_capital": 100000.0,
        "initial_position": 0
    }
    ```

    简化请求(仅提供必填参数):
    ```json
    {
        "ticker": "002848"
    }
    ```
    """
    # 生成唯一ID
    run_id = str(uuid.uuid4())

    # 将任务提交到线程池
    future = api_state._executor.submit(
        execute_stock_analysis,
        request=request,
        run_id=run_id
    )

    # 注册任务
    api_state.register_analysis_task(run_id, future)

    # 注册运行
    api_state.register_run(run_id)

    # 创建响应对象
    response = StockAnalysisResponse(
        run_id=run_id,
        ticker=request.ticker,
        status="running",
        message="分析任务已启动",
        submitted_at=datetime.now(UTC)
    )

    # 使用ApiResponse包装返回
    return ApiResponse(
        success=True,
        message="分析任务已成功启动",
        data=response
    )


@router.get("/{run_id}/status", response_model=ApiResponse[Dict])
async def get_analysis_status(run_id: str):
    """获取股票分析任务的状态"""
    task = api_state.get_analysis_task(run_id)
    run_info = api_state.get_run(run_id)

    if not run_info:
        return ApiResponse(
            success=False,
            message=f"分析任务 '{run_id}' 不存在",
            data=None
        )

    status_data = {
        "run_id": run_id,
        "status": run_info.status,
        "start_time": run_info.start_time,
        "end_time": run_info.end_time,
    }

    if task:
        if task.done():
            if task.exception():
                status_data["error"] = str(task.exception())
            status_data["is_complete"] = True
        else:
            status_data["is_complete"] = False

    return ApiResponse(data=status_data)


@router.get("/{run_id}/result", response_model=ApiResponse[Dict])
async def get_analysis_result(run_id: str):
    """获取股票分析任务的结果数据

    此接口返回最终的投资决策结果以及各个Agent的分析数据摘要。
    分析必须已经完成才能获取结果。
    """
    try:
        task = api_state.get_analysis_task(run_id)
        run_info = api_state.get_run(run_id)

        if not run_info:
            return ApiResponse(
                success=False,
                message=f"分析任务 '{run_id}' 不存在",
                data=None
            )

        # 检查任务是否完成
        if run_info.status != "completed":
            return ApiResponse(
                success=False,
                message=f"分析任务尚未完成或已失败，当前状态: {run_info.status}",
                data={"status": run_info.status}
            )

        # 收集所有参与此运行的Agent数据
        agent_results = {}
        ticker = ""
        for agent_name in run_info.agents:
            agent_data = api_state.get_agent_data(agent_name)
            if agent_data and "reasoning" in agent_data:
                # 尝试解析和序列化推理数据
                reasoning_data = safe_parse_json(agent_data["reasoning"])
                agent_results[agent_name] = serialize_for_api(reasoning_data)

            # 尝试从market_data_agent获取ticker
            if agent_name == "market_data" and agent_data and "output_state" in agent_data:
                try:
                    output = agent_data["output_state"]
                    if "data" in output and "ticker" in output["data"]:
                        ticker = output["data"]["ticker"]
                except Exception:
                    pass

        # 尝试获取portfolio_management的最终决策
        final_decision = None
        portfolio_data = api_state.get_agent_data("portfolio_management")
        if portfolio_data and "output_state" in portfolio_data:
            try:
                output = portfolio_data["output_state"]
                messages = output.get("messages", [])
                # 获取最后一个消息
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, "content"):
                        # 尝试解析content，可能是JSON字符串
                        final_decision = safe_parse_json(last_message.content)
            except Exception as e:
                logger.error(f"解析最终决策时出错: {str(e)}")

        result_data = {
            "run_id": run_id,
            "ticker": ticker,
            "completion_time": run_info.end_time,
            "final_decision": serialize_for_api(final_decision),
            "agent_results": agent_results
        }

        return ApiResponse(data=result_data)
    except Exception as e:
        logger.error(f"获取分析结果时出错: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"获取分析结果时出错: {str(e)}",
            data={"error": str(e)}
        )
