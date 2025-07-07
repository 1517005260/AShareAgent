"""
缓存管理器 - 智能缓存和数据重用
"""

import pandas as pd
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as ConcurrentTimeoutError
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
        """获取缓存的价格数据，增加错误处理和回退策略"""
        cache_key = f"{ticker}_{start_date}_{end_date}"
        
        if cache_key in self._price_data_cache:
            self._cache_hits += 1
            return self._price_data_cache[cache_key]
        
        self._cache_misses += 1
        
        # 尝试获取数据，如果失败则尝试获取更大的时间范围
        df = None
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # 使用线程池添加超时控制
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(get_price_data, ticker, start_date, end_date)
                    try:
                        df = future.result(timeout=30)  # 30秒超时
                        if df is not None:
                            if not df.empty:
                                self._price_data_cache[cache_key] = df
                                return df
                    except ConcurrentTimeoutError:
                        print(f"数据获取超时 (尝试 {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(2 ** attempt)
                        continue
            except Exception as e:
                print(f"数据获取失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
        
        # 如果所有尝试都失败，尝试从已有缓存中找到相似的数据
        if df is None or df.empty:
            df = self._get_fallback_data(ticker, start_date, end_date)
            
        return df
    
    def _get_fallback_data(self, ticker: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """从缓存中获取回退数据"""
        # 寻找相同ticker的其他时间范围数据
        for key, cached_df in self._price_data_cache.items():
            if key.startswith(ticker) and cached_df is not None:
                if not cached_df.empty:
                    # 尝试过滤出所需日期范围的数据
                    try:
                        cached_df['date'] = pd.to_datetime(cached_df['date'])
                        filtered_df = cached_df[
                            (cached_df['date'] >= start_date) & 
                            (cached_df['date'] <= end_date)
                        ]
                        if not filtered_df.empty:
                            return filtered_df
                    except:
                        continue
        
        return None
    
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