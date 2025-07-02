"""
投资组合管理API路由
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from backend.models.api_models import ApiResponse
from backend.models.auth_models import UserInDB
from backend.models.portfolio_models import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse, PortfolioService,
    TransactionCreate, TransactionResponse, HoldingResponse, PortfolioSummary
)
from backend.services.auth_service import get_current_active_user, require_permission
from backend.dependencies import get_database_manager
from src.database.models import DatabaseManager
import logging

logger = logging.getLogger("portfolio_router")

# 创建路由器
router = APIRouter(prefix="/api/portfolios", tags=["投资组合管理"])


def get_portfolio_service(db_manager: DatabaseManager = Depends(get_database_manager)) -> PortfolioService:
    """获取投资组合服务实例"""
    return PortfolioService(db_manager)


@router.post("/", response_model=ApiResponse[PortfolioResponse])
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user: UserInDB = Depends(require_permission("portfolio:create")),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """
    创建投资组合
    
    - **name**: 组合名称（必填，至少2个字符）
    - **description**: 组合描述（可选）
    - **initial_capital**: 初始资金（必填，大于0）
    """
    try:
        # 检查用户组合数量限制
        existing_portfolios = portfolio_service.list_user_portfolios(current_user.id)
        max_portfolios = 10  # 可以从系统配置读取
        
        if len(existing_portfolios) >= max_portfolios:
            return ApiResponse(
                success=False,
                message=f"每个用户最多只能创建{max_portfolios}个投资组合",
                data=None
            )
        
        # 检查组合名称是否重复
        for portfolio in existing_portfolios:
            if portfolio.name == portfolio_data.name:
                return ApiResponse(
                    success=False,
                    message="组合名称已存在，请使用其他名称",
                    data=None
                )
        
        portfolio = portfolio_service.create_portfolio(current_user.id, portfolio_data)
        
        return ApiResponse(
            success=True,
            message="投资组合创建成功",
            data=portfolio
        )
        
    except Exception as e:
        logger.error(f"创建投资组合失败: {e}")
        return ApiResponse(
            success=False,
            message=f"创建投资组合失败: {str(e)}",
            data=None
        )


@router.get("/", response_model=ApiResponse[List[PortfolioResponse]])
async def list_portfolios(
    current_user: UserInDB = Depends(require_permission("portfolio:read")),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """获取用户的投资组合列表"""
    try:
        portfolios = portfolio_service.list_user_portfolios(current_user.id)
        
        return ApiResponse(
            success=True,
            message="获取投资组合列表成功",
            data=portfolios
        )
        
    except Exception as e:
        logger.error(f"获取投资组合列表失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取投资组合列表失败: {str(e)}",
            data=[]
        )


@router.get("/{portfolio_id}", response_model=ApiResponse[PortfolioResponse])
async def get_portfolio(
    portfolio_id: int,
    current_user: UserInDB = Depends(require_permission("portfolio:read")),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """根据ID获取投资组合详情"""
    try:
        portfolio = portfolio_service.get_portfolio_by_id(current_user.id, portfolio_id)
        
        if not portfolio:
            return ApiResponse(
                success=False,
                message="投资组合不存在或无权限访问",
                data=None
            )
        
        return ApiResponse(
            success=True,
            message="获取投资组合详情成功",
            data=portfolio
        )
        
    except Exception as e:
        logger.error(f"获取投资组合详情失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取投资组合详情失败: {str(e)}",
            data=None
        )


@router.put("/{portfolio_id}", response_model=ApiResponse[PortfolioResponse])
async def update_portfolio(
    portfolio_id: int,
    update_data: PortfolioUpdate,
    current_user: UserInDB = Depends(require_permission("portfolio:update")),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """更新投资组合信息"""
    try:
        # 如果更新名称，检查是否重复
        if update_data.name:
            existing_portfolios = portfolio_service.list_user_portfolios(current_user.id)
            for portfolio in existing_portfolios:
                if portfolio.name == update_data.name and portfolio.id != portfolio_id:
                    return ApiResponse(
                        success=False,
                        message="组合名称已存在，请使用其他名称",
                        data=None
                    )
        
        updated_portfolio = portfolio_service.update_portfolio(current_user.id, portfolio_id, update_data)
        
        if not updated_portfolio:
            return ApiResponse(
                success=False,
                message="投资组合不存在或无权限访问",
                data=None
            )
        
        return ApiResponse(
            success=True,
            message="投资组合更新成功",
            data=updated_portfolio
        )
        
    except Exception as e:
        logger.error(f"更新投资组合失败: {e}")
        return ApiResponse(
            success=False,
            message=f"更新投资组合失败: {str(e)}",
            data=None
        )


@router.delete("/{portfolio_id}", response_model=ApiResponse[bool])
async def delete_portfolio(
    portfolio_id: int,
    current_user: UserInDB = Depends(require_permission("portfolio:delete")),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """删除投资组合（软删除）"""
    try:
        # 将组合设置为非活跃状态
        update_data = PortfolioUpdate(is_active=False)
        updated_portfolio = portfolio_service.update_portfolio(current_user.id, portfolio_id, update_data)
        
        if not updated_portfolio:
            return ApiResponse(
                success=False,
                message="投资组合不存在或无权限访问",
                data=False
            )
        
        return ApiResponse(
            success=True,
            message="投资组合删除成功",
            data=True
        )
        
    except Exception as e:
        logger.error(f"删除投资组合失败: {e}")
        return ApiResponse(
            success=False,
            message=f"删除投资组合失败: {str(e)}",
            data=False
        )


@router.get("/{portfolio_id}/summary", response_model=ApiResponse[PortfolioSummary])
async def get_portfolio_summary(
    portfolio_id: int,
    current_user: UserInDB = Depends(require_permission("portfolio:read")),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """获取投资组合摘要信息"""
    try:
        summary = portfolio_service.get_portfolio_summary(current_user.id, portfolio_id)
        
        if not summary:
            return ApiResponse(
                success=False,
                message="投资组合不存在或无权限访问",
                data=None
            )
        
        return ApiResponse(
            success=True,
            message="获取投资组合摘要成功",
            data=summary
        )
        
    except Exception as e:
        logger.error(f"获取投资组合摘要失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取投资组合摘要失败: {str(e)}",
            data=None
        )


@router.get("/{portfolio_id}/holdings", response_model=ApiResponse[List[HoldingResponse]])
async def get_portfolio_holdings(
    portfolio_id: int,
    current_user: UserInDB = Depends(require_permission("portfolio:read")),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """获取投资组合持仓列表"""
    try:
        holdings = portfolio_service.get_portfolio_holdings(current_user.id, portfolio_id)
        
        return ApiResponse(
            success=True,
            message="获取持仓列表成功",
            data=holdings
        )
        
    except Exception as e:
        logger.error(f"获取持仓列表失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取持仓列表失败: {str(e)}",
            data=[]
        )


@router.post("/{portfolio_id}/transactions", response_model=ApiResponse[TransactionResponse])
async def add_transaction(
    portfolio_id: int,
    transaction_data: TransactionCreate,
    current_user: UserInDB = Depends(require_permission("portfolio:update")),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """
    添加交易记录
    
    - **ticker**: 股票代码（必填）
    - **transaction_type**: 交易类型，buy或sell（必填）
    - **quantity**: 交易数量（必填，大于0）
    - **price**: 交易价格（必填，大于0）
    - **commission**: 手续费（可选，默认0）
    - **notes**: 备注（可选）
    """
    try:
        transaction = portfolio_service.add_transaction(current_user.id, portfolio_id, transaction_data)
        
        return ApiResponse(
            success=True,
            message="交易记录添加成功",
            data=transaction
        )
        
    except ValueError as e:
        return ApiResponse(
            success=False,
            message=str(e),
            data=None
        )
    except Exception as e:
        logger.error(f"添加交易记录失败: {e}")
        return ApiResponse(
            success=False,
            message=f"添加交易记录失败: {str(e)}",
            data=None
        )


@router.get("/{portfolio_id}/transactions", response_model=ApiResponse[List[TransactionResponse]])
async def get_portfolio_transactions(
    portfolio_id: int,
    limit: int = Query(50, description="返回记录数量限制", ge=1, le=200),
    offset: int = Query(0, description="跳过记录数量", ge=0),
    current_user: UserInDB = Depends(require_permission("portfolio:read")),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """获取投资组合交易记录"""
    try:
        transactions = portfolio_service.get_portfolio_transactions(
            current_user.id, portfolio_id, limit, offset
        )
        
        return ApiResponse(
            success=True,
            message="获取交易记录成功",
            data=transactions
        )
        
    except Exception as e:
        logger.error(f"获取交易记录失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取交易记录失败: {str(e)}",
            data=[]
        )


@router.get("/stats/overview", response_model=ApiResponse[Dict[str, Any]])
async def get_user_portfolio_stats(
    current_user: UserInDB = Depends(require_permission("portfolio:read")),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    """获取用户投资组合统计概览"""
    try:
        portfolios = portfolio_service.list_user_portfolios(current_user.id)
        
        total_portfolios = len(portfolios)
        total_initial_capital = sum(p.initial_capital for p in portfolios)
        total_current_value = sum(p.current_value or 0 for p in portfolios)
        total_cash_balance = sum(p.cash_balance or 0 for p in portfolios)
        total_return = total_current_value - total_initial_capital
        total_return_rate = (total_return / total_initial_capital * 100) if total_initial_capital > 0 else 0
        
        # 获取所有持仓统计
        total_positions = 0
        for portfolio in portfolios:
            holdings = portfolio_service.get_portfolio_holdings(current_user.id, portfolio.id)
            total_positions += len(holdings)
        
        stats = {
            "total_portfolios": total_portfolios,
            "total_initial_capital": total_initial_capital,
            "total_current_value": total_current_value,
            "total_cash_balance": total_cash_balance,
            "total_return": total_return,
            "total_return_rate": total_return_rate,
            "total_positions": total_positions,
            "active_portfolios": sum(1 for p in portfolios if p.is_active)
        }
        
        return ApiResponse(
            success=True,
            message="获取投资组合统计成功",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"获取投资组合统计失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取投资组合统计失败: {str(e)}",
            data={}
        )