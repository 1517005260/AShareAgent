#!/usr/bin/env python3
"""
智能回测系统的示例脚本
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    """运行回测示例"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='运行智能回测系统')
    parser.add_argument('--ticker', type=str, default='600519', help='股票代码')
    parser.add_argument('--start-date', type=str, help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--initial-capital', type=float, default=100000, help='初始资金')
    parser.add_argument('--show-reasoning', action='store_true', help='显示详细推理')
    args = parser.parse_args()
    
    from src.backtesting import IntelligentBacktester
    from src.main import run_hedge_fund
    
    # 配置参数
    ticker = args.ticker
    start_date = args.start_date or (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = args.end_date or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    initial_capital = args.initial_capital
    
    # 配置细粒度agent频率
    agent_frequencies = {
        'market_data': 'daily',       # 市场数据每日更新
        'technical': 'daily',         # 技术分析每日更新  
        'fundamentals': 'weekly',     # 基本面分析每周更新
        'sentiment': 'daily',         # 情绪分析每日更新
        'valuation': 'monthly',       # 估值分析每月更新
        'macro': 'weekly',            # 宏观分析每周更新
        'portfolio': 'daily'          # 投资组合管理每日更新
    }
    
    print("=" * 60)
    print("智能回测系统 - 细粒度频率控制")
    print("=" * 60)
    print(f"股票代码: {ticker}")
    print(f"回测期间: {start_date} 到 {end_date}")
    print(f"初始资金: ${initial_capital:,}")
    print(f"Agent频率配置:")
    for agent, freq in agent_frequencies.items():
        print(f"  {agent:12s}: {freq}")
    
    # 创建智能回测器
    backtester = IntelligentBacktester(
        agent=run_hedge_fund,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        num_of_news=5,
        agent_frequencies=agent_frequencies
    )
    
    # 运行回测
    print("\n开始运行回测...")
    backtester.run_backtest()
    
    # 分析性能
    print("\n分析性能...")
    performance_df = backtester.analyze_performance(save_plots=True)
    
    print("\n回测完成！")
    print("="*60)

if __name__ == "__main__":
    main()