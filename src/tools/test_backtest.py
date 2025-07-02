import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))


class SimplifiedBacktester:
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.portfolio = {"cash": initial_capital, "stock": 0}
        self.portfolio_values = []

    def execute_trade(self, action, quantity, current_price):
        """执行交易，验证组合约束"""
        if action == "buy" and quantity > 0:
            cost = quantity * current_price
            if cost <= self.portfolio["cash"]:
                self.portfolio["stock"] += quantity
                self.portfolio["cash"] -= cost
                return quantity
            else:
                # 计算最大可买数量
                max_quantity = int(self.portfolio["cash"] // current_price)
                if max_quantity > 0:
                    self.portfolio["stock"] += max_quantity
                    self.portfolio["cash"] -= max_quantity * current_price
                    return max_quantity
                return 0
        elif action == "sell" and quantity > 0:
            quantity = min(quantity, self.portfolio["stock"])
            if quantity > 0:
                self.portfolio["cash"] += quantity * current_price
                self.portfolio["stock"] -= quantity
                return quantity
            return 0
        return 0

    def analyze_performance(self, price_data):
        """分析回测性能"""
        portfolio_values = []
        daily_returns = []

        for date, price in price_data.iterrows():
            total_value = self.portfolio["cash"] + \
                self.portfolio["stock"] * price['close']

            # 计算日收益率
            if portfolio_values:
                daily_return = (
                    total_value / portfolio_values[-1]["Portfolio Value"] - 1) * 100
            else:
                daily_return = 0

            portfolio_values.append({
                "Date": date,
                "Portfolio Value": total_value,
                "Daily Return": daily_return
            })
            daily_returns.append(daily_return)

        # 转换为DataFrame
        performance_df = pd.DataFrame(portfolio_values).set_index("Date")

        # 计算累计收益率
        performance_df["Cumulative Return"] = (
            performance_df["Portfolio Value"] / self.initial_capital - 1) * 100

        # 可视化
        self._plot_performance(performance_df)

        # 计算性能指标
        total_return = (performance_df["Portfolio Value"].iloc[-1] -
                        self.initial_capital) / self.initial_capital
        daily_returns_series = pd.Series(daily_returns)
        sharpe_ratio = (daily_returns_series.mean() / daily_returns_series.std()
                        ) * (252 ** 0.5) if daily_returns_series.std() != 0 else 0

        # 计算最大回撤
        rolling_max = performance_df["Portfolio Value"].cummax()
        drawdown = (performance_df["Portfolio Value"] / rolling_max - 1) * 100
        max_drawdown = drawdown.min()

        print("\n=== Backtest Results ===")
        print(f"Initial Capital: {self.initial_capital:,.2f}")
        print(f"Final Total Value: {performance_df['Portfolio Value'].iloc[-1]:,.2f}")
        print(f"Total Return: {total_return * 100:.2f}%")
        print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        print(f"Max Drawdown: {max_drawdown:.2f}%")

        return performance_df

    def _plot_performance(self, performance_df):
        """绘制回测结果图表"""
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(12, 10), height_ratios=[1, 1])
        fig.suptitle("Backtest Results Analysis", fontsize=12)

        # Plot portfolio value chart
        portfolio_values_k = performance_df["Portfolio Value"] / 1000
        line1 = ax1.plot(performance_df.index,
                         portfolio_values_k, label="Portfolio Value", marker='o')
        ax1.set_ylabel("Portfolio Value (K CNY)")
        ax1.set_title("Portfolio Value Changes")
        ax1.grid(True)

        # Add labels on data points
        for x, y in zip(performance_df.index, portfolio_values_k):
            ax1.annotate(f'{y:.1f}K',
                         (x, y),
                         textcoords="offset points",
                         xytext=(0, 10),
                         ha='center',
                         fontsize=8)

        # Plot cumulative return chart
        line2 = ax2.plot(performance_df.index,
                         performance_df["Cumulative Return"],
                         label="Cumulative Return",
                         color='green',
                         marker='o')
        ax2.set_ylabel("Cumulative Return (%)")
        ax2.set_title("Cumulative Return Changes")
        ax2.grid(True)

        # Add labels on data points
        for x, y in zip(performance_df.index, performance_df["Cumulative Return"]):
            ax2.annotate(f'{y:.2f}%',
                         (x, y),
                         textcoords="offset points",
                         xytext=(0, 10),
                         ha='center',
                         fontsize=8)

        plt.xlabel("Date")
        plt.tight_layout()
        plt.show()


def generate_mock_price_data(start_date, days):
    """生成模拟价格数据"""
    dates = pd.date_range(start_date, periods=days, freq='B')
    # 创建一个更有趣的价格序列，包含上涨和下跌
    base_price = 100
    price_changes = [0, 2, -1, 3, -2, 1, 4, -3, 2, 1]  # 10天的价格变化
    prices = []
    current_price = base_price
    for change in price_changes:
        current_price += change
        prices.append(current_price)
    return pd.DataFrame({'date': dates, 'close': prices}).set_index('date')


def test_backtest():
    """测试回测系统的交易执行逻辑"""
    # 设置初始参数
    initial_capital = 100000
    start_date = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')

    # 生成模拟价格数据
    price_data = generate_mock_price_data(start_date, 10)

    # 创建回测器实例
    backtester = SimplifiedBacktester(initial_capital)

    # 模拟一系列交易决策
    decisions = [
        ("buy", 200),   # 第1天：买入200股
        ("hold", 0),    # 第2天：持有
        ("buy", 300),   # 第3天：买入300股
        ("hold", 0),    # 第4天：持有
        ("sell", 150),  # 第5天：卖出150股
        ("hold", 0),    # 第6天：持有
        ("buy", 250),   # 第7天：买入250股
        ("sell", 400),  # 第8天：卖出400股
        ("hold", 0),    # 第9天：持有
        ("buy", 200),   # 第10天：买入200股
    ]

    # 执行交易
    for (date, price), (action, quantity) in zip(price_data.iterrows(), decisions):
        executed_quantity = backtester.execute_trade(
            action, quantity, price['close'])
        print(f"Date: {date.strftime('%Y-%m-%d')}, Price: {price['close']:.2f}, "
              f"Action: {action}, Planned Qty: {quantity}, Executed: {executed_quantity}, "
              f"Cash: {backtester.portfolio['cash']:.2f}, Position: {backtester.portfolio['stock']}")

    # 分析性能
    performance_df = backtester.analyze_performance(price_data)


if __name__ == "__main__":
    test_backtest()
