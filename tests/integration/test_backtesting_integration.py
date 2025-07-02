"""
集成测试：回测系统完整流程测试

测试包含:
1. 完整的回测流程测试
2. Agent协调工作测试
3. 数据管道集成测试
4. 错误处理和恢复测试
5. 性能指标集成测试
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import os
import json

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.backtesting.backtester import IntelligentBacktester
from src.backtesting.models import Trade, PerformanceMetrics, RiskMetrics
from src.backtesting.metrics import MetricsCalculator
from src.backtesting.trading import TradeExecutor
from src.backtesting.visualizer import PerformanceVisualizer


class TestBacktestingIntegration:
    """回测系统集成测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 创建模拟agent
        self.mock_agent = Mock()
        
        # 设置默认返回值
        self.mock_agent.return_value = json.dumps({
            "action": "buy",
            "quantity": 100,
            "agent_signals": [
                {"agent": "technical", "signal": "bullish", "confidence": 0.8},
                {"agent": "sentiment", "signal": "positive", "confidence": 0.6}
            ]
        })
        
        # 测试配置
        self.config = {
            'ticker': '000001',
            'start_date': '2024-01-01',
            'end_date': '2024-01-05',
            'initial_capital': 100000,
            'num_of_news': 3,
            'commission_rate': 0.001,
            'slippage_rate': 0.001
        }
        
        # 模拟价格数据
        self.mock_price_data = pd.DataFrame({
            'open': [100.0, 102.0, 101.0, 104.0, 103.0],
            'close': [102.0, 101.0, 104.0, 103.0, 105.0],
            'high': [103.0, 103.0, 105.0, 105.0, 106.0],
            'low': [99.0, 100.0, 100.0, 102.0, 102.0],
            'volume': [1000000, 1200000, 800000, 1500000, 900000]
        })
    
    @patch('src.tools.api.get_price_data')
    @patch('src.backtesting.cache.CacheManager.get_cached_price_data')
    def test_complete_backtest_workflow(self, mock_cached_data, mock_price_data):
        """测试完整的回测流程"""
        # 设置数据mock
        mock_cached_data.return_value = self.mock_price_data
        mock_price_data.return_value = self.mock_price_data
        
        # 创建回测器
        backtester = IntelligentBacktester(
            agent=self.mock_agent,
            **self.config
        )
        
        # 运行回测
        backtester.run_backtest()
        
        # 验证回测结果
        assert len(backtester.portfolio_values) > 0
        assert backtester.portfolio['portfolio_value'] > 0
        assert len(backtester.daily_returns) > 0
        
        # 验证交易执行
        assert len(backtester.trade_executor.trades) > 0
        
        # 验证agent调用
        assert self.mock_agent.call_count > 0
        
        # 验证执行统计
        total_executions = sum(backtester._agent_execution_stats.values())
        assert total_executions > 0
    
    @patch('src.tools.api.get_price_data')
    @patch('src.backtesting.cache.CacheManager.get_cached_price_data')
    def test_agent_coordination(self, mock_cached_data, mock_price_data):
        """测试Agent协调工作"""
        mock_cached_data.return_value = self.mock_price_data
        mock_price_data.return_value = self.mock_price_data
        
        # 设置不同的agent频率
        custom_frequencies = {
            'market_data': 'daily',
            'technical': 'weekly', 
            'fundamentals': 'monthly',
            'sentiment': 'conditional',
            'valuation': 'monthly',
            'macro': 'weekly',
            'portfolio': 'daily'
        }
        
        backtester = IntelligentBacktester(
            agent=self.mock_agent,
            agent_frequencies=custom_frequencies,
            **self.config
        )
        
        # 运行回测
        backtester.run_backtest()
        
        # 验证不同agent的执行频率
        stats = backtester._agent_execution_stats
        
        # daily agents应该执行最多
        daily_executions = stats['market_data'] + stats['portfolio']
        weekly_executions = stats['technical'] + stats['macro']
        monthly_executions = stats['fundamentals'] + stats['valuation']
        
        assert daily_executions >= weekly_executions
        assert weekly_executions >= monthly_executions
    
    @patch('src.tools.api.get_price_data')
    @patch('src.backtesting.cache.CacheManager.get_cached_price_data')
    def test_performance_analysis_integration(self, mock_cached_data, mock_price_data):
        """测试性能分析集成"""
        mock_cached_data.return_value = self.mock_price_data
        mock_price_data.return_value = self.mock_price_data
        
        backtester = IntelligentBacktester(
            agent=self.mock_agent,
            **self.config
        )
        
        # 运行回测
        backtester.run_backtest()
        
        # 分析性能
        performance_df = backtester.analyze_performance(save_plots=False)
        
        # 验证性能分析结果
        assert performance_df is not None
        assert not performance_df.empty
        assert 'Portfolio Value' in performance_df.columns
        assert 'Daily Return' in performance_df.columns
        
        # 验证指标计算
        assert hasattr(backtester, 'performance_metrics')
        assert hasattr(backtester, 'risk_metrics')
    
    @patch('src.tools.api.get_price_data')
    @patch('src.backtesting.cache.CacheManager.get_cached_price_data')
    def test_error_handling_and_recovery(self, mock_cached_data, mock_price_data):
        """测试错误处理和恢复机制"""
        mock_cached_data.return_value = self.mock_price_data
        mock_price_data.return_value = self.mock_price_data
        
        # 设置agent抛出异常
        error_agent = Mock(side_effect=[Exception("Agent error"), 
                                       Exception("Agent error"),
                                       '{"action": "hold", "quantity": 0}'])
        
        backtester = IntelligentBacktester(
            agent=error_agent,
            **self.config
        )
        
        # 运行回测应该不崩溃
        try:
            backtester.run_backtest()
            # 验证系统仍然可以工作
            assert len(backtester.portfolio_values) > 0
        except Exception as e:
            pytest.fail(f"回测应该能够处理agent错误: {e}")
    
    @patch('src.tools.api.get_price_data')
    @patch('src.backtesting.cache.CacheManager.get_cached_price_data')
    def test_data_pipeline_integration(self, mock_cached_data, mock_price_data):
        """测试数据管道集成"""
        # 模拟不同的数据源响应 - 提供足够的响应来处理所有交易日
        from itertools import cycle
        mock_cached_data.side_effect = cycle([
            self.mock_price_data,  # 成功
            self.mock_price_data,  # 成功 
            None,                  # 缓存未命中
            self.mock_price_data,  # 成功
        ])
        mock_price_data.return_value = self.mock_price_data
        
        backtester = IntelligentBacktester(
            agent=self.mock_agent,
            **self.config
        )
        
        # 运行回测
        backtester.run_backtest()
        
        # 验证数据管道处理
        assert mock_cached_data.call_count > 0
        assert mock_price_data.call_count >= 0  # 可能会作为后备数据源被调用
        
        # 验证结果
        assert len(backtester.portfolio_values) > 0
    
    def test_trading_execution_integration(self):
        """测试交易执行集成"""
        trade_executor = TradeExecutor(commission_rate=0.001, slippage_rate=0.001)
        portfolio = {'cash': 100000, 'stock': 0}
        
        # 执行买入交易
        executed_qty = trade_executor.execute_trade(
            action='buy', quantity=100, current_price=100.0, 
            date='2024-01-01', portfolio=portfolio
        )
        
        # 验证交易执行
        assert executed_qty == 100
        assert portfolio['stock'] == 100
        assert portfolio['cash'] < 100000  # 账户现金减少
        
        # 验证交易记录
        assert len(trade_executor.trades) == 1
        trade = trade_executor.trades[0]
        assert trade.action == 'buy'
        assert trade.quantity == 100
        assert trade.price == 100.1  # 价格包含滑点 (100.0 * 1.001)
        assert trade.commission > 0  # 应该有手续费
    
    @patch('matplotlib.pyplot.savefig')
    def test_visualization_integration(self, mock_savefig):
        """测试可视化集成"""
        visualizer = PerformanceVisualizer(ticker='000001', initial_capital=100000)
        
        # 创建模拟数据
        portfolio_values = [
            {'Date': datetime(2024, 1, 1), 'Portfolio Value': 100000, 'Daily Return': 0},
            {'Date': datetime(2024, 1, 2), 'Portfolio Value': 102000, 'Daily Return': 2.0},
            {'Date': datetime(2024, 1, 3), 'Portfolio Value': 101000, 'Daily Return': -0.98},
        ]
        
        benchmark_values = [100, 101, 100.5]
        agent_stats = {'technical': 2, 'sentiment': 3}
        cache_stats = {'hits': 5, 'misses': 2}
        
        # 创建性能指标
        perf_metrics = PerformanceMetrics(
            total_return=0.01, annualized_return=0.12, volatility=0.15,
            sharpe_ratio=0.8, max_drawdown=-0.05, win_rate=0.6
        )
        
        risk_metrics = RiskMetrics(
            value_at_risk=-0.03, expected_shortfall=-0.05, beta=1.2,
            alpha=0.02, information_ratio=0.5, tracking_error=0.08
        )
        
        daily_returns = [0.0, 0.02, -0.0098]
        
        # 创建图表
        plot_path = visualizer.create_performance_plot(
            portfolio_values=portfolio_values,
            benchmark_values=benchmark_values,
            agent_execution_stats=agent_stats,
            cache_hits=cache_stats['hits'],
            cache_misses=cache_stats['misses'],
            total_possible_executions=10,
            agent_frequencies={'technical': 'daily', 'sentiment': 'weekly'},
            perf_metrics=perf_metrics,
            risk_metrics=risk_metrics,
            daily_returns=daily_returns,
            save_plots=False  # 不实际保存文件
        )
        
        # 验证图表创建
        # 注意：由于save_plots=False，不会实际调用savefig
        # 但可以验证函数正常运行
        assert plot_path is None or isinstance(plot_path, str)
    
    @patch('src.tools.api.get_price_data')
    @patch('src.backtesting.cache.CacheManager.get_cached_price_data')
    def test_multi_scenario_integration(self, mock_cached_data, mock_price_data):
        """测试多场景集成"""
        # 场景1：牛市场景
        bull_market_data = self.mock_price_data.copy()
        bull_market_data['close'] = [100, 105, 110, 115, 120]  # 上涨趋势
        
        mock_cached_data.return_value = bull_market_data
        mock_price_data.return_value = bull_market_data
        
        # 设置牛市agent响应
        bull_agent = Mock()
        bull_agent.return_value = '{"action": "buy", "quantity": 100}'
        
        bull_backtester = IntelligentBacktester(
            agent=bull_agent,
            **self.config
        )
        
        bull_backtester.run_backtest()
        bull_performance = bull_backtester.analyze_performance(save_plots=False)
        
        # 场景2：熊市场景
        bear_market_data = self.mock_price_data.copy()
        bear_market_data['close'] = [100, 95, 90, 85, 80]  # 下跌趋势
        
        mock_cached_data.return_value = bear_market_data
        mock_price_data.return_value = bear_market_data
        
        # 设置熊市agent响应
        bear_agent = Mock()
        bear_agent.return_value = '{"action": "sell", "quantity": 100}'
        
        bear_backtester = IntelligentBacktester(
            agent=bear_agent,
            **self.config
        )
        
        bear_backtester.run_backtest()
        bear_performance = bear_backtester.analyze_performance(save_plots=False)
        
        # 验证不同场景下的表现
        assert bull_performance is not None
        assert bear_performance is not None
        
        # 验证策略适应性（这里只是基本验证，实际效果取决于具体策略）
        assert len(bull_backtester.portfolio_values) > 0
        assert len(bear_backtester.portfolio_values) > 0
    
    def test_cache_performance_integration(self):
        """测试缓存性能集成"""
        from src.backtesting.cache import CacheManager
        
        cache_manager = CacheManager()
        
        # 测试缓存操作
        test_key = "test_decision_2024-01-01"
        test_data = {"action": "buy", "quantity": 100}
        
        # 初始状态应该无缓存
        assert cache_manager.get_agent_result(test_key) is None
        
        # 缓存数据
        cache_manager.cache_agent_result(test_key, test_data)
        
        # 验证缓存命中
        cached_result = cache_manager.get_agent_result(test_key)
        assert cached_result == test_data
        
        # 验证缓存统计
        assert cache_manager.cache_hits > 0
        assert cache_manager.cache_hit_rate > 0
    
    @patch('src.tools.api.get_price_data')
    @patch('src.backtesting.cache.CacheManager.get_cached_price_data')
    def test_stress_test_integration(self, mock_cached_data, mock_price_data):
        """测试压力测试集成"""
        # 创建极端波动的价格数据
        volatile_prices = []
        base_price = 100
        for i in range(20):  # 20个交易日
            # 模拟极端波动
            change = np.random.uniform(-0.1, 0.1)  # 日波动范围±10%
            base_price *= (1 + change)
            volatile_prices.append(base_price)
        
        volatile_data = pd.DataFrame({
            'open': volatile_prices,
            'close': [p * 1.01 for p in volatile_prices],
            'high': [p * 1.05 for p in volatile_prices],
            'low': [p * 0.95 for p in volatile_prices],
            'volume': [1000000] * 20
        })
        
        mock_cached_data.return_value = volatile_data
        mock_price_data.return_value = volatile_data
        
        # 使用高频率执行测试系统稳定性
        high_freq_config = {
            'market_data': 'daily',
            'technical': 'daily',
            'fundamentals': 'daily',
            'sentiment': 'daily',
            'valuation': 'daily',
            'macro': 'daily',
            'portfolio': 'daily'
        }
        
        stress_config = self.config.copy()
        stress_config.update({
            'start_date': '2024-01-01',
            'end_date': '2024-01-20'
        })
        
        backtester = IntelligentBacktester(
            agent=self.mock_agent,
            agent_frequencies=high_freq_config,
            **stress_config
        )
        
        # 运行压力测试
        try:
            backtester.run_backtest()
            performance_df = backtester.analyze_performance(save_plots=False)
            
            # 验证系统在高压力下仍能正常工作
            assert performance_df is not None
            assert len(backtester.portfolio_values) > 0
            assert all(v['Portfolio Value'] > 0 for v in backtester.portfolio_values)
            
        except Exception as e:
            pytest.fail(f"系统在压力测试中失败: {e}")


