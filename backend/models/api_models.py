"""
API数据模型

这个模块定义了API使用的请求和响应数据模型
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, TypeVar, Generic
from datetime import datetime, UTC

# 类型定义
T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """API响应的标准格式"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[T] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentInfo(BaseModel):
    """Agent信息模型"""
    name: str
    description: str
    state: str = "idle"  # idle, running, completed, error
    last_run: Optional[datetime] = None


class RunInfo(BaseModel):
    """运行信息模型"""
    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str  # "running", "completed", "error"
    agents: List[str] = []


class StockAnalysisRequest(BaseModel):
    """股票分析请求模型"""
    ticker: str = Field(
        ...,
        description="股票代码，例如：'002848'",
        example="002848"
    )
    show_reasoning: bool = Field(
        True,
        description="是否显示分析推理过程",
        example=True
    )
    num_of_news: int = Field(
        5,
        description="用于情感分析的新闻文章数量（1-100）",
        ge=1,
        le=100,
        example=5
    )
    initial_capital: float = Field(
        100000.0,
        description="初始资金",
        gt=0,
        example=100000.0
    )
    initial_position: int = Field(
        0,
        description="初始持仓数量",
        ge=0,
        example=0
    )
    start_date: Optional[str] = Field(
        None,
        description="分析开始日期 (YYYY-MM-DD)，为空则使用默认值（一年前）",
        example="2024-01-01"
    )
    end_date: Optional[str] = Field(
        None,
        description="分析结束日期 (YYYY-MM-DD)，为空则使用默认值（昨天）",
        example="2024-12-31"
    )
    show_summary: bool = Field(
        False,
        description="是否显示详细摘要报告",
        example=False
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "002848",
                "show_reasoning": True,
                "num_of_news": 5,
                "initial_capital": 100000.0,
                "initial_position": 0
            }
        }


class StockAnalysisResponse(BaseModel):
    """股票分析响应模型

    用于表示股票分析任务的响应信息，包含运行ID、状态和时间戳等
    """
    run_id: str = Field(..., description="分析任务唯一标识符")
    ticker: str = Field(..., description="股票代码")
    status: str = Field(..., description="任务状态：running, completed, error")
    message: str = Field(..., description="状态描述信息")
    submitted_at: datetime = Field(..., description="任务提交时间")
    completed_at: Optional[datetime] = Field(None, description="任务完成时间")

    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "550e8400-e29b-41d4-a716-446655440000",
                "ticker": "002848",
                "status": "running",
                "message": "分析任务已启动",
                "submitted_at": "2023-03-15T12:30:45.123Z",
                "completed_at": None
            }
        }


class AgentCreateRequest(BaseModel):
    """创建Agent请求模型"""
    name: str = Field(..., description="Agent名称（唯一标识符）")
    display_name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    agent_type: str = Field("analysis", description="Agent类型")
    status: str = Field("active", description="状态")
    config: Optional[Dict[str, Any]] = Field(None, description="配置信息")


class AgentUpdateRequest(BaseModel):
    """更新Agent请求模型"""
    display_name: Optional[str] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    status: Optional[str] = Field(None, description="状态")
    config: Optional[Dict[str, Any]] = Field(None, description="配置信息")


class AgentDecisionInfo(BaseModel):
    """Agent决策信息模型"""
    id: int
    run_id: str
    agent_name: str
    agent_display_name: Optional[str] = None
    ticker: str
    decision_type: str
    decision_data: Dict[str, Any]
    confidence_score: Optional[float] = None
    reasoning: Optional[str] = None
    created_at: datetime


class DecisionDisplayRequest(BaseModel):
    """决策显示格式请求模型"""
    run_id: Optional[str] = Field(None, description="运行ID筛选")
    agent_name: Optional[str] = Field(None, description="Agent名称筛选")
    ticker: Optional[str] = Field(None, description="股票代码筛选")
    limit: int = Field(50, description="返回数量限制", ge=1, le=200)


