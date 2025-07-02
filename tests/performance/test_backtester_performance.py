"""
回测系统性能测试模块

测试回测器在各种性能场景下的表现，包括：
- 大规模数据处理性能
- 内存使用效率
- 计算密集型操作性能
- 并发处理能力
- 长时间运行稳定性
"""

import pytest
import time
import psutil
import os
import gc
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
import threading
from concurrent.futures import ThreadPoolExecutor
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.backtester import Backtester


class TestBacktesterPerformance:
    """回测器性能测试"""
    
    @pytest.fixture
    def mock_agent(self):
        """创建模拟智能体"""
        agent = Mock()
        agent.return_value = '{"action": "hold", "quantity": 0}'
        return agent
        
    @pytest.fixture
    def performance_monitor(self):
        """性能监控器"""
        class PerformanceMonitor:
            def __init__(self):
                self.start_time = None
                self.start_memory = None
                self.process = psutil.Process()
                
            def start(self):
                gc.collect()  # 清理垃圾回收
                self.start_time = time.time()
                self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
                
            def stop(self, operation_name="operation"):
                end_time = time.time()
                end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
                
                execution_time = end_time - self.start_time
                memory_usage = end_memory - self.start_memory
                
                print(f"\n{operation_name} 性能指标:")
                print(f"  执行时间: {execution_time:.3f} 秒")
                print(f"  内存使用: {memory_usage:.2f} MB")
                print(f"  峰值内存: {end_memory:.2f} MB")
                
                return execution_time, memory_usage
                
        return PerformanceMonitor()
    
    @pytest.mark.performance
    def test_initialization_performance(self, mock_agent, performance_monitor):
        """测试初始化性能"""
        performance_monitor.start()
        
        # 创建多个回测器实例
        backtester_instances = []
        for i in range(100):
            backtester = Backtester(
                agent=mock_agent,
                ticker="000001",
                start_date="2024-01-01",
                end_date="2024-01-31",
                initial_capital=100000,
                num_of_news=5
            )
            backtester_instances.append(backtester)
            
        execution_time, memory_usage = performance_monitor.stop("回测器初始化(100个实例)")
        
        # 性能要求
        assert execution_time < 2.0, f"初始化时间过长: {execution_time:.3f}s"
        assert memory_usage < 100, f"内存使用过高: {memory_usage:.2f}MB"
        
    @pytest.mark.performance
    def test_large_dataset_processing(self, mock_agent, performance_monitor):
        """测试大数据集处理性能"""
        backtester = Backtester(
            agent=mock_agent,
            ticker="000001",
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=100000,
            num_of_news=5
        )
        
        performance_monitor.start()
        
        # 模拟添加大量组合价值数据
        large_dataset_size = 10000
        dates = pd.date_range("2024-01-01", periods=large_dataset_size, freq="H")
        
        for i, date in enumerate(dates):
            portfolio_value = 100000 * (1 + np.random.normal(0, 0.001))
            daily_return = np.random.normal(0, 0.01)
            
            backtester.portfolio_values.append({
                "Date": date,
                "Portfolio Value": portfolio_value,
                "Daily Return": daily_return
            })
            backtester.daily_returns.append(daily_return)
            
        backtester.portfolio["portfolio_value"] = backtester.portfolio_values[-1]["Portfolio Value"]
        
        # 计算性能指标
        performance_metrics = backtester.calculate_performance_metrics()
        risk_metrics = backtester.calculate_risk_metrics()
        
        execution_time, memory_usage = performance_monitor.stop(f"大数据集处理({large_dataset_size}条记录)")
        
        # 性能要求
        assert execution_time < 5.0, f"大数据集处理时间过长: {execution_time:.3f}s"
        assert memory_usage < 200, f"内存使用过高: {memory_usage:.2f}MB"
        assert performance_metrics is not None
        assert risk_metrics is not None
        
    @pytest.mark.performance
    def test_trade_execution_performance(self, mock_agent, performance_monitor):
        """测试交易执行性能"""
        backtester = Backtester(
            agent=mock_agent,
            ticker="000001",
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=1000000,  # 更大的初始资金
            num_of_news=5
        )
        
        performance_monitor.start()
        
        # 执行大量交易
        num_trades = 1000
        current_price = 10.0
        
        for i in range(num_trades):
            action = "buy" if i % 2 == 0 else "sell"
            quantity = 100
            date = f"2024-01-{(i % 28) + 1:02d}"
            
            backtester.execute_trade(action, quantity, current_price, date)
            current_price *= (1 + np.random.normal(0, 0.001))  # 价格随机变动
            
        execution_time, memory_usage = performance_monitor.stop(f"交易执行({num_trades}笔交易)")
        
        # 性能要求
        assert execution_time < 3.0, f"交易执行时间过长: {execution_time:.3f}s"
        assert len(backtester.trades) <= num_trades  # 一些交易可能因资金不足失败
        
    @pytest.mark.performance
    def test_memory_efficiency_during_long_backtest(self, mock_agent, performance_monitor):
        """测试长期回测的内存效率"""
        backtester = Backtester(
            agent=mock_agent,
            ticker="000001",
            start_date="2024-01-01",
            end_date="2024-12-31",  # 一年的回测
            initial_capital=100000,
            num_of_news=5
        )
        
        performance_monitor.start()
        
        # 模拟长期回测数据积累
        dates = pd.date_range("2024-01-01", "2024-12-31", freq="D")
        
        for date in dates:
            portfolio_value = 100000 * (1 + np.random.normal(0, 0.01))
            daily_return = np.random.normal(0, 0.01)
            
            backtester.portfolio_values.append({
                "Date": date,
                "Portfolio Value": portfolio_value,
                "Daily Return": daily_return
            })
            
            # 模拟交易记录
            if np.random.random() < 0.1:  # 10%概率执行交易
                backtester.execute_trade("buy", 100, 10.0, date.strftime("%Y-%m-%d"))
                
        execution_time, memory_usage = performance_monitor.stop("长期回测内存效率")
        
        # 内存使用应该在合理范围内
        assert memory_usage < 300, f"长期回测内存使用过高: {memory_usage:.2f}MB"
        assert len(backtester.portfolio_values) == len(dates)
        
    @pytest.mark.performance
    def test_concurrent_backtester_creation(self, mock_agent, performance_monitor):
        """测试并发创建回测器的性能"""
        performance_monitor.start()
        
        def create_backtester(index):
            """创建单个回测器"""
            return Backtester(
                agent=mock_agent,
                ticker=f"{index:06d}",
                start_date="2024-01-01",
                end_date="2024-01-31",
                initial_capital=100000,
                num_of_news=5
            )
        
        # 并发创建多个回测器
        num_threads = 10
        num_instances_per_thread = 5
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for i in range(num_threads * num_instances_per_thread):
                future = executor.submit(create_backtester, i)
                futures.append(future)
                
            # 等待所有任务完成
            results = []
            for future in futures:
                try:
                    result = future.result(timeout=10)
                    results.append(result)
                except Exception as e:
                    pytest.fail(f"并发创建回测器失败: {e}")
                    
        execution_time, memory_usage = performance_monitor.stop(f"并发创建回测器({len(results)}个)")
        
        # 性能要求
        assert execution_time < 5.0, f"并发创建时间过长: {execution_time:.3f}s"
        assert len(results) == num_threads * num_instances_per_thread
        
    @pytest.mark.performance
    def test_performance_calculation_scaling(self, mock_agent, performance_monitor):
        """测试性能计算的扩展性"""
        backtester = Backtester(
            agent=mock_agent,
            ticker="000001",
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=100000,
            num_of_news=5
        )
        
        # 测试不同数据量下的性能计算时间
        data_sizes = [100, 500, 1000, 5000]
        execution_times = []
        
        for size in data_sizes:
            # 重置数据
            backtester.portfolio_values = []
            backtester.daily_returns.clear()
            backtester.trades = []
            
            # 生成测试数据
            dates = pd.date_range("2024-01-01", periods=size, freq="H")
            for date in dates:
                portfolio_value = 100000 * (1 + np.random.normal(0, 0.001))
                daily_return = np.random.normal(0, 0.01)
                
                backtester.portfolio_values.append({
                    "Date": date,
                    "Portfolio Value": portfolio_value,
                    "Daily Return": daily_return
                })
                backtester.daily_returns.append(daily_return)
                
            backtester.portfolio["portfolio_value"] = backtester.portfolio_values[-1]["Portfolio Value"]
            
            # 测量性能计算时间
            start_time = time.time()
            performance_metrics = backtester.calculate_performance_metrics()
            risk_metrics = backtester.calculate_risk_metrics()
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            print(f"数据量 {size}: {execution_time:.3f}s")
            
            # 每个数据量的性能要求
            assert execution_time < 2.0, f"数据量{size}时性能计算时间过长: {execution_time:.3f}s"
            assert performance_metrics is not None
            assert risk_metrics is not None
            
        # 检查扩展性（时间复杂度应该接近线性）
        if len(execution_times) >= 4:
            # 最大数据量的时间不应该超过最小数据量时间的合理倍数
            time_ratio = execution_times[-1] / execution_times[0]
            data_ratio = data_sizes[-1] / data_sizes[0]
            
            # 时间增长应该不超过数据量增长的2倍（允许一定的非线性）
            assert time_ratio <= data_ratio * 2, f"性能扩展性不佳: 时间比率{time_ratio:.2f}, 数据比率{data_ratio:.2f}"
            
    @pytest.mark.performance  
    def test_agent_decision_processing_performance(self, mock_agent, performance_monitor):
        """测试智能体决策处理性能"""
        backtester = Backtester(
            agent=mock_agent,
            ticker="000001",
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=100000,
            num_of_news=5
        )
        
        # 模拟不同复杂度的决策响应
        complex_decisions = [
            '{"action": "buy", "quantity": 100}',
            '{"action": "sell", "quantity": 200, "reason": "市场风险增加"}',
            '{"action": "hold", "quantity": 0, "agent_signals": [{"agent": "technical", "signal": "neutral", "confidence": 0.5}]}',
            '''{"action": "buy", "quantity": 500, "agent_signals": [
                {"agent": "technical", "signal": "bullish", "confidence": 0.8},
                {"agent": "fundamental", "signal": "bullish", "confidence": 0.7}
            ], "reason": "多重信号确认"}'''
        ]
        
        performance_monitor.start()
        
        # 处理大量决策
        num_decisions = 1000
        for i in range(num_decisions):
            decision_json = complex_decisions[i % len(complex_decisions)]
            mock_agent.return_value = decision_json
            
            result = backtester.get_agent_decision(
                "2024-01-01", 
                "2023-12-01", 
                backtester.portfolio
            )
            
            assert result is not None
            assert "decision" in result
            
        execution_time, memory_usage = performance_monitor.stop(f"智能体决策处理({num_decisions}次)")
        
        # 性能要求
        assert execution_time < 3.0, f"决策处理时间过长: {execution_time:.3f}s"
        assert memory_usage < 100, f"决策处理内存使用过高: {memory_usage:.2f}MB"


