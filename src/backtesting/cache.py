"""
缓存管理器 - 智能缓存和数据重用
"""

import pandas as pd
from typing import Dict, Any, Optional
try:
    from src.tools.api import get_price_data
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.tools.api import get_price_data


class CacheManager:
    """智能缓存管理器"""
    
    def __init__(self):
        self._price_data_cache: Dict[str, pd.DataFrame] = {}
        self._agent_result_cache: Dict[str, Any] = {}
        self._market_condition_cache: Dict[str, Any] = {}
        self._cache_hits = 0
        self._cache_misses = 0
    
    def get_cached_price_data(self, ticker: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取缓存的价格数据"""
        cache_key = f"{ticker}_{start_date}_{end_date}"
        
        if cache_key in self._price_data_cache:
            return self._price_data_cache[cache_key]
        
        df = get_price_data(ticker, start_date, end_date)
        
        if df is not None and not df.empty:
            self._price_data_cache[cache_key] = df
            
        return df
    
    def get_agent_result(self, cache_key: str) -> Optional[Any]:
        """获取缓存的agent结果"""
        if cache_key in self._agent_result_cache:
            self._cache_hits += 1
            return self._agent_result_cache[cache_key]
        
        self._cache_misses += 1
        return None
    
    def cache_agent_result(self, cache_key: str, result: Any) -> None:
        """缓存agent结果"""
        self._agent_result_cache[cache_key] = result
    
    def get_last_decision(self) -> Dict[str, Any]:
        """获取最后一个缓存的决策"""
        if self._agent_result_cache:
            last_result = list(self._agent_result_cache.values())[-1]
            last_result["execution_type"] = "cached"
            return last_result
        else:
            return {
                "decision": {"action": "hold", "quantity": 0},
                "analyst_signals": {},
                "execution_type": "default"
            }
    
    @property
    def cache_hits(self) -> int:
        return self._cache_hits
    
    @property
    def cache_misses(self) -> int:
        return self._cache_misses
    
    @property
    def cache_hit_rate(self) -> float:
        total = self._cache_hits + self._cache_misses
        return (self._cache_hits / total * 100) if total > 0 else 0