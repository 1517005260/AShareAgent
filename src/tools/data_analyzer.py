import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.tools.api import get_price_history


def analyze_stock_data(symbol: str, start_date: str = None, end_date: str = None):
    """
    获取股票历史数据，计算技术指标，并保存为CSV文件

    Args:
        symbol: 股票代码
        start_date: 开始日期，格式：YYYY-MM-DD
        end_date: 结束日期，格式：YYYY-MM-DD
    """
    # 获取历史数据
    df = get_price_history(symbol, start_date, end_date)

    if df.empty:
        print("未获取到数据")
        return

    # 计算额外的技术指标
    # 1. 移动平均线
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma60'] = df['close'].rolling(window=60).mean()

    # 2. MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['signal_line'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['signal_line']

    # 3. RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # 4. 布林带
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)

    # 5. 成交量相关指标
    df['volume_ma5'] = df['volume'].rolling(window=5).mean()
    df['volume_ma20'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma5']

    # 6. 价格动量指标
    df['price_momentum'] = df['close'].pct_change(periods=5)
    df['price_acceleration'] = df['price_momentum'].diff()

    # 7. 波动率指标
    df['daily_return'] = df['close'].pct_change()
    df['volatility_5d'] = df['daily_return'].rolling(
        window=5).std() * np.sqrt(252)
    df['volatility_20d'] = df['daily_return'].rolling(
        window=20).std() * np.sqrt(252)

    # 保存为CSV文件
    output_file = f"{symbol}_analysis_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(output_file, index=False)
    print(f"数据已保存到文件: {output_file}")

    # 打印基本统计信息
    print("\n基本统计信息:")
    print(f"数据时间范围: {df['date'].min()} 至 {df['date'].max()}")
    print(f"总记录数: {len(df)}")
    print("\nNaN值统计:")
    print(df.isna().sum())


if __name__ == "__main__":
    # 测试代码
    symbol = "600519"  # 贵州茅台
    current_date = datetime.now()
    end_date = current_date.strftime("%Y-%m-%d")  # 使用今天作为结束日期
    start_date = (current_date - timedelta(days=365)).strftime("%Y-%m-%d")

    print(f"分析时间范围: {start_date} 至 {end_date}")
    analyze_stock_data(symbol, start_date, end_date)