class TestBacktesterStressTest:
    """回测器压力测试"""
    
    @pytest.fixture
    def mock_agent(self):
        """创建模拟智能体"""
        agent = Mock()
        agent.return_value = '{"action": "hold", "quantity": 0}'
        return agent
    
    @pytest.mark.stress
    def test_extreme_data_volume_handling(self, mock_agent):
        """测试极大数据量处理"""
        backtester = Backtester(
            agent=mock_agent,
            ticker="000001",
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=100000,
            num_of_news=5
        )
        
        # 生成极大数据集
        extreme_size = 50000
        start_time = time.time()
        
        try:
            dates = pd.date_range("2020-01-01", periods=extreme_size, freq="T")  # 分钟级数据
            
            for i, date in enumerate(dates):
                if i % 10000 == 0:  # 进度报告
                    print(f"处理进度: {i}/{extreme_size}")
                    
                portfolio_value = 100000 * (1 + np.random.normal(0, 0.0001))
                daily_return = np.random.normal(0, 0.001)
                
                backtester.portfolio_values.append({
                    "Date": date,
                    "Portfolio Value": portfolio_value,
                    "Daily Return": daily_return
                })
                backtester.daily_returns.append(daily_return)
                
            backtester.portfolio["portfolio_value"] = backtester.portfolio_values[-1]["Portfolio Value"]
            
            # 尝试计算性能指标
            performance_metrics = backtester.calculate_performance_metrics()
            
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"极大数据量处理完成: {total_time:.2f}s")
            assert performance_metrics is not None
            assert len(backtester.portfolio_values) == extreme_size
            
        except MemoryError:
            pytest.skip("内存不足，跳过极大数据量测试")
        
    @pytest.mark.stress
    def test_long_running_stability(self, mock_agent):
        """测试长时间运行稳定性"""
        backtester = Backtester(
            agent=mock_agent,
            ticker="000001",
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=100000,
            num_of_news=5
        )
        
        # 长时间运行测试
        start_time = time.time()
        iterations = 1000  # 减少迭代次数
        
        for i in range(iterations):
            if i % 200 == 0:
                print(f"长时间运行测试进度: {i}/{iterations}")
                
            # 模拟各种操作
            backtester.execute_trade("buy", 100, 10.0 + np.random.normal(0, 0.1), f"2024-01-01")
            backtester.execute_trade("sell", 50, 10.0 + np.random.normal(0, 0.1), f"2024-01-01")
            
            # 添加组合价值记录
            portfolio_value = 100000 * (1 + np.random.normal(0, 0.01))
            backtester.portfolio_values.append({
                "Date": datetime.now(),
                "Portfolio Value": portfolio_value,
                "Daily Return": np.random.normal(0, 0.01)
            })
            
            # 定期清理以防止内存泄漏
            if i % 200 == 0:
                gc.collect()
                
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"长时间运行测试完成: {total_time:.2f}s")
        assert len(backtester.trades) > 0
        assert len(backtester.portfolio_values) > 0
        
    @pytest.mark.stress
    def test_resource_cleanup_on_error(self, mock_agent):
        """测试错误情况下的资源清理"""
        def create_and_destroy_backtester():
            try:
                backtester = Backtester(
                    agent=mock_agent,
                    ticker="000001",
                    start_date="2024-01-01",
                    end_date="2024-01-31",
                    initial_capital=100000,
                    num_of_news=5
                )
                
                # 人为制造异常
                raise Exception("模拟异常")
                
            except Exception:
                # 确保异常被正确捕获
                pass
            finally:
                # 强制垃圾回收
                gc.collect()
                
        # 重复创建和销毁，检查内存泄漏
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        for i in range(100):
            create_and_destroy_backtester()
            
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        print(f"内存增长: {memory_increase:.2f}MB")
        
        # 内存增长应该在合理范围内
        assert memory_increase < 50, f"可能存在内存泄漏: {memory_increase:.2f}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])