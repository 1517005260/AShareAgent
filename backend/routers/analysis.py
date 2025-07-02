"""
股票分析相关路由模块

此模块提供与股票分析任务相关的API端点，集成用户认证和权限管理
"""

from fastapi import APIRouter, Depends, HTTPException, status
import uuid
import logging
import json
from datetime import datetime, UTC
from typing import Dict, List

from backend.models.api_models import (
    ApiResponse, StockAnalysisRequest, StockAnalysisResponse
)
from backend.models.auth_models import UserInDB
from backend.services.auth_service import get_current_active_user, require_permission
from backend.dependencies import get_database_manager
from backend.state import api_state
from backend.services import execute_stock_analysis
from backend.utils.api_utils import serialize_for_api, safe_parse_json
from src.database.models import DatabaseManager

logger = logging.getLogger("analysis_router")


def execute_stock_analysis_with_user(request, run_id: str, user_id: int, db_manager: DatabaseManager):
    """执行股票分析，支持用户关联和数据库记录"""
    try:
        # 调用原始分析函数
        result = execute_stock_analysis(request, run_id)
        
        # 更新任务状态为完成
        update_query = """
        UPDATE user_analysis_tasks 
        SET status = ?, completed_at = ?, result = ? 
        WHERE task_id = ?
        """
        result_json = json.dumps(serialize_for_api(result)) if result else None
        
        with db_manager.get_connection() as conn:
            conn.execute(update_query, ("completed", datetime.now(), result_json, run_id))
            conn.commit()
        
        return result
        
    except Exception as e:
        logger.error(f"执行分析任务失败 {run_id}: {e}")
        
        # 更新任务状态为失败
        error_query = """
        UPDATE user_analysis_tasks 
        SET status = ?, completed_at = ?, error_message = ? 
        WHERE task_id = ?
        """
        with db_manager.get_connection() as conn:
            conn.execute(error_query, ("failed", datetime.now(), str(e), run_id))
            conn.commit()
        
        raise e


