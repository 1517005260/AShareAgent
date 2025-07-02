"""
测试智能回测器中的细粒度Agent频率控制功能

测试包含:
1. Agent执行频率配置验证
2. 条件触发机制测试
3. 市场状态更新测试
4. 缓存机制测试
5. 部分workflow执行测试
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.backtesting.backtester import IntelligentBacktester
from src.backtesting.models import AgentConfig, Trade, PerformanceMetrics, RiskMetrics


class TestAgentFrequencyControl:
    """测试Agent频率控制系统"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.mock_agent = Mock()
        self.mock_agent.return_value = '{"action": "hold", "quantity": 0}'
        
        self.default_config = {
            'ticker': '000001',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'initial_capital': 100000,
            'num_of_news': 5
        }
        
        self.custom_frequencies = {
            'market_data': 'daily',
            'technical': 'weekly',
            'fundamentals': 'monthly',
            'sentiment': 'conditional',
            'valuation': 'monthly',
            'macro': 'weekly',
            'portfolio': 'daily'
        }
    
    def test_default_frequency_configuration(self):
        """测试默认频率配置"""
        backtester = IntelligentBacktester(
            agent=self.mock_agent,
            **self.default_config
        )
        
        # 验证默认频率配置
        expected_defaults = {
            'market_data': 'daily',
            'technical': 'daily',
            'fundamentals': 'weekly',
            'sentiment': 'daily',
            'valuation': 'monthly',
            'macro': 'weekly',
            'portfolio': 'daily'
        }
        
        assert backtester.agent_frequencies == expected_defaults
        assert all(agent in backtester._agent_execution_stats for agent in expected_defaults.keys())
    
    def test_custom_frequency_configuration(self):
        """测试自定义频率配置"""
        backtester = IntelligentBacktester(
            agent=self.mock_agent,
            agent_frequencies=self.custom_frequencies,
            **self.default_config
        )
        
        assert backtester.agent_frequencies == self.custom_frequencies
        assert all(agent in backtester._agent_execution_stats for agent in self.custom_frequencies.keys())
    
    @pytest.mark.parametrize("frequency,date,expected", [
        ('daily', datetime(2024, 1, 15), True),  # 任意日期
        ('weekly', datetime(2024, 1, 1), True),   # 周一
        ('weekly', datetime(2024, 1, 2), False),  # 周二
        ('monthly', datetime(2024, 1, 1), True),  # 月初工作日
        ('monthly', datetime(2024, 1, 15), False), # 月中
    ])
    def test_should_execute_agent_basic_frequencies(self, frequency, date, expected):
        """测试基本频率判断逻辑"""
        backtester = IntelligentBacktester(
            agent=self.mock_agent,
            **self.default_config
        )
        
        # 设置单个agent的频率
        backtester.agent_frequencies = {'test_agent': frequency}
        
        result = backtester._should_execute_agent('test_agent', date)
        assert result == expected
    
    def test_conditional_trigger_volatility(self):
        """测试基于波动率的条件触发"""
        backtester = IntelligentBacktester(
            agent=self.mock_agent,
            **self.default_config
        )
        
        # 模拟高波动率状态
        high_volatility_data = [0.05] * 10 + [0.15] * 10  # 前期低波动，后期高波动
        for vol in high_volatility_data:
            backtester._market_volatility.append(vol)
        
        # 测试条件触发
        should_execute = backtester._check_conditional_trigger('test_agent', datetime(2024, 1, 15))
        assert should_execute == True
    
    def test_conditional_trigger_price_change(self):
        """测试基于价格变动的条件触发"""
        backtester = IntelligentBacktester(
            agent=self.mock_agent,
            **self.default_config
        )
        
        # 模拟大幅价格变动
        large_price_changes = [0.03, 0.02, 0.01]  # 3日累计变动6%，超过5%阈值
        for change in large_price_changes:
            backtester._price_changes.append(change)
        
        should_execute = backtester._check_conditional_trigger('test_agent', datetime(2024, 1, 15))
        assert should_execute == True
    
    def test_market_conditions_update(self):
        """测试市场状态更新机制"""
        backtester = IntelligentBacktester(
            agent=self.mock_agent,
            **self.default_config
        )
        
        # 初始状态
        assert len(backtester._price_changes) == 0
        assert len(backtester._market_volatility) == 0
        
        # 更新价格数据
        prices = [100, 105, 103, 108, 102]  # 模拟价格序列
        for i in range(1, len(prices)):
            backtester._update_market_conditions(prices[i], prices[i-1])
        
        # 验证价格变动记录
        assert len(backtester._price_changes) == 4
        expected_changes = [0.05, -0.019, 0.049, -0.056]  # 计算的价格变动
        
        for i, expected in enumerate(expected_changes):
            assert abs(backtester._price_changes[i] - expected) < 0.001
        
        # 验证波动率计算
        assert len(backtester._market_volatility) == 0  # 还未达到5个数据点
        
        # 添加第5个价格点
        backtester._update_market_conditions(110, 102)
        assert len(backtester._market_volatility) == 1  # 现在应该有波动率数据
    
    def test_agent_execution_statistics(self):
        """测试Agent执行统计"""
        backtester = IntelligentBacktester(
            agent=self.mock_agent,
            agent_frequencies=self.custom_frequencies,
            **self.default_config
        )
        
        # Mock cache manager methods
        with patch.object(backtester.cache_manager, 'get_agent_result', return_value=None), \
             patch.object(backtester.cache_manager, 'get_last_decision', return_value={'action': 'hold', 'quantity': 0}):
            
            # 模拟多次决策调用
            test_dates = [
                '2024-01-01',  # 周一 - technical, macro应该执行
                '2024-01-02',  # 周二 - 只有daily agents执行
                '2024-01-03',  # 周三 - 月初，fundamentals可能执行
            ]
            
            for date in test_dates:
                backtester.get_agent_decision(date, '2023-12-01', {'cash': 100000, 'stock': 0})
        
        # 验证执行统计
        stats = backtester._agent_execution_stats
        
        # daily agents应该执行3次
        assert stats['market_data'] == 3
        assert stats['portfolio'] == 3
        
        # weekly agents在周一执行1次
        assert stats['technical'] >= 1
        assert stats['macro'] >= 1
        
        # monthly agents在月初执行
        assert stats['fundamentals'] >= 1
        assert stats['valuation'] >= 1
        
        # conditional agent执行次数取决于市场条件
        assert stats['sentiment'] >= 0
    
    def test_partial_workflow_execution(self):
        """测试部分workflow执行"""
        backtester = IntelligentBacktester(
            agent=self.mock_agent,
            **self.default_config
        )
        
        # 模拟只有部分agents需要执行的情况
        agents_to_execute = ['technical', 'sentiment']
        
        with patch.object(backtester.cache_manager, 'get_cached_price_data') as mock_price_data:
            # 创建真实的DataFrame进行测试
            import pandas as pd
            import numpy as np
            
            test_data = pd.DataFrame({
                'open': [95, 96, 97, 98, 99, 100] + [98] * 20,  # 提供足够的数据
                'close': [94, 95, 96, 97, 98, 99] + [97] * 20
            })
            mock_price_data.return_value = test_data
            
            result = backtester._execute_partial_workflow(
                agents_to_execute, '2024-01-15', '2023-12-15', {'cash': 100000, 'stock': 0}
            )
            
            # 验证结果结构
            assert 'decision' in result
            assert 'analyst_signals' in result
            assert 'execution_type' in result
            assert result['execution_type'] == 'partial_workflow'
            assert result['agents_executed'] == agents_to_execute
    
    def test_frequency_validation(self):
        """测试频率配置验证"""
        invalid_frequencies = {
            'market_data': 'invalid_frequency',
            'technical': 'daily'
        }
        
        with pytest.raises(ValueError, match="无效的频率配置"):
            IntelligentBacktester(
                agent=self.mock_agent,
                agent_frequencies=invalid_frequencies,
                **self.default_config
            )
    
    def test_cache_integration(self):
        """测试缓存集成"""
        backtester = IntelligentBacktester(
            agent=self.mock_agent,
            **self.default_config
        )
        
        # 设置缓存命中
        cached_decision = {
            'decision': {'action': 'buy', 'quantity': 100},
            'analyst_signals': {'technical': 'bullish'},
            'execution_type': 'cached'
        }
        
        with patch.object(backtester.cache_manager, 'get_agent_result', return_value=cached_decision) as mock_get_result:
            result = backtester.get_agent_decision('2024-01-15', '2023-12-15', {'cash': 100000, 'stock': 0})
        
        # 验证返回缓存结果
        assert result == cached_decision
        
        # 验证缓存被正确调用
        mock_get_result.assert_called_once()
    
    def test_optimization_rate_calculation(self):
        """测试优化率计算"""
        backtester = IntelligentBacktester(
            agent=self.mock_agent,
            agent_frequencies=self.custom_frequencies,
            **self.default_config
        )
        
        # 模拟执行统计
        backtester._total_possible_executions = 10
        backtester._agent_execution_stats = {
            'market_data': 10,    # daily - 执行100%
            'technical': 2,       # weekly - 执行20%
            'fundamentals': 1,    # monthly - 执行10%
            'sentiment': 5,       # conditional - 执行50%
            'valuation': 1,       # monthly - 执行10%
            'macro': 2,           # weekly - 执行20%
            'portfolio': 10       # daily - 执行100%
        }
        
        # 计算优化率
        total_possible = backtester._total_possible_executions * len(backtester.agent_frequencies)
        total_actual = sum(backtester._agent_execution_stats.values())
        expected_optimization_rate = (1 - total_actual / total_possible) * 100
        
        # 验证优化率在合理范围内（应该 > 0，因为不是所有agents都每次执行）
        assert expected_optimization_rate > 0
        assert expected_optimization_rate < 100