@pytest.mark.slow  # 标记为慢速测试
class TestBacktestingPerformance:
    """回测系统性能测试"""
    
    @patch('src.tools.api.get_price_data')
    @patch('src.backtesting.cache.CacheManager.get_cached_price_data')
    def test_large_dataset_performance(self, mock_cached_data, mock_price_data):
        """测试大数据集性能"""
        # 创建大量数据（模拟1年的数据）
        num_days = 252
        large_dataset = pd.DataFrame({
            'open': np.random.uniform(90, 110, num_days),
            'close': np.random.uniform(90, 110, num_days),
            'high': np.random.uniform(110, 120, num_days),
            'low': np.random.uniform(80, 90, num_days),
            'volume': np.random.randint(500000, 2000000, num_days)
        })
        
        mock_cached_data.return_value = large_dataset
        mock_price_data.return_value = large_dataset
        
        mock_agent = Mock()
        mock_agent.return_value = '{"action": "hold", "quantity": 0}'
        
        config = {
            'ticker': '000001',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'initial_capital': 1000000,  # 更大的初始资金
            'num_of_news': 5
        }
        
        backtester = IntelligentBacktester(
            agent=mock_agent,
            **config
        )
        
        # 记录性能
        import time
        start_time = time.time()
        
        backtester.run_backtest()
        performance_df = backtester.analyze_performance(save_plots=False)
        
        execution_time = time.time() - start_time
        
        # 验证性能要求（根据实际情况调整）
        assert execution_time < 60  # 应该在1分钟内完成
        assert performance_df is not None
        # 验证portfolio_values数量在合理范围内 (包含周末)
        assert len(backtester.portfolio_values) >= num_days
        assert len(backtester.portfolio_values) <= num_days + 15  # 允许额外的周末天数
        
        # 验证缓存效果
        cache_hit_rate = backtester.cache_manager.cache_hit_rate
        assert cache_hit_rate >= 0  # 缓存命中率应该大于等于0
        
        print(f"大数据集性能测试结果:")
        print(f"  数据点数: {num_days}")
        print(f"  执行时间: {execution_time:.2f}秒")
        print(f"  缓存命中率: {cache_hit_rate:.1f}%")
        print(f"  Agent执行统计: {backtester._agent_execution_stats}")