# 创建路由器
router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.post("/start", response_model=ApiResponse[StockAnalysisResponse])
async def start_stock_analysis(
    request: StockAnalysisRequest,
    current_user: UserInDB = Depends(require_permission("analysis:basic")),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
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
    try:
        # 生成唯一任务ID
        task_id = str(uuid.uuid4())
        
        # 保存任务到数据库
        query = """
        INSERT INTO user_analysis_tasks (user_id, task_id, ticker, task_type, status, parameters, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        parameters = {
            "show_reasoning": request.show_reasoning,
            "num_of_news": request.num_of_news,
            "initial_capital": request.initial_capital,
            "initial_position": request.initial_position
        }
        
        with db_manager.get_connection() as conn:
            conn.execute(query, (
                current_user.id,
                task_id,
                request.ticker,
                "analysis",
                "pending",
                json.dumps(parameters),
                datetime.now()
            ))
            conn.commit()
        
        # 更新任务状态为运行中
        update_query = "UPDATE user_analysis_tasks SET status = ?, started_at = ? WHERE task_id = ?"
        with db_manager.get_connection() as conn:
            conn.execute(update_query, ("running", datetime.now(), task_id))
            conn.commit()
        
        # 将任务提交到线程池
        future = api_state._executor.submit(
            execute_stock_analysis_with_user,
            request=request,
            run_id=task_id,
            user_id=current_user.id,
            db_manager=db_manager
        )

        # 注册任务
        api_state.register_analysis_task(task_id, future)

        # 注册运行
        api_state.register_run(task_id)

        # 创建响应对象
        response = StockAnalysisResponse(
            run_id=task_id,
            ticker=request.ticker,
            status="running",
            message="分析任务已启动",
            submitted_at=datetime.now(UTC)
        )
        
    except Exception as e:
        logger.error(f"启动分析任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动分析任务失败: {str(e)}"
        )

    # 使用ApiResponse包装返回
    return ApiResponse(
        success=True,
        message="分析任务已成功启动",
        data=response
    )


@router.get("/history", response_model=ApiResponse[Dict])
async def get_user_analysis_history(
    skip: int = 0,
    limit: int = 20,
    status: str = None,
    ticker: str = None,
    current_user: UserInDB = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """获取用户的分析历史记录"""
    try:
        # 构建查询条件
        where_conditions = ["user_id = ?"]
        params = [current_user.id]
        
        if status:
            where_conditions.append("status = ?")
            params.append(status)
        
        if ticker:
            where_conditions.append("ticker = ?")
            params.append(ticker)
        
        where_clause = " AND ".join(where_conditions)
        
        # 获取总数
        count_query = f"SELECT COUNT(*) as total FROM user_analysis_tasks WHERE {where_clause}"
        count_result = db_manager.execute_query(count_query, params)
        total = count_result[0]["total"] if count_result else 0
        
        # 获取分页数据
        query = f"""
        SELECT task_id, ticker, task_type, status, parameters, 
               created_at, started_at, completed_at, error_message
        FROM user_analysis_tasks 
        WHERE {where_clause}
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
        """
        params.extend([limit, skip])
        
        tasks = db_manager.execute_query(query, params)
        
        # 转换参数JSON字符串为对象
        task_list = []
        for task in tasks:
            task_dict = dict(task)
            if task_dict["parameters"]:
                try:
                    task_dict["parameters"] = json.loads(task_dict["parameters"])
                except json.JSONDecodeError:
                    task_dict["parameters"] = {}
            task_list.append(task_dict)
        
        return ApiResponse(
            success=True,
            message="获取分析历史成功",
            data={
                "tasks": task_list,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
        
    except Exception as e:
        logger.error(f"获取分析历史失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取分析历史失败: {str(e)}",
            data=None
        )


@router.get("/{run_id}/status", response_model=ApiResponse[Dict])
async def get_analysis_status(
    run_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """获取股票分析任务的状态"""
    try:
        # 从数据库获取任务信息
        query = """
        SELECT * FROM user_analysis_tasks 
        WHERE task_id = ? AND user_id = ?
        """
        result = db_manager.execute_query(query, (run_id, current_user.id))
        
        if not result:
            return ApiResponse(
                success=False,
                message=f"分析任务 '{run_id}' 不存在或无权限访问",
                data=None
            )
        
        task_data = dict(result[0])
        
        # 获取内存中的任务状态
        task = api_state.get_analysis_task(run_id)
        run_info = api_state.get_run(run_id)
        
        status_data = {
            "task_id": task_data["task_id"],
            "ticker": task_data["ticker"],
            "status": task_data["status"],
            "created_at": task_data["created_at"],
            "started_at": task_data["started_at"],
            "completed_at": task_data["completed_at"],
            "error_message": task_data["error_message"]
        }
        
        # 如果任务还在内存中运行，获取实时状态
        if task and not task.done():
            status_data["is_running"] = True
        elif task and task.done():
            status_data["is_running"] = False
            if task.exception():
                status_data["runtime_error"] = str(task.exception())
        
        return ApiResponse(
            success=True,
            message="获取任务状态成功",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取任务状态失败: {str(e)}",
            data=None
        )


@router.get("/{run_id}/result", response_model=ApiResponse[Dict])
async def get_analysis_result(
    run_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """获取股票分析任务的结果数据

    此接口返回最终的投资决策结果以及各个Agent的分析数据摘要。
    分析必须已经完成才能获取结果。
    """
    try:
        # 从数据库获取任务信息，确保用户权限
        query = """
        SELECT * FROM user_analysis_tasks 
        WHERE task_id = ? AND user_id = ?
        """
        result = db_manager.execute_query(query, (run_id, current_user.id))
        
        if not result:
            return ApiResponse(
                success=False,
                message=f"分析任务 '{run_id}' 不存在或无权限访问",
                data=None
            )
        
        task_data = dict(result[0])
        
        # 检查任务是否完成
        if task_data["status"] != "completed":
            return ApiResponse(
                success=False,
                message=f"分析任务尚未完成或已失败，当前状态: {task_data['status']}",
                data={"status": task_data["status"]}
            )
        
        # 从数据库获取保存的结果
        if task_data["result"]:
            try:
                stored_result = json.loads(task_data["result"])
                return ApiResponse(
                    success=True,
                    message="获取分析结果成功",
                    data={
                        "task_id": task_data["task_id"],
                        "ticker": task_data["ticker"],
                        "completion_time": task_data["completed_at"],
                        "result": stored_result
                    }
                )
            except json.JSONDecodeError:
                logger.error(f"解析存储的分析结果失败: {run_id}")
        
        # 如果数据库中没有结果，尝试从内存获取
        task = api_state.get_analysis_task(run_id)
        run_info = api_state.get_run(run_id)
        
        if not run_info:
            return ApiResponse(
                success=False,
                message="分析结果不可用",
                data=None
            )
        
        # 收集所有参与此运行的Agent数据
        agent_results = {}
        ticker = task_data["ticker"]
        
        for agent_name in run_info.agents:
            agent_data = api_state.get_agent_data(agent_name)
            if agent_data and "reasoning" in agent_data:
                reasoning_data = safe_parse_json(agent_data["reasoning"])
                agent_results[agent_name] = serialize_for_api(reasoning_data)

        # 尝试获取portfolio_management的最终决策
        final_decision = None
        portfolio_data = api_state.get_agent_data("portfolio_management")
        if portfolio_data and "output_state" in portfolio_data:
            try:
                output = portfolio_data["output_state"]
                messages = output.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, "content"):
                        final_decision = safe_parse_json(last_message.content)
            except Exception as e:
                logger.error(f"解析最终决策时出错: {str(e)}")

        result_data = {
            "task_id": run_id,
            "ticker": ticker,
            "completion_time": task_data["completed_at"],
            "final_decision": serialize_for_api(final_decision),
            "agent_results": agent_results
        }

        return ApiResponse(
            success=True,
            message="获取分析结果成功",
            data=result_data
        )
        
    except Exception as e:
        logger.error(f"获取分析结果时出错: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"获取分析结果时出错: {str(e)}",
            data={"error": str(e)}
        )


@router.delete("/{task_id}", response_model=ApiResponse[bool])
async def delete_analysis_task(
    task_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """删除分析任务记录（仅限已完成或失败的任务）"""
    try:
        # 检查任务是否存在且属于当前用户
        check_query = """
        SELECT status FROM user_analysis_tasks 
        WHERE task_id = ? AND user_id = ?
        """
        result = db_manager.execute_query(check_query, (task_id, current_user.id))
        
        if not result:
            return ApiResponse(
                success=False,
                message="任务不存在或无权限删除",
                data=False
            )
        
        task_status = result[0]["status"]
        
        # 只允许删除已完成或失败的任务
        if task_status in ["running", "pending"]:
            return ApiResponse(
                success=False,
                message="无法删除正在运行或待处理的任务",
                data=False
            )
        
        # 删除任务记录
        delete_query = "DELETE FROM user_analysis_tasks WHERE task_id = ? AND user_id = ?"
        with db_manager.get_connection() as conn:
            cursor = conn.execute(delete_query, (task_id, current_user.id))
            conn.commit()
            
            if cursor.rowcount > 0:
                return ApiResponse(
                    success=True,
                    message="任务删除成功",
                    data=True
                )
            else:
                return ApiResponse(
                    success=False,
                    message="删除任务失败",
                    data=False
                )
                
    except Exception as e:
        logger.error(f"删除分析任务失败: {e}")
        return ApiResponse(
            success=False,
            message=f"删除任务失败: {str(e)}",
            data=False
        )
