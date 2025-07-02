"""
回测相关路由模块

此模块提供与回测任务相关的API端点，集成用户认证和权限管理
"""

from fastapi import APIRouter, Depends, HTTPException, status
import logging
from typing import Dict

from backend.models.api_models import (
    ApiResponse, BacktestRequest, BacktestResponse, BacktestResultData
)
from backend.models.auth_models import UserInDB
from backend.services.auth_service import get_current_active_user, require_permission
from backend.services.backtest_service import BacktestService
from backend.dependencies import get_database_manager
from src.database.models import DatabaseManager

logger = logging.getLogger("backtest_router")

# 创建路由器
router = APIRouter(prefix="/api/backtest", tags=["Backtest"])


@router.post("/start", response_model=ApiResponse[BacktestResponse])
async def start_backtest(
    request: BacktestRequest,
    current_user: UserInDB = Depends(require_permission("backtest:basic")),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """开始回测任务

    此API端点允许前端触发新的回测任务。回测将在后台进行，
    前端可通过返回的run_id查询回测状态和结果。

    参数说明:
    - ticker: 股票代码，如"002848"（必填）
    - start_date: 回测开始日期，格式YYYY-MM-DD（必填）
    - end_date: 回测结束日期，格式YYYY-MM-DD（必填）
    - initial_capital: 初始资金，默认为100000
    - num_of_news: 用于情感分析的新闻数量(1-100)，默认为5
    - agent_frequencies: 各Agent的执行频率配置，可选

    示例请求:
    ```json
    {
        "ticker": "002848",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 100000.0,
        "num_of_news": 5,
        "agent_frequencies": {
            "market_data": "daily",
            "technical": "daily",
            "fundamentals": "weekly",
            "sentiment": "daily",
            "valuation": "monthly",
            "macro": "weekly",
            "portfolio": "daily"
        }
    }
    ```

    简化请求(仅提供必填参数):
    ```json
    {
        "ticker": "002848",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
    ```
    """
    try:
        backtest_service = BacktestService(db_manager)
        response = await backtest_service.start_backtest(request, current_user)
        
        return ApiResponse(
            success=True,
            message="回测任务已成功启动",
            data=response
        )
        
    except Exception as e:
        logger.error(f"启动回测任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动回测任务失败: {str(e)}"
        )


@router.get("/history", response_model=ApiResponse[Dict])
async def get_backtest_history(
    skip: int = 0,
    limit: int = 20,
    status: str = None,
    ticker: str = None,
    current_user: UserInDB = Depends(require_permission("backtest:history")),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """获取用户的回测历史记录"""
    try:
        backtest_service = BacktestService(db_manager)
        result = await backtest_service.get_backtest_history(
            current_user, skip, limit, status, ticker
        )
        
        return ApiResponse(
            success=True,
            message="获取回测历史成功",
            data=result
        )
        
    except Exception as e:
        logger.error(f"获取回测历史失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取回测历史失败: {str(e)}",
            data=None
        )


@router.get("/{run_id}/status", response_model=ApiResponse[Dict])
async def get_backtest_status(
    run_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """获取回测任务的状态"""
    try:
        backtest_service = BacktestService(db_manager)
        status_data = await backtest_service.get_backtest_status(run_id, current_user)
        
        return ApiResponse(
            success=True,
            message="获取任务状态成功",
            data=status_data
        )
        
    except ValueError as e:
        return ApiResponse(
            success=False,
            message=str(e),
            data=None
        )
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取任务状态失败: {str(e)}",
            data=None
        )


@router.get("/{run_id}/result", response_model=ApiResponse[Dict])
async def get_backtest_result(
    run_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """获取回测任务的结果数据

    此接口返回最终的回测结果，包括性能指标、风险指标、交易记录等。
    回测必须已经完成才能获取结果。
    """
    try:
        backtest_service = BacktestService(db_manager)
        result_data = await backtest_service.get_backtest_result(run_id, current_user)
        
        return ApiResponse(
            success=True,
            message="获取回测结果成功",
            data=result_data
        )
        
    except ValueError as e:
        return ApiResponse(
            success=False,
            message=str(e),
            data=None
        )
    except Exception as e:
        logger.error(f"获取回测结果时出错: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"获取回测结果时出错: {str(e)}",
            data={"error": str(e)}
        )


@router.delete("/{task_id}", response_model=ApiResponse[bool])
async def delete_backtest_task(
    task_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """删除回测任务记录（仅限已完成或失败的任务）"""
    try:
        backtest_service = BacktestService(db_manager)
        success = await backtest_service.delete_backtest_task(task_id, current_user)
        
        return ApiResponse(
            success=success,
            message="任务删除成功" if success else "任务删除失败",
            data=success
        )
        
    except ValueError as e:
        return ApiResponse(
            success=False,
            message=str(e),
            data=False
        )
    except Exception as e:
        logger.error(f"删除回测任务失败: {e}")
        return ApiResponse(
            success=False,
            message=f"删除任务失败: {str(e)}",
            data=False
        )