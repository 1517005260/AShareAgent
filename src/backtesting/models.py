"""
数据模型和类型定义
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentConfig:
    """Agent配置"""
    name: str
    frequency: str  # 'daily', 'weekly', 'monthly', 'conditional'
    condition: Optional[str] = None  # 条件触发规则
    cache_duration: int = 1  # 缓存持续天数


@dataclass
class Trade:
    """交易执行记录"""
    date: str
    action: str
    quantity: int
    price: float
    executed_quantity: int
    commission: float = 0.0
    slippage: float = 0.0
    
    def to_dict(self):
        """转换为字典格式"""
        total_amount = self.executed_quantity * self.price
        return {
            "date": self.date,
            "action": self.action,
            "quantity": self.quantity,
            "price": self.price,
            "executed_quantity": self.executed_quantity,
            "commission": self.commission,
            "slippage": self.slippage,
            "total_amount": total_amount
        }


@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    trades_count: int = 0
    avg_trade_return: float = 0.0


@dataclass
class RiskMetrics:
    """风险指标"""
    value_at_risk: float = 0.0
    expected_shortfall: float = 0.0
    beta: float = 0.0
    alpha: float = 0.0
    information_ratio: float = 0.0
    tracking_error: float = 0.0