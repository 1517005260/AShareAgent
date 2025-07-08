from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from tools.api import get_eastmoney_data, get_market_data
from backend.services.auth_service import get_current_active_user

router = APIRouter()

class StockPriceResponse(BaseModel):
    ticker: str
    current_price: float
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    updated_at: Optional[str] = None

@router.get("/price/{ticker}", response_model=Dict[str, Any])
async def get_stock_price(
    ticker: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    获取股票实时价格
    """
    try:
        # 使用改进的市场数据API（已经包含了多数据源回退逻辑）
        try:
            data = get_market_data(ticker)
            if data and data.get('current_price') and data['current_price'] > 0:
                return {
                    "success": True,
                    "data": {
                        "ticker": ticker,
                        "current_price": data['current_price'],
                        "change": data.get('change'),
                        "change_percent": data.get('change_percent'),
                        "volume": data.get('volume'),
                        "market_cap": data.get('market_cap'),
                        "updated_at": data.get('updated_at')
                    },
                    "message": "获取股票价格成功"
                }
        except Exception as e:
            print(f"市场数据API失败: {str(e)}")
        
        # 如果市场数据API也失败，直接尝试东方财富API
        try:
            data = get_eastmoney_data(ticker)
            if data and data.get('current_price') and data['current_price'] > 0:
                return {
                    "success": True,
                    "data": {
                        "ticker": ticker,
                        "current_price": data['current_price'],
                        "change": data.get('change'),
                        "change_percent": data.get('change_percent'),
                        "volume": data.get('volume'),
                        "market_cap": data.get('market_cap'),
                        "updated_at": data.get('updated_at')
                    },
                    "message": "获取股票价格成功"
                }
        except Exception as e:
            print(f"东方财富API失败: {str(e)}")
        
        # 如果都失败了，返回错误
        return {
            "success": False,
            "message": f"无法获取股票 {ticker} 的价格数据",
            "error": "所有数据源都不可用或返回无效价格"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "获取股票价格时发生错误",
            "error": str(e)
        }

@router.get("/info/{ticker}", response_model=Dict[str, Any])
async def get_stock_info(
    ticker: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    获取股票详细信息
    """
    try:
        data = get_market_data(ticker)
        if data:
            return {
                "success": True,
                "data": data,
                "message": "获取股票信息成功"
            }
        else:
            return {
                "success": False,
                "message": f"无法获取股票 {ticker} 的信息"
            }
    except Exception as e:
        return {
            "success": False,
            "message": "获取股票信息时发生错误",
            "error": str(e)
        }