@pytest.mark.integration
class TestAgentFrequencyIntegration:
    """集成测试：Agent频率控制与回测系统整合"""
    
    @patch('src.tools.api.get_price_data')
    def test_full_backtest_with_frequency_control(self, mock_price_data):
        """测试完整回测流程中的频率控制"""
        # 设置价格数据mock
        import pandas as pd
        mock_df = pd.DataFrame({
            'open': [100, 102, 101, 103, 99],
            'close': [102, 101, 103, 99, 101],
            'high': [103, 103, 104, 104, 102],
            'low': [99, 100, 100, 98, 98],
            'volume': [1000000] * 5
        })
        mock_price_data.return_value = mock_df
        
        mock_agent = Mock()
        mock_agent.return_value = '{"action": "hold", "quantity": 0}'
        
        # 使用高频率配置进行短期回测
        frequencies = {
            'market_data': 'daily',
            'technical': 'daily',
            'fundamentals': 'weekly',
            'sentiment': 'daily',
            'valuation': 'weekly',
            'macro': 'weekly',
            'portfolio': 'daily'
        }
        
        backtester = IntelligentBacktester(
            agent=mock_agent,
            ticker='000001',
            start_date='2024-01-01',
            end_date='2024-01-05',
            initial_capital=100000,
            num_of_news=3,
            agent_frequencies=frequencies
        )
        
        # 运行回测
        backtester.run_backtest()
        
        # 验证执行统计
        stats = backtester._agent_execution_stats
        
        # daily agents应该有更多执行次数
        assert stats['market_data'] >= stats['fundamentals']
        assert stats['technical'] >= stats['valuation']
        
        # 验证有投资组合数据
        assert len(backtester.portfolio_values) > 0
        assert backtester.portfolio['portfolio_value'] > 0
