"""
智能回测器主类 - 细粒度频率控制
整合所有组件，提供完整的回测功能
"""

import json
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import deque
import warnings
import os

try:
    from .models import AgentConfig, Trade, PerformanceMetrics, RiskMetrics
    from .cache import CacheManager
    from .trading import TradeExecutor
    from .metrics import MetricsCalculator
    from .visualizer import PerformanceVisualizer
    from .benchmarks import BenchmarkCalculator
except ImportError:
    # 当直接运行时，使用绝对导入
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.backtesting.models import AgentConfig, Trade, PerformanceMetrics, RiskMetrics
    from src.backtesting.cache import CacheManager
    from src.backtesting.trading import TradeExecutor
    from src.backtesting.metrics import MetricsCalculator
    from src.backtesting.visualizer import PerformanceVisualizer
    from src.backtesting.benchmarks import BenchmarkCalculator
from src.tools.api import get_price_data

# 抑制警告
warnings.filterwarnings('ignore')


class IntelligentBacktester:
    """智能回测框架 - 支持细粒度频率控制"""
    
    def __init__(self, agent, ticker: str, start_date: str, end_date: str, 
                 initial_capital: float, num_of_news: int,
                 commission_rate: float = 0.0003, slippage_rate: float = 0.001,
                 benchmark_ticker: str = '000001',
                 benchmark_type: str = 'spe',
                 agent_frequencies: Optional[Dict[str, str]] = None,
                 time_granularity: str = 'daily',
                 rebalance_frequency: str = 'daily',
                 transaction_cost: float = 0.001,
                 slippage: float = 0.0005):
        """
        初始化智能回测器
        
        Args:
            agent: 智能体函数
            ticker: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            initial_capital: 初始资金
            num_of_news: 新闻分析数量
            commission_rate: 手续费率 (已弃用，使用transaction_cost)
            slippage_rate: 滑点率 (已弃用，使用slippage)
            benchmark_ticker: 基准指数代码
            benchmark_type: 基准类型 ('spe', 'csi300', 'equal_weight', 'momentum', 'mean_reversion')
            agent_frequencies: 各agent的执行频率配置
            time_granularity: 时间细粒度 ('minute', 'hourly', 'daily', 'weekly')
            rebalance_frequency: 调仓频率 ('daily', 'weekly', 'monthly', 'quarterly')
            transaction_cost: 交易手续费率
            slippage: 滑点率
        """
        self.agent = agent
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.benchmark_ticker = benchmark_ticker  # 保留向后兼容
        self.benchmark_type = benchmark_type
        self.num_of_news = num_of_news
        
        # 新增高级参数
        self.time_granularity = time_granularity
        self.rebalance_frequency = rebalance_frequency
        
        # 使用新的交易成本参数，向后兼容旧参数
        self.transaction_cost = transaction_cost if transaction_cost != 0.001 else commission_rate
        self.slippage = slippage if slippage != 0.0005 else slippage_rate
        
        # 默认agent频率配置
        default_frequencies = {
            'market_data': 'daily',       # 市场数据每日更新
            'technical': 'daily',         # 技术分析每日更新  
            'fundamentals': 'weekly',     # 基本面分析每周更新
            'sentiment': 'daily',         # 情绪分析每日更新
            'valuation': 'monthly',       # 估值分析每月更新
            'macro': 'weekly',            # 宏观分析每周更新
            'portfolio': 'daily'          # 投资组合管理每日更新
        }
        
        self.agent_frequencies = agent_frequencies or default_frequencies
        
        # 初始化组件
        self.cache_manager = CacheManager()
        self.trade_executor = TradeExecutor(self.transaction_cost, self.slippage)
        self.visualizer = PerformanceVisualizer(ticker, initial_capital)
        self.benchmark_calculator = BenchmarkCalculator(benchmark_type, initial_capital)
        
        # 投资组合跟踪
        self.portfolio = {"cash": initial_capital, "stock": 0}
        self.portfolio_values = []
        self.daily_returns = []
        self.benchmark_returns = []
        self.benchmark_values = []
        
        # 性能和风险指标
        self.performance_metrics = PerformanceMetrics()
        self.risk_metrics = RiskMetrics()
        
        # 执行统计
        self._agent_execution_stats = {agent: 0 for agent in self.agent_frequencies.keys()}
        self._total_possible_executions = 0
        
        # 市场状态跟踪（用于条件触发）
        self._market_volatility = deque(maxlen=20)
        self._price_changes = deque(maxlen=5)
        
        # 日志设置
        self.setup_logging()
        self.validate_inputs()
        
        print(f"初始化智能回测器")
        print(f"Agent执行频率配置:")
        for agent, freq in self.agent_frequencies.items():
            print(f"  {agent:12s}: {freq}")

    def setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger('intelligent_backtester')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # 设置回测日志文件
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        current_date = datetime.now().strftime('%Y%m%d')
        backtest_period = f"{self.start_date.replace('-', '')}_{self.end_date.replace('-', '')}"
        log_file = os.path.join(log_dir, f"intelligent_backtest_{self.ticker}_{current_date}_{backtest_period}.log")
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        
        self.backtest_logger = logging.getLogger('intelligent_backtest')
        self.backtest_logger.setLevel(logging.INFO)
        if self.backtest_logger.handlers:
            self.backtest_logger.handlers.clear()
        self.backtest_logger.addHandler(file_handler)

    def validate_inputs(self):
        """验证输入参数"""
        try:
            start = datetime.strptime(self.start_date, "%Y-%m-%d")
            end = datetime.strptime(self.end_date, "%Y-%m-%d")
            if start >= end:
                raise ValueError("开始日期必须早于结束日期")
            if self.initial_capital <= 0:
                raise ValueError("初始资金必须大于0")
            if not isinstance(self.ticker, str) or len(self.ticker) != 6:
                raise ValueError("无效的股票代码格式")
            
            # 验证频率配置
            valid_frequencies = ['daily', 'weekly', 'monthly', 'conditional']
            for agent, freq in self.agent_frequencies.items():
                if freq not in valid_frequencies:
                    raise ValueError(f"无效的频率配置 {agent}: {freq}")
            
            self.logger.info("输入参数验证通过")
        except Exception as e:
            self.logger.error(f"输入参数验证失败: {str(e)}")
            raise

    def _should_execute_agent(self, agent_name: str, current_date: datetime) -> bool:
        """判断特定agent是否应该在当前日期执行"""
        if agent_name not in self.agent_frequencies:
            return True  # 默认执行
            
        frequency = self.agent_frequencies[agent_name]
        
        if frequency == 'daily':
            return True
        elif frequency == 'weekly':
            # 每周一执行
            return current_date.weekday() == 0
        elif frequency == 'monthly':
            # 每月第一个交易日执行 (只在第一天执行)
            return current_date.day == 1
        elif frequency == 'conditional':
            return self._check_conditional_trigger(agent_name, current_date)
        
        return False

    def _check_conditional_trigger(self, agent_name: str, current_date: datetime) -> bool:
        """检查条件触发逻辑"""
        # 高波动率时增加执行频率
        if len(self._market_volatility) >= 10:
            recent_volatility = np.std(list(self._market_volatility))
            historical_volatility = np.std(list(self._market_volatility)) if len(self._market_volatility) > 15 else recent_volatility
            
            if recent_volatility > historical_volatility * 1.5:  # 波动率上升50%
                return True
        
        # 价格大幅变动时触发
        if len(self._price_changes) >= 3:
            recent_change = abs(sum(list(self._price_changes)[-3:]))
            if recent_change > 0.05:  # 3日累计变动超过5%
                return True
        
        # 周一或月初触发
        return current_date.weekday() == 0 or current_date.day <= 3

    def _update_market_conditions(self, current_price: float, previous_price: float):
        """更新市场状态"""
        if previous_price > 0:
            price_change = (current_price - previous_price) / previous_price
            self._price_changes.append(price_change)
            
            # 计算短期波动率
            if len(self._price_changes) >= 5:
                volatility = np.std(list(self._price_changes))
                self._market_volatility.append(volatility)

    def get_agent_decision(self, current_date: str, lookback_start: str, portfolio: Dict[str, float]) -> Dict[str, Any]:
        """获取智能体决策，支持细粒度频率控制"""
        current_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
        self._total_possible_executions += 1
        
        # 检查哪些agent需要执行
        agents_to_execute = []
        for agent_name in self.agent_frequencies.keys():
            if self._should_execute_agent(agent_name, current_date_obj):
                agents_to_execute.append(agent_name)
                self._agent_execution_stats[agent_name] += 1
        
        if not agents_to_execute:
            # 没有agent需要执行，返回cached决策
            return self.cache_manager.get_last_decision()
        
        # 检查缓存
        cache_key = f"{current_date}_{'-'.join(sorted(agents_to_execute))}"
        cached_result = self.cache_manager.get_agent_result(cache_key)
        if cached_result is not None:
            self.logger.info(f"使用缓存的决策: {current_date} (agents: {agents_to_execute})")
            return cached_result
        
        # 执行需要的agents
        self.logger.info(f"执行agents: {agents_to_execute} at {current_date}")
        
        # 根据需要执行的agents调整执行策略
        if len(agents_to_execute) == len(self.agent_frequencies):
            # 所有agents都需要执行，使用完整workflow
            result = self._execute_full_workflow(current_date, lookback_start, portfolio)
        else:
            # 部分agents执行，使用简化workflow
            result = self._execute_partial_workflow(agents_to_execute, current_date, lookback_start, portfolio)
        
        # 缓存结果
        self.cache_manager.cache_agent_result(cache_key, result)
        
        return result

    def _execute_full_workflow(self, current_date: str, lookback_start: str, portfolio: Dict[str, float]) -> Dict[str, Any]:
        """执行完整的agent workflow"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    time.sleep(2)
                
                result = self.agent(
                    ticker=self.ticker,
                    start_date=lookback_start,
                    end_date=current_date,
                    portfolio=portfolio,
                    num_of_news=self.num_of_news,
                    run_id=f"intelligent_backtest_{self.ticker}_{current_date.replace('-', '')}"
                )

                # 解析结果
                try:
                    if isinstance(result, str):
                        result = result.replace('```json\n', '').replace('\n```', '').strip()
                        parsed_result = json.loads(result)
                        formatted_result = {
                            "decision": parsed_result,
                            "analyst_signals": {},
                            "execution_type": "full_workflow"
                        }
                        
                        if "agent_signals" in parsed_result:
                            formatted_result["analyst_signals"] = {
                                signal["agent"]: {
                                    "signal": signal.get("signal", "unknown"),
                                    "confidence": signal.get("confidence", 0)
                                }
                                for signal in parsed_result["agent_signals"]
                            }
                        
                        return formatted_result
                        
                    return result
                    
                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON解析错误: {str(e)}")
                    return {
                        "decision": {"action": "hold", "quantity": 0},
                        "analyst_signals": {},
                        "execution_type": "fallback"
                    }

            except Exception as e:
                self.logger.warning(f"完整workflow执行失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    return {
                        "decision": {"action": "hold", "quantity": 0},
                        "analyst_signals": {},
                        "execution_type": "error_fallback"
                    }
                time.sleep(2 ** attempt)

    def _execute_partial_workflow(self, agents_to_execute: List[str], current_date: str, 
                                lookback_start: str, portfolio: Dict[str, float]) -> Dict[str, Any]:
        """执行部分agent workflow (简化版)"""
        self.logger.info(f"执行简化workflow，包含agents: {agents_to_execute}")
        
        # 基于需要执行的agents制定简化的决策逻辑
        decision = {"action": "hold", "quantity": 0}
        
        try:
            # 获取市场数据（总是需要的）
            df = self.cache_manager.get_cached_price_data(self.ticker, lookback_start, current_date)
            if df is None or df.empty:
                return {
                    "decision": decision,
                    "analyst_signals": {},
                    "execution_type": "no_data"
                }
            
            current_price = df.iloc[-1]['open']
            
            # 简化的决策逻辑
            signals = {}
            
            if 'technical' in agents_to_execute:
                # 简化技术分析
                if len(df) >= 20:
                    ma20 = df['close'].rolling(20).mean().iloc[-1]
                    if current_price > ma20 * 1.02:  # 价格超过20日均线2%
                        signals['technical'] = 'bullish'
                    elif current_price < ma20 * 0.98:  # 价格低于20日均线2%
                        signals['technical'] = 'bearish'
                    else:
                        signals['technical'] = 'neutral'
            
            if 'sentiment' in agents_to_execute:
                # 简化情绪分析（基于价格动量）
                if len(df) >= 5:
                    momentum = (current_price / df['close'].iloc[-5] - 1)
                    if momentum > 0.03:
                        signals['sentiment'] = 'positive'
                    elif momentum < -0.03:
                        signals['sentiment'] = 'negative'
                    else:
                        signals['sentiment'] = 'neutral'
            
            # 基于信号组合做出决策
            bullish_signals = sum(1 for s in signals.values() if s in ['bullish', 'positive'])
            bearish_signals = sum(1 for s in signals.values() if s in ['bearish', 'negative'])
            
            if bullish_signals > bearish_signals and bullish_signals >= 1:
                decision = {"action": "buy", "quantity": 100}
            elif bearish_signals > bullish_signals and bearish_signals >= 1:
                decision = {"action": "sell", "quantity": 100}
            
            return {
                "decision": decision,
                "analyst_signals": signals,
                "execution_type": "partial_workflow",
                "agents_executed": agents_to_execute
            }
            
        except Exception as e:
            self.logger.error(f"简化workflow执行失败: {str(e)}")
            return {
                "decision": {"action": "hold", "quantity": 0},
                "analyst_signals": {},
                "execution_type": "partial_error"
            }

    def run_backtest(self):
        """运行智能回测"""
        dates = pd.date_range(self.start_date, self.end_date, freq="B")
        
        # 预先计算基准收益率
        benchmark_info = self.benchmark_calculator.get_benchmark_info()
        self.logger.info(f"\n开始智能回测...")
        self.logger.info(f"使用基准: {benchmark_info['name']} - {benchmark_info['description']}")
        print(f"基准: {benchmark_info['name']}")
        
        try:
            self.benchmark_returns = self.benchmark_calculator.calculate_benchmark_returns(
                self.ticker, self.start_date, self.end_date)
            self.logger.info(f"成功计算基准收益率，共{len(self.benchmark_returns)}个数据点")
        except Exception as e:
            self.logger.warning(f"基准计算失败，将使用默认基准: {e}")
            self.benchmark_returns = []
        
        print(f"{'Date':<12} {'Ticker':<6} {'Action':<6} {'Qty':>8} {'Price':>8} {'Cash':>12} {'Position':>8} {'Total Value':>12} {'Execution Type':<15}")
        print("-" * 125)

        previous_price = None

        for current_date in dates:
            lookback_start = (current_date - timedelta(days=30)).strftime("%Y-%m-%d")
            current_date_str = current_date.strftime("%Y-%m-%d")

            # 获取智能体决策
            output = self.get_agent_decision(current_date_str, lookback_start, self.portfolio)
            
            agent_decision = output.get("decision", {"action": "hold", "quantity": 0})
            action, quantity = agent_decision.get("action", "hold"), agent_decision.get("quantity", 0)
            execution_type = output.get("execution_type", "unknown")
            
            # 获取价格数据并执行交易
            df = self.cache_manager.get_cached_price_data(self.ticker, lookback_start, current_date_str)
            if df is None or df.empty:
                continue

            current_price = df.iloc[-1]['open']
            
            # 更新市场状态
            if previous_price is not None:
                self._update_market_conditions(current_price, previous_price)
            previous_price = current_price
            
            executed_quantity = self.trade_executor.execute_trade(action, quantity, current_price, current_date_str, self.portfolio)

            # 更新投资组合价值
            total_value = self.portfolio["cash"] + self.portfolio["stock"] * current_price
            self.portfolio["portfolio_value"] = total_value

            # 计算日收益率
            if len(self.portfolio_values) > 0:
                daily_return = (total_value / self.portfolio_values[-1]["Portfolio Value"] - 1)
            else:
                daily_return = 0
            
            self.daily_returns.append(daily_return)

            # 记录投资组合价值
            self.portfolio_values.append({
                "Date": current_date,
                "Portfolio Value": total_value,
                "Daily Return": daily_return * 100
            })
            
            # 更新基准数据 (已预先计算)
            current_day_index = len(self.portfolio_values) - 1
            if current_day_index < len(self.benchmark_returns):
                benchmark_return = self.benchmark_returns[current_day_index]
            else:
                benchmark_return = 0.0
                
            # 计算累积基准价值
            if len(self.benchmark_values) == 0:
                self.benchmark_values.append(self.initial_capital)
            else:
                prev_value = self.benchmark_values[-1]
                new_value = prev_value * (1 + benchmark_return)
                self.benchmark_values.append(new_value)
                
            # 打印进度
            print(f"{current_date_str:<12} {self.ticker:<6} {action.upper():<6} {executed_quantity:>8} "
                  f"{current_price:>8.2f} {self.portfolio['cash']:>12,.0f} {self.portfolio['stock']:>8} "
                  f"{total_value:>12,.0f} {execution_type:<15}")

    def analyze_performance(self, save_plots: bool = True) -> Optional[pd.DataFrame]:
        """分析性能，包含智能执行统计"""
        if not self.portfolio_values:
            print("无性能数据可分析")
            return None
            
        # 计算所有指标
        perf_metrics = MetricsCalculator.calculate_performance_metrics(
            self.portfolio_values, self.daily_returns, self.trade_executor.trades, self.initial_capital)
        risk_metrics = MetricsCalculator.calculate_risk_metrics(self.daily_returns, self.benchmark_returns)
        
        # 创建性能DataFrame
        performance_df = pd.DataFrame(self.portfolio_values).set_index("Date")
        
        # 生成图表
        if save_plots:
            plot_path = self.visualizer.create_performance_plot(
                self.portfolio_values,
                self.benchmark_values,
                self._agent_execution_stats,
                self.cache_manager.cache_hits,
                self.cache_manager.cache_misses,
                self._total_possible_executions,
                self.agent_frequencies,
                perf_metrics,
                risk_metrics,
                self.daily_returns,
                save_plots
            )
            if plot_path:
                print(f"\n图形已保存到: {plot_path}")
        
        # 打印智能优化统计
        self._print_optimization_stats(performance_df, perf_metrics, risk_metrics)
        
        return performance_df

    def parse_decision_from_text(self, text: str) -> Dict[str, Any]:
        """从文本中解析决策"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['buy', 'purchase', 'bullish', 'positive']):
            return {"action": "buy", "quantity": 100}
        elif any(word in text_lower for word in ['sell', 'bearish', 'negative', 'downside']):
            return {"action": "sell", "quantity": 100}
        else:
            return {"action": "hold", "quantity": 0}

    def calculate_performance_metrics(self) -> PerformanceMetrics:
        """计算性能指标"""
        if not self.portfolio_values or not self.daily_returns:
            return PerformanceMetrics()
        
        return MetricsCalculator.calculate_performance_metrics(
            self.portfolio_values, self.daily_returns, 
            self.trade_executor.trades, self.initial_capital
        )

    def calculate_risk_metrics(self) -> RiskMetrics:
        """计算风险指标"""
        if not self.daily_returns:
            return RiskMetrics()
        
        return MetricsCalculator.calculate_risk_metrics(
            self.daily_returns, self.benchmark_returns
        )

    def execute_trade(self, action: str, quantity: int, price: float, 
                     date: str = None) -> int:
        """执行交易"""
        return self.trade_executor.execute_trade(action, quantity, price, date, self.portfolio)

    @property
    def commission_rate(self) -> float:
        """获取手续费率"""
        return self.trade_executor.commission_rate

    @property
    def slippage_rate(self) -> float:
        """获取滑点率"""
        return self.trade_executor.slippage_rate

    @property
    def trades(self) -> List[Trade]:
        """获取交易记录"""
        return self.trade_executor.trades
    
    @trades.setter
    def trades(self, value: List[Trade]):
        """设置交易记录"""
        self.trade_executor.trades = value

    def _print_optimization_stats(self, performance_df: pd.DataFrame, 
                                perf_metrics: PerformanceMetrics, risk_metrics: RiskMetrics):
        """打印优化统计信息"""
        cache_hit_rate = self.cache_manager.cache_hit_rate
        
        print("\n" + "="*70)
        print("智能优化统计")
        print("="*70)
        for agent, count in self._agent_execution_stats.items():
            total_days = len(performance_df)
            execution_rate = count / total_days * 100
            print(f"{agent:15s}: {count:3d}/{total_days} 次执行 ({execution_rate:5.1f}%)")
        
        print(f"\n缓存性能:")
        print(f"  缓存命中: {self.cache_manager.cache_hits}")
        print(f"  缓存未命中: {self.cache_manager.cache_misses}")  
        print(f"  缓存命中率: {cache_hit_rate:.1f}%")
        
        # 计算总体优化效果
        total_possible = self._total_possible_executions * len(self.agent_frequencies)
        total_actual = sum(self._agent_execution_stats.values())
        optimization_rate = (1 - total_actual / total_possible) * 100 if total_possible > 0 else 0
        print(f"  总体优化率: {optimization_rate:.1f}%")
        
        # 打印性能摘要
        print("\n" + "="*60)
        print("回测性能摘要")
        print("="*60)
        print(f"初始资金: ${self.initial_capital:,.2f}")
        print(f"最终价值: ${self.portfolio['portfolio_value']:,.2f}")
        print(f"总收益: {perf_metrics.total_return*100:.2f}%")
        print(f"年化收益: {perf_metrics.annualized_return*100:.2f}%")
        print(f"夏普比率: {perf_metrics.sharpe_ratio:.2f}")
        print(f"最大回撤: {perf_metrics.max_drawdown*100:.2f}%")
        print(f"VaR (95%): {risk_metrics.value_at_risk*100:.2f}%")
        print(f"信息比率: {risk_metrics.information_ratio:.2f}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='运行智能回测模拟')
    parser.add_argument('--ticker', type=str, required=True, help='股票代码 (如: 600519)')
    parser.add_argument('--end-date', type=str,
                        default=datetime.now().strftime('%Y-%m-%d'), help='结束日期，格式: YYYY-MM-DD')
    parser.add_argument('--start-date', type=str, default=(datetime.now() -
                        timedelta(days=90)).strftime('%Y-%m-%d'), help='开始日期，格式: YYYY-MM-DD')
    parser.add_argument('--initial-capital', type=float,
                        default=100000, help='初始资金 (默认: 100000)')
    parser.add_argument('--num-of-news', type=int, default=5,
                        help='新闻分析数量 (默认: 5)')
    
    # 细粒度频率控制参数
    parser.add_argument('--market-data-freq', type=str, default='daily',
                        choices=['daily', 'weekly', 'monthly', 'conditional'],
                        help='市场数据更新频率 (默认: daily)')
    parser.add_argument('--technical-freq', type=str, default='daily',
                        choices=['daily', 'weekly', 'monthly', 'conditional'],
                        help='技术分析频率 (默认: daily)')
    parser.add_argument('--fundamentals-freq', type=str, default='weekly',
                        choices=['daily', 'weekly', 'monthly', 'conditional'],
                        help='基本面分析频率 (默认: weekly)')
    parser.add_argument('--sentiment-freq', type=str, default='daily',
                        choices=['daily', 'weekly', 'monthly', 'conditional'],
                        help='情绪分析频率 (默认: daily)')
    parser.add_argument('--valuation-freq', type=str, default='monthly',
                        choices=['daily', 'weekly', 'monthly', 'conditional'],
                        help='估值分析频率 (默认: monthly)')
    parser.add_argument('--macro-freq', type=str, default='weekly',
                        choices=['daily', 'weekly', 'monthly', 'conditional'],
                        help='宏观分析频率 (默认: weekly)')
    parser.add_argument('--portfolio-freq', type=str, default='daily',
                        choices=['daily', 'weekly', 'monthly', 'conditional'],
                        help='投资组合管理频率 (默认: daily)')
    
    # 基准选择参数
    parser.add_argument('--benchmark', type=str, default='spe',
                        choices=['spe', 'csi300', 'equal_weight', 'momentum', 'mean_reversion'],
                        help='基准类型 (默认: spe - 买入并持有策略)')
    parser.add_argument('--list-benchmarks', action='store_true',
                        help='列出所有可用的基准类型并退出')

    args = parser.parse_args()
    
    # 如果用户要求列出基准，显示并退出
    if args.list_benchmarks:
        print("可用的基准类型:")
        for key, name in BenchmarkCalculator.list_available_benchmarks().items():
            print(f"  {key}: {name}")
        exit(0)

    # 构建agent频率配置
    agent_frequencies = {
        'market_data': args.market_data_freq,
        'technical': args.technical_freq,
        'fundamentals': args.fundamentals_freq,
        'sentiment': args.sentiment_freq,
        'valuation': args.valuation_freq,
        'macro': args.macro_freq,
        'portfolio': args.portfolio_freq
    }

    # 创建智能回测器实例
    try:
        from src.main import run_hedge_fund
    except ImportError:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from src.main import run_hedge_fund
    
    backtester = IntelligentBacktester(
        agent=run_hedge_fund,
        ticker=args.ticker,
        start_date=args.start_date,
        end_date=args.end_date,
        initial_capital=args.initial_capital,
        num_of_news=args.num_of_news,
        benchmark_type=args.benchmark,
        agent_frequencies=agent_frequencies
    )

    # 运行回测
    backtester.run_backtest()

    # 分析性能
    performance_df = backtester.analyze_performance(save_plots=True)