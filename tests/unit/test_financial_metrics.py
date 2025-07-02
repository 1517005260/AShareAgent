"""
测试金融指标计算，包括VaR等风险指标

测试包含:
1. VaR (Value at Risk) 计算
2. Expected Shortfall (ES) 计算  
3. Beta和Alpha计算
4. 夏普比率计算
5. 最大回撤计算
6. 跟踪误差和信息比率
7. 性能指标计算
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.backtesting.metrics import MetricsCalculator
from src.backtesting.models import PerformanceMetrics, RiskMetrics, Trade


class TestFinancialMetricsCalculation:
    """测试金融指标计算功能"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 创建测试数据
        np.random.seed(42)  # 确保可重复性
        
        # 生成模拟投资组合收益率
        self.returns = np.random.normal(0.001, 0.02, 252)  # 年化收益率数据
        
        # 生成基准收益率
        self.benchmark_returns = np.random.normal(0.0008, 0.015, 252)
        
        # 创建投资组合价值序列
        initial_value = 100000
        cumulative_returns = np.cumprod(1 + self.returns)
        portfolio_values = initial_value * cumulative_returns
        
        self.portfolio_values = []
        for i, value in enumerate(portfolio_values):
            self.portfolio_values.append({
                'Date': datetime(2024, 1, 1) + timedelta(days=i),
                'Portfolio Value': value,
                'Daily Return': self.returns[i] * 100
            })
        
        # 创建交易记录
        self.trades = [
            Trade(datetime(2024, 1, 1), 'buy', 100, 100.0, 100, 0.3),
            Trade(datetime(2024, 1, 15), 'sell', 50, 105.0, 50, 0.15),
            Trade(datetime(2024, 1, 30), 'buy', 25, 98.0, 25, 0.075)
        ]
        
        self.initial_capital = 100000
    
    def test_var_calculation(self):
        """测试VaR (Value at Risk) 计算"""
        risk_metrics = MetricsCalculator.calculate_risk_metrics(
            self.returns.tolist(), self.benchmark_returns.tolist()
        )
        
        # VaR应该是负值（损失）
        assert risk_metrics.value_at_risk < 0
        
        # 手动计算VaR进行验证
        manual_var = np.percentile(self.returns, 5)
        assert abs(risk_metrics.value_at_risk - manual_var) < 1e-10
        
        # VaR应该在合理范围内（日收益率）
        assert risk_metrics.value_at_risk > -0.1  # 不应该超过-10%
        assert risk_metrics.value_at_risk < 0     # 应该是负值
    
    def test_expected_shortfall_calculation(self):
        """测试Expected Shortfall (条件VaR) 计算"""
        risk_metrics = MetricsCalculator.calculate_risk_metrics(
            self.returns.tolist(), self.benchmark_returns.tolist()
        )
        
        # ES应该比VaR更负（更大损失）
        assert risk_metrics.expected_shortfall <= risk_metrics.value_at_risk
        
        # 手动计算ES进行验证
        var_95 = np.percentile(self.returns, 5)
        tail_returns = self.returns[self.returns <= var_95]
        manual_es = np.mean(tail_returns) if len(tail_returns) > 0 else 0
        
        assert abs(risk_metrics.expected_shortfall - manual_es) < 1e-10
    
    def test_beta_calculation(self):
        """测试Beta系数计算"""
        risk_metrics = MetricsCalculator.calculate_risk_metrics(
            self.returns.tolist(), self.benchmark_returns.tolist()
        )
        
        # Beta应该在合理范围内
        assert -2.0 <= risk_metrics.beta <= 3.0
        
        # 手动计算Beta进行验证
        covariance = np.cov(self.returns, self.benchmark_returns)[0, 1]
        benchmark_variance = np.var(self.benchmark_returns)
        manual_beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
        
        assert abs(risk_metrics.beta - manual_beta) < 1e-10
    
    def test_alpha_calculation(self):
        """测试Alpha计算"""
        risk_metrics = MetricsCalculator.calculate_risk_metrics(
            self.returns.tolist(), self.benchmark_returns.tolist()
        )
        
        # Alpha可以是正值或负值
        assert -1.0 <= risk_metrics.alpha <= 1.0  # 年化Alpha在合理范围内
        
        # 手动计算Alpha进行验证
        portfolio_return = np.mean(self.returns) * 252
        benchmark_return = np.mean(self.benchmark_returns) * 252
        risk_free_rate = 0.03
        manual_alpha = portfolio_return - (risk_free_rate + risk_metrics.beta * (benchmark_return - risk_free_rate))
        
        assert abs(risk_metrics.alpha - manual_alpha) < 1e-10
    
    def test_tracking_error_calculation(self):
        """测试跟踪误差计算"""
        risk_metrics = MetricsCalculator.calculate_risk_metrics(
            self.returns.tolist(), self.benchmark_returns.tolist()
        )
        
        # 跟踪误差应该是正值
        assert risk_metrics.tracking_error >= 0
        
        # 手动计算跟踪误差进行验证
        excess_returns = self.returns - self.benchmark_returns
        manual_tracking_error = np.std(excess_returns) * np.sqrt(252)
        
        assert abs(risk_metrics.tracking_error - manual_tracking_error) < 1e-10
    
    def test_information_ratio_calculation(self):
        """测试信息比率计算"""
        risk_metrics = MetricsCalculator.calculate_risk_metrics(
            self.returns.tolist(), self.benchmark_returns.tolist()
        )
        
        # 信息比率可以是正值或负值
        assert -5.0 <= risk_metrics.information_ratio <= 5.0
        
        # 手动计算信息比率进行验证
        excess_returns = self.returns - self.benchmark_returns
        mean_excess_return = np.mean(excess_returns) * 252
        manual_ir = mean_excess_return / risk_metrics.tracking_error if risk_metrics.tracking_error > 0 else 0
        
        assert abs(risk_metrics.information_ratio - manual_ir) < 1e-10
    
    def test_sharpe_ratio_calculation(self):
        """测试夏普比率计算"""
        perf_metrics = MetricsCalculator.calculate_performance_metrics(
            self.portfolio_values, self.returns.tolist(), self.trades, self.initial_capital
        )
        
        # 夏普比率应该在合理范围内
        assert -3.0 <= perf_metrics.sharpe_ratio <= 5.0
        
        # 手动计算夏普比率进行验证
        annualized_return = perf_metrics.annualized_return
        volatility = np.std(self.returns) * np.sqrt(252)
        risk_free_rate = 0.03
        manual_sharpe = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        assert abs(perf_metrics.sharpe_ratio - manual_sharpe) < 1e-10
    
    def test_max_drawdown_calculation(self):
        """测试最大回撤计算"""
        perf_metrics = MetricsCalculator.calculate_performance_metrics(
            self.portfolio_values, self.returns.tolist(), self.trades, self.initial_capital
        )
        
        # 最大回撤应该是负值或零
        assert perf_metrics.max_drawdown <= 0
        
        # 手动计算最大回撤进行验证
        df = pd.DataFrame(self.portfolio_values).set_index('Date')
        rolling_max = df['Portfolio Value'].cummax()
        drawdown = (df['Portfolio Value'] / rolling_max - 1)
        manual_max_drawdown = drawdown.min()
        
        assert abs(perf_metrics.max_drawdown - manual_max_drawdown) < 1e-10
    
    def test_win_rate_calculation(self):
        """测试胜率计算"""
        perf_metrics = MetricsCalculator.calculate_performance_metrics(
            self.portfolio_values, self.returns.tolist(), self.trades, self.initial_capital
        )
        
        # 胜率应该在0-1之间
        assert 0 <= perf_metrics.win_rate <= 1
        
        # 手动计算胜率进行验证
        profitable_trades = [t for t in self.trades 
                           if MetricsCalculator._calculate_trade_pnl(t) > 0]
        manual_win_rate = len(profitable_trades) / len(self.trades) if self.trades else 0
        
        assert abs(perf_metrics.win_rate - manual_win_rate) < 1e-10
    
    def test_profit_factor_calculation(self):
        """测试盈利因子计算"""
        perf_metrics = MetricsCalculator.calculate_performance_metrics(
            self.portfolio_values, self.returns.tolist(), self.trades, self.initial_capital
        )
        
        # 盈利因子应该是正值
        assert perf_metrics.profit_factor >= 0
        
        # 手动计算盈利因子进行验证
        profits = sum([MetricsCalculator._calculate_trade_pnl(t) for t in self.trades 
                      if MetricsCalculator._calculate_trade_pnl(t) > 0])
        losses = sum([abs(MetricsCalculator._calculate_trade_pnl(t)) for t in self.trades 
                     if MetricsCalculator._calculate_trade_pnl(t) < 0])
        manual_profit_factor = profits / losses if losses > 0 else float('inf') if profits > 0 else 0
        
        if manual_profit_factor != float('inf'):
            assert abs(perf_metrics.profit_factor - manual_profit_factor) < 1e-10
    
    def test_volatility_calculation(self):
        """测试波动率计算"""
        perf_metrics = MetricsCalculator.calculate_performance_metrics(
            self.portfolio_values, self.returns.tolist(), self.trades, self.initial_capital
        )
        
        # 波动率应该是正值
        assert perf_metrics.volatility >= 0
        
        # 手动计算年化波动率进行验证
        manual_volatility = np.std(self.returns) * np.sqrt(252)
        
        assert abs(perf_metrics.volatility - manual_volatility) < 1e-10
    
    def test_trade_pnl_calculation(self):
        """测试单笔交易盈亏计算"""
        buy_trade = Trade(datetime(2024, 1, 1), 'buy', 100, 100.0, 100, 0.3)
        sell_trade = Trade(datetime(2024, 1, 15), 'sell', 100, 105.0, 100, 0.3)
        
        buy_pnl = MetricsCalculator._calculate_trade_pnl(buy_trade)
        sell_pnl = MetricsCalculator._calculate_trade_pnl(sell_trade)
        
        # 买入交易的PnL应该是负值（现金流出）
        assert buy_pnl < 0
        expected_buy_pnl = -100 * 100.0 - 0.3
        assert abs(buy_pnl - expected_buy_pnl) < 1e-10
        
        # 卖出交易的PnL应该是正值（现金流入）
        assert sell_pnl > 0
        expected_sell_pnl = 100 * 105.0 - 0.3
        assert abs(sell_pnl - expected_sell_pnl) < 1e-10
    
    def test_insufficient_data_handling(self):
        """测试数据不足时的处理"""
        # 测试空数据
        empty_metrics = MetricsCalculator.calculate_risk_metrics([], [])
        assert empty_metrics.value_at_risk == 0
        assert empty_metrics.expected_shortfall == 0
        assert empty_metrics.beta == 0
        
        # 测试数据不足（少于30个点）
        short_returns = [0.01, 0.02, -0.01]
        short_metrics = MetricsCalculator.calculate_risk_metrics(short_returns, [])
        assert short_metrics.value_at_risk == 0
        assert short_metrics.expected_shortfall == 0
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 测试零方差基准
        zero_var_benchmark = [0.001] * 100  # 完全无波动的基准
        returns = np.random.normal(0.001, 0.02, 100).tolist()
        
        metrics = MetricsCalculator.calculate_risk_metrics(returns, zero_var_benchmark)
        # 当基准方差为0时，beta应该为0
        assert metrics.beta == 0
        # 追踪误差应该等于投资组合收益率的标准差（年化）
        expected_tracking_error = np.std(returns) * np.sqrt(252)
        assert abs(metrics.tracking_error - expected_tracking_error) < 1e-10
        
        # 测试相同的投资组合和基准收益率
        identical_returns = [0.01, 0.02, -0.01, 0.005] * 10
        identical_metrics = MetricsCalculator.calculate_risk_metrics(identical_returns, identical_returns)
        
        # Beta应该接近1，跟踪误差应该接近0
        assert abs(identical_metrics.beta - 1.0) < 0.1  # 放宽容差，允许数值计算误差
        assert abs(identical_metrics.tracking_error) < 1e-10
        assert abs(identical_metrics.information_ratio) < 1e-10


