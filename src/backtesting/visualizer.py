"""
性能可视化器 - 图表生成和分析展示
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib
from datetime import datetime
from typing import List, Dict, Any
try:
    from .models import PerformanceMetrics, RiskMetrics
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.backtesting.models import PerformanceMetrics, RiskMetrics

# 配置matplotlib
matplotlib.rcParams['font.size'] = 10
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['figure.dpi'] = 100
plt.style.use('default')


class PerformanceVisualizer:
    """性能可视化器"""
    
    def __init__(self, ticker: str, initial_capital: float):
        self.ticker = ticker
        self.initial_capital = initial_capital
    
    def create_performance_plot(self, 
                              portfolio_values: List[Dict[str, Any]],
                              benchmark_values: List[float],
                              agent_execution_stats: Dict[str, int],
                              cache_hits: int,
                              cache_misses: int,
                              total_possible_executions: int,
                              agent_frequencies: Dict[str, str],
                              perf_metrics: PerformanceMetrics,
                              risk_metrics: RiskMetrics,
                              daily_returns: List[float],
                              save_plots: bool = True) -> str:
        """创建性能分析图表"""
        
        if not portfolio_values:
            print("无性能数据可分析")
            return ""
        
        # 创建性能DataFrame
        performance_df = pd.DataFrame(portfolio_values).set_index("Date")
        performance_df["Cumulative Return"] = (
            performance_df["Portfolio Value"] / self.initial_capital - 1) * 100
        performance_df["Portfolio Value (K)"] = performance_df["Portfolio Value"] / 1000
        
        if not save_plots:
            return ""
        
        # 创建图形目录
        plots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'plots')
        os.makedirs(plots_dir, exist_ok=True)
        
        # 创建增强的可视化
        fig = plt.figure(figsize=(16, 12))
        
        # 投资组合价值图表
        ax1 = plt.subplot(3, 3, 1)
        ax1.plot(performance_df.index, performance_df["Portfolio Value (K)"], 
                label="Portfolio Value", linewidth=2, color='blue')
        ax1.set_ylabel("Portfolio Value (K)")
        ax1.set_title("Portfolio Value Evolution")
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        # 格式化x轴日期
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(performance_df)//6)))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 累计收益对比基准
        ax2 = plt.subplot(3, 3, 2)
        ax2.plot(performance_df.index, performance_df["Cumulative Return"], 
                label="Portfolio", linewidth=2, color='green')
        
        if benchmark_values and len(benchmark_values) == len(performance_df):
            benchmark_returns = [(val/benchmark_values[0] - 1)*100 for val in benchmark_values]
            ax2.plot(performance_df.index, benchmark_returns, 
                    label="Benchmark", linewidth=2, color='orange', alpha=0.7)
        
        ax2.set_ylabel("Cumulative Return (%)")
        ax2.set_title("Returns vs Benchmark")
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        # 格式化x轴日期
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(performance_df)//6)))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Agent执行频率统计
        ax3 = plt.subplot(3, 3, 3)
        agents = list(agent_execution_stats.keys())
        executions = [agent_execution_stats[agent] for agent in agents]
        total_days = len(performance_df)
        
        bars = ax3.bar(range(len(agents)), executions, color='skyblue', alpha=0.7)
        ax3.set_xticks(range(len(agents)))
        ax3.set_xticklabels([a[:6] for a in agents], rotation=45)
        ax3.set_ylabel("Executions")
        ax3.set_title("Agent Execution Frequency")
        
        # 添加执行次数标签
        for i, bar in enumerate(bars):
            height = bar.get_height()
            percentage = height / total_days * 100
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}\n({percentage:.0f}%)',
                    ha='center', va='bottom', fontsize=8)
        
        # 回撤图表
        ax4 = plt.subplot(3, 3, 4)
        rolling_max = performance_df["Portfolio Value"].cummax()
        drawdown = (performance_df["Portfolio Value"] / rolling_max - 1) * 100
        ax4.fill_between(performance_df.index, drawdown, 0, alpha=0.3, color='red')
        ax4.plot(performance_df.index, drawdown, color='red', linewidth=1)
        ax4.set_ylabel("Drawdown (%)")
        ax4.set_title("Portfolio Drawdown")
        ax4.grid(True, alpha=0.3)
        # 格式化x轴日期
        ax4.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax4.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(performance_df)//6)))
        plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 日收益率分布
        ax5 = plt.subplot(3, 3, 5)
        if len(daily_returns) > 1:
            returns_pct = [r * 100 for r in daily_returns]
            ax5.hist(returns_pct, bins=30, alpha=0.7, color='lightgreen', edgecolor='black')
            ax5.axvline(np.mean(returns_pct), color='red', linestyle='--', 
                       label=f'Mean: {np.mean(returns_pct):.2f}%')
            ax5.set_xlabel("Daily Return (%)")
            ax5.set_ylabel("Frequency")
            ax5.set_title("Daily Returns Distribution")
            ax5.legend()
            ax5.grid(True, alpha=0.3)
        
        # 缓存命中率饼图
        ax6 = plt.subplot(3, 3, 6)
        cache_labels = ['Cache Hits', 'Cache Misses']
        cache_sizes = [cache_hits, cache_misses]
        colors = ['lightblue', 'lightcoral']
        
        if sum(cache_sizes) > 0:
            ax6.pie(cache_sizes, labels=cache_labels, colors=colors, autopct='%1.1f%%')
            ax6.set_title(f'Cache Performance\n(Total: {sum(cache_sizes)})')
        
        # 性能指标摘要
        ax7 = plt.subplot(3, 3, (7, 9))  # 占用最后一行
        ax7.axis('off')
        
        # 计算总体优化效果
        total_possible = total_possible_executions * len(agent_frequencies)
        total_actual = sum(agent_execution_stats.values())
        optimization_rate = (1 - total_actual / total_possible) * 100 if total_possible > 0 else 0
        
        metrics_text = f"""
        PERFORMANCE SUMMARY
        
        Total Return: {perf_metrics.total_return*100:.2f}%
        Annualized Return: {perf_metrics.annualized_return*100:.2f}%
        Volatility: {perf_metrics.volatility*100:.2f}%
        Sharpe Ratio: {perf_metrics.sharpe_ratio:.2f}
        Max Drawdown: {perf_metrics.max_drawdown*100:.2f}%
        
        TRADE STATISTICS
        
        Total Trades: {perf_metrics.trades_count}
        Win Rate: {perf_metrics.win_rate*100:.1f}%
        Profit Factor: {perf_metrics.profit_factor:.2f}
        
        RISK METRICS
        
        VaR (95%): {risk_metrics.value_at_risk*100:.2f}%
        Expected Shortfall: {risk_metrics.expected_shortfall*100:.2f}%
        Beta: {risk_metrics.beta:.2f}
        Information Ratio: {risk_metrics.information_ratio:.2f}
        
        INTELLIGENT OPTIMIZATION
        
        Agent Optimization: {optimization_rate:.1f}%
        Cache Hit Rate: {((cache_hits/(cache_hits+cache_misses)*100) if (cache_hits+cache_misses) > 0 else 0):.1f}%
        Total Requests Saved: {cache_hits}
        
        AGENT EXECUTION STATS
        
        {chr(10).join([f"{agent:12s}: {count:3d} times" for agent, count in agent_execution_stats.items()])}
        """
        
        ax7.text(0.05, 0.95, metrics_text, transform=ax7.transAxes, fontsize=9,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        plt.tight_layout()
        
        # 保存图形
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plot_filename = f"intelligent_backtest_{self.ticker}_{timestamp}.png"
        plot_path = os.path.join(plots_dir, plot_filename)
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return plot_path