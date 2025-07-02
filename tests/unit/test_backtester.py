"""
回测系统测试模块

测试回测器的核心功能，包括：
- 回测框架初始化
- 交易执行逻辑
- 性能指标计算
- 风险管理
- 数据处理和验证
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
import json
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.backtester import Backtester, Trade, PerformanceMetrics, RiskMetrics


class TestBacktesterInitialization:
    """测试回测器初始化功能"""
    
    def test_basic_initialization(self):
        """测试基本初始化"""
        mock_agent = Mock()
        backtester = Backtester(
            agent=mock_agent,
            ticker="000001",
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=100000,
            num_of_news=5
        )
        
        assert backtester.ticker == "000001"
        assert backtester.initial_capital == 100000
        assert backtester.portfolio["cash"] == 100000
        assert backtester.portfolio["stock"] == 0
        assert backtester.commission_rate == 0.0003
        assert backtester.slippage_rate == 0.001
        
    def test_custom_initialization_parameters(self):
        """测试自定义初始化参数"""
        mock_agent = Mock()
        backtester = Backtester(
            agent=mock_agent,
            ticker="600519",
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=200000,
            num_of_news=10,
            commission_rate=0.0005,
            slippage_rate=0.002,
            benchmark_ticker="000300"
        )
        
        assert backtester.initial_capital == 200000
        assert backtester.commission_rate == 0.0005
        assert backtester.slippage_rate == 0.002
        assert backtester.benchmark_ticker == "000300"
        
    def test_input_validation_success(self):
        """测试输入验证成功情况"""
        mock_agent = Mock()
        backtester = Backtester(
            agent=mock_agent,
            ticker="000001",
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=100000,
            num_of_news=5
        )
        # 如果没有异常则通过
        assert backtester is not None
        
    def test_input_validation_invalid_dates(self):
        """测试无效日期输入"""
        mock_agent = Mock()
        with pytest.raises(ValueError, match="开始日期必须早于结束日期"):
            Backtester(
                agent=mock_agent,
                ticker="000001",
                start_date="2024-01-31",
                end_date="2024-01-01",
                initial_capital=100000,
                num_of_news=5
            )
            
    def test_input_validation_invalid_capital(self):
        """测试无效资金输入"""
        mock_agent = Mock()
        with pytest.raises(ValueError, match="初始资金必须大于0"):
            Backtester(
                agent=mock_agent,
                ticker="000001",
                start_date="2024-01-01",
                end_date="2024-01-31",
                initial_capital=-1000,
                num_of_news=5
            )
            
    def test_input_validation_invalid_ticker(self):
        """测试无效股票代码"""
        mock_agent = Mock()
        with pytest.raises(ValueError, match="无效的股票代码格式"):
            Backtester(
                agent=mock_agent,
                ticker="INVALID",
                start_date="2024-01-01",
                end_date="2024-01-31",
                initial_capital=100000,
                num_of_news=5
            )


class TestTradeExecution:
    """测试交易执行功能"""
    
    @pytest.fixture
    def backtester(self):
        """创建测试用回测器"""
        mock_agent = Mock()
        return Backtester(
            agent=mock_agent,
            ticker="000001",
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=100000,
            num_of_news=5
        )
        
    def test_buy_trade_execution(self, backtester):
        """测试买入交易执行"""
        initial_cash = backtester.portfolio["cash"]
        current_price = 10.0
        quantity = 1000
        
        executed_qty = backtester.execute_trade("buy", quantity, current_price, "2024-01-01")
        
        # 计算预期成本
        execution_price = current_price * (1 + backtester.slippage_rate)
        total_cost = quantity * execution_price
        commission = total_cost * backtester.commission_rate
        expected_cash = initial_cash - total_cost - commission
        
        assert executed_qty == quantity
        assert backtester.portfolio["stock"] == quantity
        assert abs(backtester.portfolio["cash"] - expected_cash) < 0.01
        assert len(backtester.trades) == 1
        
    def test_sell_trade_execution(self, backtester):
        """测试卖出交易执行"""
        # 先买入一些股票
        backtester.portfolio["stock"] = 1000
        backtester.portfolio["cash"] = 90000
        
        current_price = 11.0
        quantity = 500
        
        executed_qty = backtester.execute_trade("sell", quantity, current_price, "2024-01-01")
        
        # 计算预期收益
        execution_price = current_price * (1 - backtester.slippage_rate)
        gross_proceeds = quantity * execution_price
        commission = gross_proceeds * backtester.commission_rate
        net_proceeds = gross_proceeds - commission
        expected_cash = 90000 + net_proceeds
        
        assert executed_qty == quantity
        assert backtester.portfolio["stock"] == 500
        assert abs(backtester.portfolio["cash"] - expected_cash) < 0.01
        
    def test_insufficient_cash_buy(self, backtester):
        """测试资金不足时的买入"""
        current_price = 100.0
        quantity = 2000  # 需要20万，但只有10万
        
        executed_qty = backtester.execute_trade("buy", quantity, current_price, "2024-01-01")
        
        # 应该只能买入有限数量
        assert executed_qty < quantity
        assert backtester.portfolio["cash"] >= 0
        
    def test_insufficient_stock_sell(self, backtester):
        """测试股票不足时的卖出"""
        backtester.portfolio["stock"] = 500
        current_price = 10.0
        quantity = 1000  # 要卖1000股，但只有500股
        
        executed_qty = backtester.execute_trade("sell", quantity, current_price, "2024-01-01")
        
        assert executed_qty == 500  # 只能卖出现有的500股
        assert backtester.portfolio["stock"] == 0
        
    def test_hold_action(self, backtester):
        """测试持有动作"""
        initial_cash = backtester.portfolio["cash"]
        initial_stock = backtester.portfolio["stock"]
        
        executed_qty = backtester.execute_trade("hold", 0, 10.0, "2024-01-01")
        
        assert executed_qty == 0
        assert backtester.portfolio["cash"] == initial_cash
        assert backtester.portfolio["stock"] == initial_stock
        assert len(backtester.trades) == 0


class TestPerformanceCalculation:
    """测试性能指标计算"""
    
    @pytest.fixture
    def backtester_with_data(self):
        """创建带有历史数据的回测器"""
        mock_agent = Mock()
        backtester = Backtester(
            agent=mock_agent,
            ticker="000001",
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=100000,
            num_of_news=5
        )
        
        # 添加一些模拟的组合价值数据
        dates = pd.date_range("2024-01-01", "2024-01-31", freq="D")
        for i, date in enumerate(dates):
            portfolio_value = 100000 * (1 + np.random.normal(0, 0.01))  # 随机波动
            daily_return = (portfolio_value / 100000 - 1) if i == 0 else (portfolio_value / backtester.portfolio_values[-1]["Portfolio Value"] - 1)
            
            backtester.portfolio_values.append({
                "Date": date,
                "Portfolio Value": portfolio_value,
                "Daily Return": daily_return * 100
            })
            backtester.daily_returns.append(daily_return)
            
        backtester.portfolio["portfolio_value"] = backtester.portfolio_values[-1]["Portfolio Value"]
        return backtester
        
    def test_performance_metrics_calculation(self, backtester_with_data):
        """测试性能指标计算"""
        metrics = backtester_with_data.calculate_performance_metrics()
        
        assert isinstance(metrics, PerformanceMetrics)
        assert isinstance(metrics.total_return, (int, float))
        assert isinstance(metrics.annualized_return, (int, float))
        assert isinstance(metrics.volatility, (int, float))
        assert isinstance(metrics.sharpe_ratio, (int, float))
        assert isinstance(metrics.max_drawdown, (int, float))
        
        # 检查值的合理性
        assert -1 <= metrics.total_return <= 10  # 总回报在合理范围内
        assert 0 <= metrics.volatility <= 5  # 波动率非负
        assert -10 <= metrics.sharpe_ratio <= 10  # 夏普比率在合理范围内
        
    def test_risk_metrics_calculation(self, backtester_with_data):
        """测试风险指标计算"""
        metrics = backtester_with_data.calculate_risk_metrics()
        
        assert isinstance(metrics, RiskMetrics)
        assert isinstance(metrics.value_at_risk, (int, float))
        assert isinstance(metrics.expected_shortfall, (int, float))
        assert isinstance(metrics.beta, (int, float))
        
        # VaR应该是负值（表示损失）
        assert metrics.value_at_risk <= 0
        assert metrics.expected_shortfall <= metrics.value_at_risk
        
    def test_trade_statistics(self, backtester_with_data):
        """测试交易统计计算"""
        # 添加一些模拟交易到交易执行器
        test_trades = [
            Trade("2024-01-02", "buy", 100, 10.0, 100, 3.0),
            Trade("2024-01-05", "sell", 100, 11.0, 100, 3.3),
            Trade("2024-01-10", "buy", 200, 9.5, 200, 5.7),
            Trade("2024-01-15", "sell", 200, 9.0, 200, 5.4),
        ]
        backtester_with_data.trade_executor.trades.extend(test_trades)
        
        metrics = backtester_with_data.calculate_performance_metrics()
        
        assert metrics.trades_count == 4
        assert 0 <= metrics.win_rate <= 1
        assert metrics.profit_factor >= 0


class TestAgentDecisionProcessing:
    """测试智能体决策处理"""
    
    @pytest.fixture
    def backtester(self):
        """创建测试用回测器"""
        mock_agent = Mock()
        return Backtester(
            agent=mock_agent,
            ticker="000001",
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=100000,
            num_of_news=5
        )
        
    def test_valid_json_decision_parsing(self, backtester):
        """测试有效JSON决策解析"""
        mock_result = json.dumps({
            "action": "buy",
            "quantity": 500,
            "reason": "Strong bullish signals"
        })
        
        backtester.agent.return_value = mock_result
        
        with patch('src.backtester.get_price_data') as mock_price:
            mock_price.return_value = pd.DataFrame({
                'open': [10.0], 'close': [10.5], 'high': [10.8], 'low': [9.8]
            })
            
            result = backtester.get_agent_decision("2024-01-01", "2023-12-01", backtester.portfolio)
            
        assert result["decision"]["action"] == "buy"
        assert result["decision"]["quantity"] == 500
        
    def test_invalid_json_decision_fallback(self, backtester):
        """测试无效JSON时的回退处理"""
        backtester.agent.return_value = "Invalid JSON response"
        
        result = backtester.get_agent_decision("2024-01-01", "2023-12-01", backtester.portfolio)
        
        assert result["decision"]["action"] == "hold"
        assert result["decision"]["quantity"] == 0
        
    def test_agent_exception_handling(self, backtester):
        """测试智能体异常处理"""
        backtester.agent.side_effect = Exception("API Error")
        
        result = backtester.get_agent_decision("2024-01-01", "2023-12-01", backtester.portfolio)
        
        assert result["decision"]["action"] == "hold"
        assert result["decision"]["quantity"] == 0
        
    def test_text_decision_parsing(self, backtester):
        """测试文本决策解析"""
        test_cases = [
            ("I recommend to buy this stock", "buy"),
            ("This stock looks bearish, sell", "sell"),
            ("Market is uncertain, better to hold", "hold"),
            ("Strong bullish momentum", "buy"),
            ("Significant downside risk", "sell")
        ]
        
        for text, expected_action in test_cases:
            result = backtester.parse_decision_from_text(text)
            assert result["action"] == expected_action


class TestDataIntegration:
    """测试数据集成功能"""
    
    @pytest.fixture
    def backtester(self):
        """创建测试用回测器"""
        mock_agent = Mock()
        return Backtester(
            agent=mock_agent,
            ticker="000001",
            start_date="2024-01-01",
            end_date="2024-01-05",
            initial_capital=100000,
            num_of_news=5
        )
        
    @patch('src.backtester.get_price_data')
    def test_price_data_integration(self, mock_price_data, backtester):
        """测试价格数据集成"""
        # 模拟价格数据
        mock_price_data.return_value = pd.DataFrame({
            'open': [10.0, 10.5, 11.0],
            'close': [10.5, 11.0, 11.5],
            'high': [10.8, 11.2, 11.8],
            'low': [9.8, 10.3, 10.8],
            'volume': [1000000, 1200000, 800000]
        })
        
        # 模拟智能体返回
        backtester.agent.return_value = json.dumps({
            "action": "buy",
            "quantity": 100
        })
        
        # 运行一步回测
        output = backtester.get_agent_decision("2024-01-01", "2023-12-01", backtester.portfolio)
        
        assert output is not None
        assert "decision" in output
        
    def test_portfolio_value_tracking(self, backtester):
        """测试组合价值跟踪"""
        # 手动添加一些组合价值记录
        test_data = [
            {"Date": pd.Timestamp("2024-01-01"), "Portfolio Value": 100000, "Daily Return": 0},
            {"Date": pd.Timestamp("2024-01-02"), "Portfolio Value": 101000, "Daily Return": 1},
            {"Date": pd.Timestamp("2024-01-03"), "Portfolio Value": 99500, "Daily Return": -1.49}
        ]
        
        backtester.portfolio_values = test_data
        
        assert len(backtester.portfolio_values) == 3
        assert backtester.portfolio_values[0]["Portfolio Value"] == 100000
        assert backtester.portfolio_values[1]["Daily Return"] == 1


class TestErrorHandling:
    """测试错误处理功能"""
    
    @pytest.fixture
    def backtester(self):
        """创建测试用回测器"""
        mock_agent = Mock()
        return Backtester(
            agent=mock_agent,
            ticker="000001",
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=100000,
            num_of_news=5
        )
        
    def test_missing_price_data_handling(self, backtester):
        """测试缺失价格数据的处理"""
        backtester.agent.return_value = json.dumps({"action": "buy", "quantity": 100})
        
        with patch('src.backtester.get_price_data') as mock_price:
            mock_price.return_value = None  # 模拟数据获取失败
            
            result = backtester.get_agent_decision("2024-01-01", "2023-12-01", backtester.portfolio)
            
        # 应该返回有效的决策，即使价格数据缺失
        assert result is not None
        assert "decision" in result
        
    def test_empty_dataframe_handling(self, backtester):
        """测试空数据框处理"""
        backtester.agent.return_value = json.dumps({"action": "buy", "quantity": 100})
        
        with patch('src.backtester.get_price_data') as mock_price:
            mock_price.return_value = pd.DataFrame()  # 空数据框
            
            result = backtester.get_agent_decision("2024-01-01", "2023-12-01", backtester.portfolio)
            
        assert result is not None
        assert "decision" in result


class TestBacktesterIntegration:
    """测试回测器集成功能"""
    
    def test_complete_backtest_workflow_mock(self):
        """测试完整的回测工作流程（使用模拟数据）"""
        mock_agent = Mock()
        
        # 创建回测器
        backtester = Backtester(
            agent=mock_agent,
            ticker="000001",
            start_date="2024-01-01",
            end_date="2024-01-03",  # 短期测试
            initial_capital=100000,
            num_of_news=5
        )
        
        # 模拟智能体决策
        mock_agent.return_value = json.dumps({
            "action": "buy",
            "quantity": 1000,
            "reason": "Test decision"
        })
        
        # 模拟价格数据
        with patch('src.backtester.get_price_data') as mock_price:
            mock_price.return_value = pd.DataFrame({
                'open': [10.0],
                'close': [10.5],
                'high': [10.8],
                'low': [9.8]
            })
            
            # 运行回测（只测试核心逻辑，不实际遍历日期）
            decision = backtester.get_agent_decision("2024-01-01", "2023-12-01", backtester.portfolio)
            
        assert decision is not None
        assert decision["decision"]["action"] == "buy"
        
        # 测试交易执行
        executed_qty = backtester.execute_trade("buy", 1000, 10.0, "2024-01-01")
        assert executed_qty > 0
        assert backtester.portfolio["stock"] > 0
        assert backtester.portfolio["cash"] < backtester.initial_capital
        
    def test_performance_analysis_with_minimal_data(self):
        """测试最小数据集的性能分析"""
        mock_agent = Mock()
        backtester = Backtester(
            agent=mock_agent,
            ticker="000001",
            start_date="2024-01-01",
            end_date="2024-01-05",
            initial_capital=100000,
            num_of_news=5
        )
        
        # 添加最小数据集
        backtester.portfolio_values = [
            {"Date": pd.Timestamp("2024-01-01"), "Portfolio Value": 100000, "Daily Return": 0},
            {"Date": pd.Timestamp("2024-01-02"), "Portfolio Value": 101000, "Daily Return": 1}
        ]
        backtester.daily_returns.append(0.01)
        backtester.portfolio["portfolio_value"] = 101000
        
        # 应该能够计算基本指标而不出错
        metrics = backtester.calculate_performance_metrics()
        assert metrics is not None
        assert metrics.total_return > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])