"""
系统性能测试

测试系统在不同负载下的性能表现
"""

import pytest
import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
import json
import psutil
import gc


class TestSystemPerformance:
    """系统性能测试"""
    
    @pytest.mark.performance
    def test_single_analysis_latency(self, performance_monitor, mock_agent_state):
        """测试单次分析延迟"""
        state = mock_agent_state.copy()
        
        # 准备测试数据
        messages = [
            Mock(
                content=json.dumps({"signal": "bullish", "confidence": 0.7}),
                name="technical_analyst_agent"
            ),
            Mock(
                content=json.dumps({"signal": "bearish", "confidence": 0.6}),
                name="fundamentals_agent"
            ),
            Mock(
                content=json.dumps({"signal": "neutral", "confidence": 0.5}),
                name="sentiment_agent"
            ),
            Mock(
                content=json.dumps({"signal": "bullish", "confidence": 0.8}),
                name="valuation_agent"
            )
        ]
        
        state["messages"] = messages
        
        # 测试多次执行的平均延迟
        latencies = []
        
        for _ in range(10):
            performance_monitor.start()
            
            from src.agents.researcher_bull import researcher_bull_agent
            result = researcher_bull_agent(state)
            
            latency = performance_monitor.stop("single_analysis")
            latencies.append(latency)
            
            assert result is not None
        
        # 分析延迟统计
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)
        
        # 性能要求
        assert avg_latency < 0.5, f"平均延迟过高: {avg_latency:.3f}s"
        assert max_latency < 1.0, f"最大延迟过高: {max_latency:.3f}s"
        assert min_latency > 0, f"最小延迟异常: {min_latency:.3f}s"
        
        # 计算延迟稳定性
        latency_std = (sum((x - avg_latency) ** 2 for x in latencies) / len(latencies)) ** 0.5
        cv = latency_std / avg_latency  # 变异系数
        assert cv < 0.5, f"延迟变异性过大: {cv:.3f}"
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_analysis_throughput(self, mock_agent_state):
        """测试并发分析吞吐量"""
        def run_analysis(iteration):
            state = mock_agent_state.copy()
            state["data"]["iteration"] = iteration
            
            messages = [
                Mock(
                    content=json.dumps({"signal": "bullish", "confidence": 0.7}),
                    name="technical_analyst_agent"
                ),
                Mock(
                    content=json.dumps({"signal": "bearish", "confidence": 0.6}),
                    name="fundamentals_agent"
                ),
                Mock(
                    content=json.dumps({"signal": "neutral", "confidence": 0.5}),
                    name="sentiment_agent"
                ),
                Mock(
                    content=json.dumps({"signal": "bullish", "confidence": 0.8}),
                    name="valuation_agent"
                )
            ]
            
            state["messages"] = messages
            
            start_time = time.time()
            
            from src.agents.researcher_bull import researcher_bull_agent
            result = researcher_bull_agent(state)
            
            end_time = time.time()
            
            return {
                "iteration": iteration,
                "duration": end_time - start_time,
                "success": result is not None
            }
        
        # 并发测试
        num_threads = 5
        num_iterations = 20
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(run_analysis, i) for i in range(num_iterations)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 分析结果
        successful_runs = sum(1 for r in results if r["success"])
        average_duration = sum(r["duration"] for r in results) / len(results)
        throughput = successful_runs / total_time
        
        # 性能断言
        assert successful_runs == num_iterations, f"成功率: {successful_runs}/{num_iterations}"
        assert throughput > 10, f"吞吐量过低: {throughput:.2f} ops/sec"
        assert average_duration < 1.0, f"平均响应时间过长: {average_duration:.3f}s"
    
    @pytest.mark.performance
    def test_memory_usage_under_load(self, mock_agent_state):
        """测试负载下的内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        def memory_intensive_analysis():
            state = mock_agent_state.copy()
            
            # 创建较大的消息数据
            large_data = "x" * 10000  # 10KB数据
            messages = []
            
            for i in range(50):  # 创建更多消息
                message = Mock(
                    content=json.dumps({
                        "signal": "bullish",
                        "confidence": 0.7,
                        "large_data": large_data,
                        "iteration": i
                    }),
                    name=f"agent_{i % 4}"
                )
                messages.append(message)
            
            state["messages"] = messages
            
            from src.agents.researcher_bull import researcher_bull_agent
            result = researcher_bull_agent(state)
            
            return result
        
        # 执行多次内存密集型分析
        memory_readings = []
        
        for i in range(20):
            result = memory_intensive_analysis()
            
            # 记录内存使用
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_readings.append(current_memory)
            
            # 强制垃圾回收
            if i % 5 == 0:
                gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        peak_memory = max(memory_readings)
        memory_growth = final_memory - initial_memory
        
        # 内存使用断言
        assert memory_growth < 100, f"内存增长过多: {memory_growth:.2f}MB"
        assert peak_memory < initial_memory + 200, f"峰值内存过高: {peak_memory:.2f}MB"
    
    @pytest.mark.performance
    def test_cpu_usage_efficiency(self, mock_agent_state):
        """测试CPU使用效率"""
        import psutil
        import threading
        
        cpu_readings = []
        stop_monitoring = threading.Event()
        
        def monitor_cpu():
            while not stop_monitoring.is_set():
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_readings.append(cpu_percent)
        
        # 开始CPU监控
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()
        
        try:
            # 执行CPU密集型测试
            state = mock_agent_state.copy()
            messages = [
                Mock(
                    content=json.dumps({"signal": "bullish", "confidence": 0.7}),
                    name="technical_analyst_agent"
                ),
                Mock(
                    content=json.dumps({"signal": "bearish", "confidence": 0.6}),
                    name="fundamentals_agent"
                ),
                Mock(
                    content=json.dumps({"signal": "neutral", "confidence": 0.5}),
                    name="sentiment_agent"
                ),
                Mock(
                    content=json.dumps({"signal": "bullish", "confidence": 0.8}),
                    name="valuation_agent"
                )
            ]
            
            state["messages"] = messages
            
            # 执行多次分析
            for _ in range(50):
                from src.agents.researcher_bull import researcher_bull_agent
                result = researcher_bull_agent(state)
                assert result is not None
            
        finally:
            # 停止监控
            stop_monitoring.set()
            monitor_thread.join()
        
        # 分析CPU使用
        if cpu_readings:
            avg_cpu = sum(cpu_readings) / len(cpu_readings)
            max_cpu = max(cpu_readings)
            
            # CPU使用不应该过高（考虑到这是单线程测试）
            assert avg_cpu < 80, f"平均CPU使用率过高: {avg_cpu:.2f}%"
            assert max_cpu < 95, f"峰值CPU使用率过高: {max_cpu:.2f}%"
    
    @pytest.mark.performance
    def test_scalability_with_data_size(self, mock_agent_state):
        """测试数据规模可扩展性"""
        def test_with_message_count(message_count):
            state = mock_agent_state.copy()
            
            # 创建指定数量的消息
            messages = []
            for i in range(message_count):
                message = Mock(
                    content=json.dumps({
                        "signal": "bullish",
                        "confidence": 0.7,
                        "data": f"data_{i}",
                        "timestamp": time.time()
                    }),
                    name=f"agent_{i % 4}"
                )
                messages.append(message)
            
            state["messages"] = messages
            
            start_time = time.time()
            
            from src.agents.researcher_bull import researcher_bull_agent
            result = researcher_bull_agent(state)
            
            end_time = time.time()
            
            return {
                "message_count": message_count,
                "duration": end_time - start_time,
                "success": result is not None
            }
        
        # 测试不同的数据规模
        test_sizes = [10, 50, 100, 200, 500]
        results = []
        
        for size in test_sizes:
            result = test_with_message_count(size)
            results.append(result)
            assert result["success"], f"规模{size}测试失败"
        
        # 分析可扩展性
        # 检查时间复杂度是否合理（应该接近线性）
        for i in range(1, len(results)):
            prev_result = results[i-1]
            curr_result = results[i]
            
            size_ratio = curr_result["message_count"] / prev_result["message_count"]
            time_ratio = curr_result["duration"] / prev_result["duration"]
            
            # 时间增长不应该超过数据规模增长的平方
            assert time_ratio <= size_ratio ** 1.5, f"规模{curr_result['message_count']}时性能退化严重"
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_long_running_stability(self, mock_agent_state):
        """测试长期运行稳定性"""
        state = mock_agent_state.copy()
        
        messages = [
            Mock(
                content=json.dumps({"signal": "bullish", "confidence": 0.7}),
                name="technical_analyst_agent"
            ),
            Mock(
                content=json.dumps({"signal": "bearish", "confidence": 0.6}),
                name="fundamentals_agent"
            ),
            Mock(
                content=json.dumps({"signal": "neutral", "confidence": 0.5}),
                name="sentiment_agent"
            ),
            Mock(
                content=json.dumps({"signal": "bullish", "confidence": 0.8}),
                name="valuation_agent"
            )
        ]
        
        state["messages"] = messages
        
        # 长期运行测试
        start_time = time.time()
        success_count = 0
        error_count = 0
        response_times = []
        
        target_duration = 10  # 运行10秒
        
        while time.time() - start_time < target_duration:
            try:
                iteration_start = time.time()
                
                from src.agents.researcher_bull import researcher_bull_agent
                result = researcher_bull_agent(state)
                
                iteration_end = time.time()
                response_time = iteration_end - iteration_start
                response_times.append(response_time)
                
                if result is not None:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
            
            # 短暂休息，避免过度占用CPU
            time.sleep(0.01)
        
        total_time = time.time() - start_time
        total_runs = success_count + error_count
        
        # 稳定性断言
        success_rate = success_count / total_runs if total_runs > 0 else 0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        throughput = total_runs / total_time
        
        assert success_rate >= 0.95, f"成功率过低: {success_rate:.2%}"
        assert avg_response_time < 1.0, f"平均响应时间过长: {avg_response_time:.3f}s"
        assert throughput > 10, f"吞吐量过低: {throughput:.2f} ops/sec"
        assert error_count < total_runs * 0.05, f"错误率过高: {error_count}/{total_runs}"


class TestResourceUtilization:
    """资源利用率测试"""
    
    @pytest.mark.performance
    def test_file_handle_management(self, mock_agent_state):
        """测试文件句柄管理"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_handles = process.num_fds() if hasattr(process, 'num_fds') else 0
        
        # 执行多次操作，检查文件句柄泄漏
        for i in range(100):
            state = mock_agent_state.copy()
            state["data"]["iteration"] = i
            
            messages = [
                Mock(
                    content=json.dumps({"signal": "bullish", "confidence": 0.7}),
                    name="technical_analyst_agent"
                )
            ]
            state["messages"] = messages
            
            from src.agents.researcher_bull import researcher_bull_agent
            result = researcher_bull_agent(state)
            
            # 每20次检查一次句柄数
            if i % 20 == 0 and hasattr(process, 'num_fds'):
                current_handles = process.num_fds()
                handle_growth = current_handles - initial_handles
                assert handle_growth < 50, f"可能存在文件句柄泄漏: {handle_growth}"
    
    @pytest.mark.performance
    def test_thread_safety(self, mock_agent_state):
        """测试线程安全性"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def worker_thread(thread_id):
            try:
                for i in range(10):
                    state = mock_agent_state.copy()
                    state["data"]["thread_id"] = thread_id
                    state["data"]["iteration"] = i
                    
                    messages = [
                        Mock(
                            content=json.dumps({"signal": "bullish", "confidence": 0.7}),
                            name="technical_analyst_agent"
                        ),
                        Mock(
                            content=json.dumps({"signal": "bearish", "confidence": 0.6}),
                            name="fundamentals_agent"
                        ),
                        Mock(
                            content=json.dumps({"signal": "neutral", "confidence": 0.5}),
                            name="sentiment_agent"
                        ),
                        Mock(
                            content=json.dumps({"signal": "bullish", "confidence": 0.8}),
                            name="valuation_agent"
                        )
                    ]
                    state["messages"] = messages
                    
                    from src.agents.researcher_bull import researcher_bull_agent
                    result = researcher_bull_agent(state)
                    
                    results_queue.put({
                        "thread_id": thread_id,
                        "iteration": i,
                        "success": result is not None
                    })
                    
            except Exception as e:
                errors_queue.put({
                    "thread_id": thread_id,
                    "error": str(e)
                })
        
        # 创建多个线程
        threads = []
        num_threads = 5
        
        for thread_id in range(num_threads):
            thread = threading.Thread(target=worker_thread, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 收集结果
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        errors = []
        while not errors_queue.empty():
            errors.append(errors_queue.get())
        
        # 验证线程安全性
        expected_results = num_threads * 10
        assert len(results) == expected_results, f"结果数量不符: {len(results)}/{expected_results}"
        assert len(errors) == 0, f"发生错误: {errors}"
        
        # 验证所有操作都成功
        successful_results = sum(1 for r in results if r["success"])
        assert successful_results == expected_results, f"成功率不符: {successful_results}/{expected_results}"