"""
智能回测器入口点 - 向后兼容
重新导向到新的模块化结构
"""

# 导入新的模块化回测器
from .backtesting import IntelligentBacktester, Trade, PerformanceMetrics, RiskMetrics
from .tools.api import get_price_data

# 为了向后兼容，保留原有的导入路径和类名映射
Backtester = IntelligentBacktester

__all__ = ['IntelligentBacktester', 'Backtester', 'Trade', 'PerformanceMetrics', 'RiskMetrics', 'get_price_data']

# 如果直接运行此文件，转发到新的模块
if __name__ == "__main__":
    import subprocess
    import sys
    import os
    
    # 运行新的backtester模块
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backtester_path = os.path.join(current_dir, 'backtesting', 'backtester.py')
    
    # 传递所有命令行参数
    cmd = [sys.executable, backtester_path] + sys.argv[1:]
    subprocess.run(cmd)