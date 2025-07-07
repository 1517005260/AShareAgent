"""
量化基准实现
提供5种常见的量化交易基准对比指标
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

try:
    from src.tools.api import get_price_data
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.tools.api import get_price_data


class BenchmarkCalculator:
    """基准计算器"""
    
    AVAILABLE_BENCHMARKS = {
        'spe': 'SPE策略 (买入并持有策略)',
        'csi300': 'CSI300指数',
        'equal_weight': '等权重策略',
        'momentum': '动量策略',
        'mean_reversion': '均值回归策略'
    }
    
    def __init__(self, benchmark_type: str, initial_capital: float = 100000):
        """
        初始化基准计算器
        
        Args:
            benchmark_type: 基准类型 ('spe', 'csi300', 'equal_weight', 'momentum', 'mean_reversion')
            initial_capital: 初始资金
        """
        if benchmark_type not in self.AVAILABLE_BENCHMARKS:
            raise ValueError(f"不支持的基准类型: {benchmark_type}. 可选: {list(self.AVAILABLE_BENCHMARKS.keys())}")
        
        self.benchmark_type = benchmark_type
        self.initial_capital = initial_capital
        self.logger = logging.getLogger(__name__)
        
    def calculate_benchmark_returns(self, ticker: str, start_date: str, end_date: str) -> List[float]:
        """
        计算基准收益率
        
        Args:
            ticker: 主要股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            基准日收益率列表
        """
        if self.benchmark_type == 'spe':
            return self._calculate_spe_returns(ticker, start_date, end_date)
        elif self.benchmark_type == 'csi300':
            return self._calculate_csi300_returns(start_date, end_date)
        elif self.benchmark_type == 'equal_weight':
            return self._calculate_equal_weight_returns(ticker, start_date, end_date)
        elif self.benchmark_type == 'momentum':
            return self._calculate_momentum_returns(ticker, start_date, end_date)
        elif self.benchmark_type == 'mean_reversion':
            return self._calculate_mean_reversion_returns(ticker, start_date, end_date)
        else:
            return []
    
    def _calculate_spe_returns(self, ticker: str, start_date: str, end_date: str) -> List[float]:
        """
        SPE策略 (买入并持有)
        简单买入并持有策略，作为最基础的基准
        """
        try:
            df = get_price_data(ticker, start_date, end_date)
            if df is None or df.empty:
                self.logger.warning(f"无法获取{ticker}的价格数据")
                return []
            
            # 确保date列是datetime类型
            df['date'] = pd.to_datetime(df['date'])
            
            # 筛选出回测期间的数据
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            mask = (df['date'] >= start_dt) & (df['date'] <= end_dt)
            filtered_df = df[mask].copy()
            
            if filtered_df.empty:
                self.logger.warning(f"筛选后无{ticker}数据在期间{start_date}到{end_date}")
                return []
            
            # 计算日收益率
            filtered_df['daily_return'] = filtered_df['close'].pct_change()
            returns = filtered_df['daily_return'].fillna(0).tolist()
            
            self.logger.info(f"SPE基准: 筛选出{len(returns)}个交易日的数据")
            return returns
        except Exception as e:
            self.logger.error(f"计算SPE基准失败: {e}")
            return []
    
    def _calculate_csi300_returns(self, start_date: str, end_date: str) -> List[float]:
        """
        CSI300指数基准
        中国A股市场最重要的基准指数
        """
        try:
            # 使用CSI300指数代码
            df = get_price_data('000300', start_date, end_date)
            if df is None or df.empty:
                self.logger.warning("无法获取CSI300指数数据")
                return []
            
            df['daily_return'] = df['close'].pct_change()
            return df['daily_return'].fillna(0).tolist()
        except Exception as e:
            self.logger.error(f"计算CSI300基准失败: {e}")
            return []
    
    def _calculate_equal_weight_returns(self, ticker: str, start_date: str, end_date: str) -> List[float]:
        """
        等权重策略
        对一篮子股票进行等权重配置
        """
        try:
            # 选择代表性股票组合 (包括主要股票和一些大盘股)
            stock_list = [ticker, '000001', '000002', '600036', '600519']
            
            returns_data = []
            for stock in stock_list:
                try:
                    df = get_price_data(stock, start_date, end_date)
                    if df is not None:
                        if not df.empty:
                            df['daily_return'] = df['close'].pct_change()
                            returns_data.append(df['daily_return'].fillna(0))
                except:
                    continue
            
            if not returns_data:
                return []
            
            # 计算等权重收益率
            returns_df = pd.concat(returns_data, axis=1)
            equal_weight_returns = returns_df.mean(axis=1, skipna=True)
            return equal_weight_returns.fillna(0).tolist()
        except Exception as e:
            self.logger.error(f"计算等权重基准失败: {e}")
            return []
    
    def _calculate_momentum_returns(self, ticker: str, start_date: str, end_date: str) -> List[float]:
        """
        动量策略
        基于价格动量的交易策略
        """
        try:
            df = get_price_data(ticker, start_date, end_date)
            if df is None or df.empty:
                return []
            
            # 计算20日动量指标
            df['momentum'] = df['close'].pct_change(20)
            df['position'] = np.where(df['momentum'] > 0, 1, 0)  # 动量为正时持有
            df['strategy_return'] = df['position'].shift(1) * df['close'].pct_change()
            
            return df['strategy_return'].fillna(0).tolist()
        except Exception as e:
            self.logger.error(f"计算动量基准失败: {e}")
            return []
    
    def _calculate_mean_reversion_returns(self, ticker: str, start_date: str, end_date: str) -> List[float]:
        """
        均值回归策略
        基于价格均值回归的交易策略
        """
        try:
            df = get_price_data(ticker, start_date, end_date)
            if df is None or df.empty:
                return []
            
            # 计算20日移动平均和标准差
            df['ma20'] = df['close'].rolling(20).mean()
            df['std20'] = df['close'].rolling(20).std()
            
            # 计算z-score
            df['z_score'] = (df['close'] - df['ma20']) / df['std20']
            
            # 均值回归信号：价格偏离均值时反向操作
            df['position'] = np.where(df['z_score'] < -1, 1,  # 超卖时买入
                                    np.where(df['z_score'] > 1, -1, 0))  # 超买时卖出
            
            df['strategy_return'] = df['position'].shift(1) * df['close'].pct_change()
            
            return df['strategy_return'].fillna(0).tolist()
        except Exception as e:
            self.logger.error(f"计算均值回归基准失败: {e}")
            return []
    
    def get_benchmark_info(self) -> Dict[str, Any]:
        """获取基准信息"""
        return {
            'type': self.benchmark_type,
            'name': self.AVAILABLE_BENCHMARKS[self.benchmark_type],
            'description': self._get_benchmark_description()
        }
    
    def _get_benchmark_description(self) -> str:
        """获取基准描述"""
        descriptions = {
            'spe': '买入并持有策略，长期持有目标股票，是最基础的投资基准',
            'csi300': 'CSI300指数，代表中国A股市场300只最大且流动性最好的股票',
            'equal_weight': '等权重策略，对选定股票池进行等权重配置，降低个股风险',
            'momentum': '动量策略，基于价格趋势进行交易，追涨杀跌',
            'mean_reversion': '均值回归策略，基于价格偏离均值时的修正进行交易'
        }
        return descriptions.get(self.benchmark_type, '')

    @staticmethod
    def list_available_benchmarks() -> Dict[str, str]:
        """列出所有可用的基准"""
        return BenchmarkCalculator.AVAILABLE_BENCHMARKS.copy()