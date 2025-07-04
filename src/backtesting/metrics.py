"""
性能和风险指标计算器
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any
try:
    from .models import PerformanceMetrics, RiskMetrics, Trade
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.backtesting.models import PerformanceMetrics, RiskMetrics, Trade


class MetricsCalculator:
    """性能和风险指标计算器"""
    
    @staticmethod
    def calculate_performance_metrics(portfolio_values: List[Dict[str, Any]], 
                                    daily_returns: List[float],
                                    trades: List[Trade],
                                    initial_capital: float) -> PerformanceMetrics:
        """计算性能指标"""
        if not portfolio_values:
            return PerformanceMetrics()
            
        df = pd.DataFrame(portfolio_values).set_index("Date")
        daily_returns_array = np.array(daily_returns)
        
        final_value = portfolio_values[-1]["Portfolio Value"]
        total_return = (final_value - initial_capital) / initial_capital
        
        days = len(df)
        annualized_return = (1 + total_return) ** (252 / days) - 1 if days > 0 else 0
        
        volatility = np.std(daily_returns_array) * np.sqrt(252) if len(daily_returns_array) > 1 else 0
        
        risk_free_rate = 0.03
        excess_return = annualized_return - risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        rolling_max = df["Portfolio Value"].cummax()
        drawdown = (df["Portfolio Value"] / rolling_max - 1)
        max_drawdown = drawdown.min()
        
        profitable_trades = [t for t in trades if MetricsCalculator._calculate_trade_pnl(t) > 0]
        win_rate = len(profitable_trades) / len(trades) if trades else 0
        
        profits = sum([MetricsCalculator._calculate_trade_pnl(t) for t in profitable_trades])
        losses = sum([abs(MetricsCalculator._calculate_trade_pnl(t)) for t in trades 
                     if MetricsCalculator._calculate_trade_pnl(t) < 0])
        profit_factor = profits / losses if losses > 0 else float('inf') if profits > 0 else 0
        
        avg_trade_return = np.mean([MetricsCalculator._calculate_trade_pnl(t) for t in trades]) if trades else 0
        
        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            trades_count=len(trades),
            avg_trade_return=avg_trade_return
        )
    
    @staticmethod
    def calculate_risk_metrics(daily_returns: List[float], 
                             benchmark_returns: List[float]) -> RiskMetrics:
        """计算修正的风险指标"""
        if len(daily_returns) < 2:  # 最少需要2个数据点
            return RiskMetrics()
            
        returns_array = np.array(daily_returns)
        
        # 计算VaR和ES，即使在数据点较少时也要计算
        var_95 = np.percentile(returns_array, 5) if len(returns_array) >= 2 else (returns_array[0] if len(returns_array) > 0 else 0)
        tail_returns = returns_array[returns_array <= var_95]
        es = np.mean(tail_returns) if len(tail_returns) > 0 else var_95
        
        beta = 0.0
        alpha = 0.0
        tracking_error = 0.0
        information_ratio = 0.0
        
        # 确保基准收益率数据存在且长度匹配
        if len(benchmark_returns) == len(daily_returns) and len(benchmark_returns) >= 2:
            benchmark_array = np.array(benchmark_returns)
            
            # 过滤掉无效数据
            valid_indices = ~(np.isnan(returns_array) | np.isnan(benchmark_array) | 
                            np.isinf(returns_array) | np.isinf(benchmark_array))
            
            if np.sum(valid_indices) >= 2:
                valid_returns = returns_array[valid_indices]
                valid_benchmark = benchmark_array[valid_indices]
                
                benchmark_std = np.std(valid_benchmark)
                if benchmark_std > 1e-8:  # 避免除零错误
                    # 计算beta
                    if len(valid_returns) >= 2 and len(valid_benchmark) >= 2:
                        try:
                            covariance_matrix = np.cov(valid_returns, valid_benchmark)
                            if covariance_matrix.shape == (2, 2):
                                covariance = covariance_matrix[0, 1]
                                benchmark_variance = np.var(valid_benchmark)
                                beta = covariance / benchmark_variance if benchmark_variance > 1e-8 else 0
                        except:
                            beta = 0
                    
                    # 计算alpha
                    if len(valid_returns) >= 2:
                        portfolio_return = np.mean(valid_returns) * 252
                        benchmark_return = np.mean(valid_benchmark) * 252
                        risk_free_rate = 0.03
                        alpha = portfolio_return - (risk_free_rate + beta * (benchmark_return - risk_free_rate))
                
                # 计算跟踪误差和信息比率
                excess_returns = valid_returns - valid_benchmark
                if len(excess_returns) >= 2:
                    tracking_error = np.std(excess_returns) * np.sqrt(252)
                    
                    if tracking_error > 1e-8:
                        mean_excess_return = np.mean(excess_returns) * 252
                        information_ratio = mean_excess_return / tracking_error
        
        return RiskMetrics(
            value_at_risk=var_95,
            expected_shortfall=es,
            beta=beta,
            alpha=alpha,
            information_ratio=information_ratio,
            tracking_error=tracking_error
        )
    
    @staticmethod
    def _calculate_trade_pnl(trade: Trade) -> float:
        """计算单笔交易盈亏"""
        try:
            if trade.action == "buy":
                return -trade.executed_quantity * trade.price - trade.commission
            else:  # sell
                return trade.executed_quantity * trade.price - trade.commission
        except (AttributeError, TypeError):
            # Handle cases where trade is a Mock object or has invalid attributes
            return 0.0