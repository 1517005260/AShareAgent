"""
回测系统性能测试

测试包含:
1. 大数据集性能测试
2. 并发执行测试
3. 内存使用测试
4. 缓存效率测试
5. API调用性能测试
"""

import pytest
import time
import psutil
import threading
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.backtesting.backtester import IntelligentBacktester
from src.backtesting.cache import CacheManager
from src.backtesting.metrics import MetricsCalculator


class TestBacktestingPerformance:
    """回测系统性能测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.mock_agent = Mock()
        self.mock_agent.return_value = '{"action": "hold", "quantity": 0}'
        
        self.performance_thresholds = {
            'max_execution_time': 30,  # 秒
            'max_memory_usage': 500,   # MB
            'min_cache_hit_rate': 20,  # %
            'max_cpu_usage': 80,       # %
        }
    
    @pytest.mark.slow
    def test_large_dataset_performance(self):
        """测试大数据集性能"""
        # 创建1年的数据
        num_days = 252
        large_dataset = self._create_large_dataset(num_days)
        
        with patch('src.backtesting.cache.CacheManager.get_cached_price_data') as mock_data:
            mock_data.return_value = large_dataset
            
            config = {
                'ticker': '000001',
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'initial_capital': 1000000,
                'num_of_news': 5
            }
            
            # 性能监控
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            backtester = IntelligentBacktester(
                agent=self.mock_agent,
                **config
            )
            
            # 运行回测
            backtester.run_backtest()
            
            # 计算性能指标
            execution_time = time.time() - start_time
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_usage = end_memory - start_memory
            
            # 性能断言
            assert execution_time < self.performance_thresholds['max_execution_time'], \
                f"执行时间过长: {execution_time:.2f}s > {self.performance_thresholds['max_execution_time']}s"
            
            assert memory_usage < self.performance_thresholds['max_memory_usage'], \
                f"内存使用过多: {memory_usage:.2f}MB > {self.performance_thresholds['max_memory_usage']}MB"
            
            # 验证结果正确性
            assert len(backtester.portfolio_values) > 0
            assert backtester.portfolio['portfolio_value'] > 0
            
            print(f"\n性能测试结果:")
            print(f"  数据点数: {num_days}")
            print(f"  执行时间: {execution_time:.2f}秒")
            print(f"  内存使用: {memory_usage:.2f}MB")
            print(f"  平均每天: {execution_time/num_days*1000:.2f}ms")
    
    def test_cache_performance(self):
        """测试缓存性能"""
        cache_manager = CacheManager()
        
        # 测试数据
        test_keys = [f"test_key_{i}" for i in range(1000)]
        test_data = {"action": "buy", "quantity": 100}
        
        # 测试缓存写入性能
        start_time = time.time()
        for key in test_keys:
            cache_manager.cache_agent_result(key, test_data)
        write_time = time.time() - start_time
        
        # 测试缓存读取性能
        start_time = time.time()
        hit_count = 0
        for key in test_keys:
            result = cache_manager.get_agent_result(key)
            if result is not None:
                hit_count += 1
        read_time = time.time() - start_time
        
        # 计算指标
        hit_rate = (hit_count / len(test_keys)) * 100
        avg_write_time = write_time / len(test_keys) * 1000  # ms
        avg_read_time = read_time / len(test_keys) * 1000    # ms
        
        # 性能断言
        assert hit_rate >= self.performance_thresholds['min_cache_hit_rate'], \
            f"缓存命中率过低: {hit_rate:.1f}% < {self.performance_thresholds['min_cache_hit_rate']}%"
        
        assert avg_write_time < 1.0, f"缓存写入太慢: {avg_write_time:.3f}ms"
        assert avg_read_time < 0.5, f"缓存读取太慢: {avg_read_time:.3f}ms"
        
        print(f"\n缓存性能结果:")
        print(f"  缓存命中率: {hit_rate:.1f}%")
        print(f"  平均写入时间: {avg_write_time:.3f}ms")
        print(f"  平均读取时间: {avg_read_time:.3f}ms")
    
    def test_metrics_calculation_performance(self):
        """测试指标计算性能"""
        # 创建大量测试数据
        num_points = 10000
        returns = np.random.normal(0.001, 0.02, num_points)
        benchmark_returns = np.random.normal(0.0008, 0.015, num_points)
        
        portfolio_values = []
        for i, ret in enumerate(returns):
            portfolio_values.append({
                'Date': datetime(2024, 1, 1) + timedelta(days=i//4),
                'Portfolio Value': 100000 * (1 + ret),
                'Daily Return': ret * 100
            })
        
        trades = []
        for i in range(100):  # 100笔交易
            trades.append(Mock())
        
        # 测试性能指标计算
        start_time = time.time()
        perf_metrics = MetricsCalculator.calculate_performance_metrics(
            portfolio_values, returns.tolist(), trades, 100000
        )
        perf_time = time.time() - start_time
        
        # 测试风险指标计算
        start_time = time.time()
        risk_metrics = MetricsCalculator.calculate_risk_metrics(
            returns.tolist(), benchmark_returns.tolist()
        )
        risk_time = time.time() - start_time
        
        # 性能断言
        assert perf_time < 2.0, f"性能指标计算太慢: {perf_time:.3f}s"
        assert risk_time < 1.0, f"风险指标计算太慢: {risk_time:.3f}s"
        
        # 验证结果正确性
        assert perf_metrics is not None
        assert risk_metrics is not None
        assert isinstance(perf_metrics.sharpe_ratio, (int, float))
        assert isinstance(risk_metrics.value_at_risk, (int, float))
        
        print(f"\n指标计算性能:")
        print(f"  数据点数: {num_points}")
        print(f"  性能指标计算: {perf_time:.3f}s")
        print(f"  风险指标计算: {risk_time:.3f}s")
    
    @pytest.mark.slow
    def test_concurrent_backtesting_performance(self):
        """测试并发回测性能"""
        num_threads = 3
        results = []
        errors = []
        
        def run_backtest(thread_id):
            try:
                with patch('src.backtesting.cache.CacheManager.get_cached_price_data') as mock_data:
                    mock_data.return_value = self._create_small_dataset()
                    
                    config = {
                        'ticker': f'00000{thread_id}',
                        'start_date': '2024-01-01',
                        'end_date': '2024-01-10',
                        'initial_capital': 100000,
                        'num_of_news': 3
                    }
                    
                    backtester = IntelligentBacktester(
                        agent=self.mock_agent,
                        **config
                    )
                    
                    start_time = time.time()
                    backtester.run_backtest()
                    execution_time = time.time() - start_time
                    
                    results.append({
                        'thread_id': thread_id,
                        'execution_time': execution_time,
                        'portfolio_value': backtester.portfolio['portfolio_value']
                    })
                    
            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")
        
        # 创建和启动线程
        threads = []
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=run_backtest, args=(i+1,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # 验证结果
        assert len(errors) == 0, f"并发执行错误: {errors}"
        assert len(results) == num_threads, f"期望 {num_threads} 个结果，实际得到 {len(results)} 个"
        
        # 性能断言
        max_single_time = max(r['execution_time'] for r in results)
        assert total_time < max_single_time * 1.5, \
            f"并发效率低: 总时间 {total_time:.2f}s > 最大单个时间 {max_single_time:.2f}s * 1.5"
        
        print(f"\n并发性能结果:")
        print(f"  线程数: {num_threads}")
        print(f"  总执行时间: {total_time:.2f}s")
        print(f"  平均单线程时间: {sum(r['execution_time'] for r in results) / len(results):.2f}s")
        print(f"  最大单线程时间: {max_single_time:.2f}s")
    
    def test_memory_usage_monitoring(self):
        """测试内存使用监控"""
        # 获取初始内存
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建多个回测器实例
        backtesters = []
        memory_samples = [initial_memory]
        
        with patch('src.backtesting.cache.CacheManager.get_cached_price_data') as mock_data:
            mock_data.return_value = self._create_small_dataset()
            
            for i in range(5):
                config = {
                    'ticker': f'00000{i}',
                    'start_date': '2024-01-01',
                    'end_date': '2024-01-05',
                    'initial_capital': 100000,
                    'num_of_news': 3
                }
                
                backtester = IntelligentBacktester(
                    agent=self.mock_agent,
                    **config
                )
                backtesters.append(backtester)
                
                # 记录内存使用
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
        
        # 计算内存增长
        memory_growth = memory_samples[-1] - memory_samples[0]
        avg_memory_per_instance = memory_growth / len(backtesters) if len(backtesters) > 0 else 0
        
        # 内存使用断言
        assert memory_growth < self.performance_thresholds['max_memory_usage'], \
            f"内存使用过多: {memory_growth:.2f}MB"
        
        assert avg_memory_per_instance < 50, \
            f"单个实例内存使用过多: {avg_memory_per_instance:.2f}MB"
        
        print(f"\n内存使用监控:")
        print(f"  初始内存: {initial_memory:.2f}MB")
        print(f"  最终内存: {memory_samples[-1]:.2f}MB")
        print(f"  内存增长: {memory_growth:.2f}MB")
        print(f"  平均每实例: {avg_memory_per_instance:.2f}MB")
    
    def test_cpu_usage_monitoring(self):
        """测试CPU使用率监控"""
        import threading
        import time
        
        cpu_samples = []
        monitoring = True
        
        def monitor_cpu():
            while monitoring:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_samples.append(cpu_percent)
                time.sleep(0.1)
        
        # 启动CPU监控
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()
        
        try:
            with patch('src.backtesting.cache.CacheManager.get_cached_price_data') as mock_data:
                mock_data.return_value = self._create_medium_dataset()
                
                config = {
                    'ticker': '000001',
                    'start_date': '2024-01-01',
                    'end_date': '2024-01-31',
                    'initial_capital': 100000,
                    'num_of_news': 5
                }
                
                backtester = IntelligentBacktester(
                    agent=self.mock_agent,
                    **config
                )
                
                # 运行回测
                backtester.run_backtest()
                
        finally:
            # 停止监控
            monitoring = False
            monitor_thread.join()
        
        # 计算CPU使用统计
        if cpu_samples:
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            max_cpu = max(cpu_samples)
            
            # CPU使用断言
            assert avg_cpu < self.performance_thresholds['max_cpu_usage'], \
                f"平均CPU使用率过高: {avg_cpu:.1f}% > {self.performance_thresholds['max_cpu_usage']}%"
            
            print(f"\nCPU使用监控:")
            print(f"  平均CPU使用率: {avg_cpu:.1f}%")
            print(f"  最大CPU使用率: {max_cpu:.1f}%")
            print(f"  采样数量: {len(cpu_samples)}")
    
    # 辅助方法
    
    def _create_large_dataset(self, num_days: int) -> pd.DataFrame:
        """创建大数据集"""
        np.random.seed(42)
        return pd.DataFrame({
            'open': np.random.uniform(90, 110, num_days),
            'close': np.random.uniform(90, 110, num_days),
            'high': np.random.uniform(110, 120, num_days),
            'low': np.random.uniform(80, 90, num_days),
            'volume': np.random.randint(500000, 2000000, num_days)
        })
    
    def _create_medium_dataset(self) -> pd.DataFrame:
        """创建中等数据集"""
        return self._create_large_dataset(30)  # 30天
    
    def _create_small_dataset(self) -> pd.DataFrame:
        """创建小数据集"""
        return pd.DataFrame({
            'open': [100.0, 102.0, 101.0, 104.0, 103.0],
            'close': [102.0, 101.0, 104.0, 103.0, 105.0],
            'high': [103.0, 103.0, 105.0, 105.0, 106.0],
            'low': [99.0, 100.0, 100.0, 102.0, 102.0],
            'volume': [1000000, 1200000, 800000, 1500000, 900000]
        })


if __name__ == '__main__':
    # 运行性能测试
    pytest.main([__file__, '-v', '--tb=short'])