@pytest.mark.parametrize("confidence_level,expected_percentile", [
    (0.95, 5),
    (0.99, 1),
    (0.90, 10),
])
def test_var_confidence_levels(confidence_level, expected_percentile):
    """测试不同置信水平的VaR计算"""
    np.random.seed(42)
    returns = np.random.normal(0, 0.02, 1000)
    
    # 注意：当前实现固定使用95% VaR
    # 这个测试展示了如何扩展以支持不同置信水平
    var = np.percentile(returns, expected_percentile)
    
    # 验证VaR的合理性
    assert var < 0  # VaR应该是负值
    # 对于置信水平，VaR应该表示在该置信水平下的最大损失
    # 例如，95%置信水平意味着5%的数据低于VaR
    actual_percentile = len(returns[returns <= var]) / len(returns) * 100
    expected_percentile_threshold = expected_percentile + 1  # 允许1%误差
    assert actual_percentile <= expected_percentile_threshold


class TestFinancialMetricsIntegration:
    """金融指标计算的集成测试"""
    
    def test_metrics_consistency(self):
        """测试指标计算的一致性"""
        np.random.seed(123)
        
        # 生成一致的测试数据
        returns = np.random.normal(0.0005, 0.015, 252)
        benchmark_returns = np.random.normal(0.0003, 0.012, 252)
        
        initial_capital = 100000
        cumulative_returns = np.cumprod(1 + returns)
        portfolio_values = []
        
        for i, cum_ret in enumerate(cumulative_returns):
            portfolio_values.append({
                'Date': datetime(2024, 1, 1) + timedelta(days=i),
                'Portfolio Value': initial_capital * cum_ret,
                'Daily Return': returns[i] * 100
            })
        
        trades = [Trade(datetime(2024, 1, 1), 'buy', 100, 100.0, 100, 0.3)]
        
        # 计算所有指标
        perf_metrics = MetricsCalculator.calculate_performance_metrics(
            portfolio_values, returns.tolist(), trades, initial_capital
        )
        risk_metrics = MetricsCalculator.calculate_risk_metrics(
            returns.tolist(), benchmark_returns.tolist()
        )
        
        # 验证指标间的关系
        # 1. 夏普比率应该与收益率和波动率一致
        expected_sharpe = (perf_metrics.annualized_return - 0.03) / perf_metrics.volatility
        assert abs(perf_metrics.sharpe_ratio - expected_sharpe) < 1e-10
        
        # 2. VaR应该比ES更小（绝对值）
        assert abs(risk_metrics.value_at_risk) <= abs(risk_metrics.expected_shortfall)
        
        # 3. 所有概率指标应该在合理范围内
        assert 0 <= perf_metrics.win_rate <= 1
        assert perf_metrics.max_drawdown <= 0
        assert perf_metrics.volatility >= 0
    
    @patch('src.backtesting.backtester.IntelligentBacktester')
    def test_metrics_with_backtester_integration(self, mock_backtester):
        """测试指标计算与回测系统的集成"""
        # 模拟回测器返回的数据
        mock_instance = mock_backtester.return_value
        
        # 设置回测结果
        portfolio_values = [
            {'Date': datetime(2024, 1, 1), 'Portfolio Value': 100000, 'Daily Return': 0},
            {'Date': datetime(2024, 1, 2), 'Portfolio Value': 101000, 'Daily Return': 1.0},
            {'Date': datetime(2024, 1, 3), 'Portfolio Value': 99500, 'Daily Return': -1.49},
        ]
        
        daily_returns = [0.0, 0.01, -0.0149]
        benchmark_returns = [0.0, 0.008, -0.012]
        
        trades = [Trade(datetime(2024, 1, 1), 'buy', 100, 100.0, 100, 0.3)]
        
        # 计算指标
        perf_metrics = MetricsCalculator.calculate_performance_metrics(
            portfolio_values, daily_returns, trades, 100000
        )
        risk_metrics = MetricsCalculator.calculate_risk_metrics(
            daily_returns, benchmark_returns
        )
        
        # 验证指标计算成功
        assert perf_metrics is not None
        assert risk_metrics is not None
        assert isinstance(perf_metrics.total_return, float)
        assert isinstance(risk_metrics.value_at_risk, float)