# 回测相关数据模型
class BacktestRequest(BaseModel):
    """回测请求模型"""
    ticker: str = Field(
        ...,
        description="股票代码，例如：'002848'",
        example="002848"
    )
    start_date: str = Field(
        ...,
        description="回测开始日期，格式：YYYY-MM-DD",
        example="2024-01-01"
    )
    end_date: str = Field(
        ...,
        description="回测结束日期，格式：YYYY-MM-DD",
        example="2024-12-31"
    )
    initial_capital: float = Field(
        100000.0,
        description="初始资金",
        gt=0,
        example=100000.0
    )
    num_of_news: int = Field(
        5,
        description="用于情感分析的新闻文章数量（1-100）",
        ge=1,
        le=100,
        example=5
    )
    agent_frequencies: Optional[Dict[str, str]] = Field(
        None,
        description="各Agent的执行频率配置",
        example={
            "market_data": "daily",
            "technical": "daily",
            "fundamentals": "weekly",
            "sentiment": "daily",
            "valuation": "monthly",
            "macro": "weekly",
            "portfolio": "daily"
        }
    )
    time_granularity: Optional[str] = Field(
        "daily",
        description="时间细粒度：minute/hourly/daily/weekly",
        example="daily"
    )
    benchmark_type: Optional[str] = Field(
        "spe",
        description="基准策略类型：spe/csi300/equal_weight/momentum/mean_reversion",
        example="spe"
    )
    rebalance_frequency: Optional[str] = Field(
        "daily",
        description="调仓频率：daily/weekly/monthly/quarterly",
        example="daily"
    )
    transaction_cost: Optional[float] = Field(
        0.001,
        description="交易手续费率（小数形式）",
        ge=0,
        le=0.01,
        example=0.001
    )
    slippage: Optional[float] = Field(
        0.0005,
        description="滑点率（小数形式）",
        ge=0,
        le=0.005,
        example=0.0005
    )
    
    class Config:
        json_schema_extra = {
            "example": {
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
        }


class BacktestResponse(BaseModel):
    """回测响应模型"""
    run_id: str = Field(..., description="回测任务唯一标识符")
    ticker: str = Field(..., description="股票代码")
    start_date: str = Field(..., description="回测开始日期")
    end_date: str = Field(..., description="回测结束日期")
    status: str = Field(..., description="任务状态：running, completed, error")
    message: str = Field(..., description="状态描述信息")
    submitted_at: datetime = Field(..., description="任务提交时间")
    completed_at: Optional[datetime] = Field(None, description="任务完成时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "550e8400-e29b-41d4-a716-446655440001",
                "ticker": "002848",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "status": "running",
                "message": "回测任务已启动",
                "submitted_at": "2023-03-15T12:30:45.123Z",
                "completed_at": None
            }
        }


class BacktestResultData(BaseModel):
    """回测结果数据模型"""
    performance_metrics: Dict[str, Any] = Field(..., description="性能指标")
    risk_metrics: Dict[str, Any] = Field(..., description="风险指标")
    trades: List[Dict[str, Any]] = Field(..., description="交易记录")
    portfolio_values: Dict[str, Any] = Field(..., description="组合价值时间序列")
    benchmark_comparison: Optional[Dict[str, Any]] = Field(None, description="基准比较")
    
    class Config:
        json_schema_extra = {
            "example": {
                "performance_metrics": {
                    "total_return": 0.15,
                    "annualized_return": 0.12,
                    "sharpe_ratio": 1.25,
                    "max_drawdown": -0.08
                },
                "risk_metrics": {
                    "volatility": 0.18,
                    "var_95": -0.025,
                    "beta": 1.1
                },
                "trades": [
                    {
                        "date": "2024-01-15",
                        "action": "buy",
                        "shares": 100,
                        "price": 25.5,
                        "commission": 5.0
                    }
                ],
                "portfolio_values": {
                    "dates": ["2024-01-01", "2024-01-02"],
                    "values": [100000, 100250]
                }
            }
        }
