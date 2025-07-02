"""
交易执行器 - 处理买卖操作和手续费
"""

from typing import Dict, List
try:
    from .models import Trade
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.backtesting.models import Trade


class TradeExecutor:
    """交易执行器"""
    
    def __init__(self, commission_rate: float = 0.0003, slippage_rate: float = 0.001):
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.trades: List[Trade] = []
    
    def execute_trade(self, action: str, quantity: int, current_price: float, 
                     date: str, portfolio: Dict[str, float]) -> int:
        """执行交易，包含手续费和滑点"""
        executed_quantity = 0
        
        if action == "buy" and quantity > 0:
            execution_price = current_price * (1 + self.slippage_rate)
            gross_cost = quantity * execution_price
            commission = gross_cost * self.commission_rate
            total_cost = gross_cost + commission
            
            if total_cost <= portfolio["cash"]:
                executed_quantity = quantity
            else:
                max_affordable = portfolio["cash"] / (execution_price * (1 + self.commission_rate))
                executed_quantity = int(max_affordable)
                
            if executed_quantity > 0:
                actual_cost = executed_quantity * execution_price
                actual_commission = actual_cost * self.commission_rate
                portfolio["stock"] += executed_quantity
                portfolio["cash"] -= (actual_cost + actual_commission)
                
                trade = Trade(
                    date=date,
                    action=action,
                    quantity=quantity,
                    price=execution_price,
                    executed_quantity=executed_quantity,
                    commission=actual_commission,
                    slippage=execution_price - current_price
                )
                self.trades.append(trade)
                
        elif action == "sell" and quantity > 0:
            execution_price = current_price * (1 - self.slippage_rate)
            executed_quantity = min(quantity, portfolio["stock"])
            
            if executed_quantity > 0:
                gross_proceeds = executed_quantity * execution_price
                commission = gross_proceeds * self.commission_rate
                net_proceeds = gross_proceeds - commission
                
                portfolio["cash"] += net_proceeds
                portfolio["stock"] -= executed_quantity
                
                trade = Trade(
                    date=date,
                    action=action,
                    quantity=quantity,
                    price=execution_price,
                    executed_quantity=executed_quantity,
                    commission=commission,
                    slippage=current_price - execution_price
                )
                self.trades.append(trade)
                
        return executed_quantity
    
    def calculate_trade_pnl(self, trade: Trade) -> float:
        """计算单笔交易盈亏"""
        if trade.action == "buy":
            return -trade.executed_quantity * trade.price - trade.commission
        else:  # sell
            return trade.executed_quantity * trade.price - trade.commission