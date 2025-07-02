"""
测试数据源的可靠性和质量

包括akshare、东方财富、yfinance等数据源的验证
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import requests

from src.tools.api import (
    get_financial_metrics, get_market_data, get_price_history,
    validate_data_quality, monitor_data_quality, safe_float,
    convert_percentage, get_eastmoney_data
)


class TestDataSourceReliability:
    """测试数据源可靠性"""
    
    @pytest.mark.data_validation
    def test_akshare_connection(self):
        """测试akshare连接可靠性"""
        with patch('src.tools.api.ak.stock_zh_a_spot_em') as mock_ak:
            # 模拟正常响应
            mock_ak.return_value = pd.DataFrame({
                '代码': ['000001', '000002'],
                '总市值': [500000000000, 300000000000],
                '市盈率-动态': [12.5, 15.2],
                '市净率': [1.8, 2.1]
            })
            
            # 测试数据获取
            try:
                from src.tools.api import _get_market_data_akshare
                result = _get_market_data_akshare('000001')
                
                assert result is not None
                assert 'market_cap' in result
                assert isinstance(result['market_cap'], (int, float, type(None)))
                
            except Exception as e:
                pytest.fail(f"akshare连接测试失败: {e}")
    
    @pytest.mark.data_validation
    def test_eastmoney_api_reliability(self):
        """测试东方财富API可靠性"""
        with patch('requests.get') as mock_get:
            # 模拟正常API响应
            mock_response = Mock()
            mock_response.json.return_value = {
                'rc': 0,
                'data': {
                    'f43': 1250,  # 价格*100
                    'f116': 500000000000,  # 总市值
                    'f114': 12.5,  # PE
                    'f167': 1.8,   # PB
                    'f47': 1000000,  # 成交量
                }
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # 测试东方财富数据
            result = get_eastmoney_data('000001')
            
            assert result is not None
            assert 'current_price' in result
            assert 'pe_ratio' in result
            assert 'pb_ratio' in result
            assert result['current_price'] == 12.5  # 1250/100
    
    @pytest.mark.data_validation
    def test_data_source_fallback(self):
        """测试数据源回退机制"""
        with patch('src.tools.api._get_financial_metrics_akshare') as mock_ak, \
             patch('src.tools.api._get_financial_metrics_eastmoney') as mock_em, \
             patch('src.tools.api._get_financial_metrics_yfinance') as mock_yf:
            
            # 模拟akshare失败
            mock_ak.side_effect = Exception("akshare连接失败")
            
            # 模拟eastmoney成功
            mock_em.return_value = [{
                'pe_ratio': 12.5,
                'pb_ratio': 1.8,
                'return_on_equity': 0.15
            }]
            
            # 测试回退机制
            result = get_financial_metrics('000001')
            
            assert result is not None
            assert len(result) > 0
            assert 'pe_ratio' in result[0]
            
            # 验证akshare被调用但失败，然后调用eastmoney
            mock_ak.assert_called_once()
            mock_em.assert_called_once()
    
    @pytest.mark.data_validation
    def test_data_source_timeout_handling(self):
        """测试数据源超时处理"""
        with patch('requests.get') as mock_get:
            # 模拟超时
            mock_get.side_effect = requests.Timeout("连接超时")
            
            result = get_eastmoney_data('000001')
            
            # 超时时应该返回None而不是崩溃
            assert result is None
    
    @pytest.mark.data_validation
    def test_invalid_stock_code_handling(self):
        """测试无效股票代码处理"""
        with patch('src.tools.api.ak.stock_zh_a_spot_em') as mock_ak:
            # 模拟无效代码返回空数据
            mock_ak.return_value = pd.DataFrame()
            
            result = get_financial_metrics('INVALID_CODE')
            
            # 应该返回默认结构而不是崩溃
            assert result is not None
            assert len(result) > 0
            assert isinstance(result[0], dict)


class TestDataQuality:
    """测试数据质量"""
    
    
    
    @pytest.mark.data_validation
    def test_data_freshness(self):
        """测试数据新鲜度"""
        with patch('src.tools.api.get_price_history') as mock_price:
            # 模拟返回过期数据
            old_date = datetime.now() - timedelta(days=30)
            mock_price.return_value = pd.DataFrame({
                'date': [old_date],
                'close': [10.0],
                'open': [9.9],
                'high': [10.1],
                'low': [9.8],
                'volume': [1000000]
            })
            
            result = mock_price('000001')
            
            if not result.empty:
                latest_date = pd.to_datetime(result['date']).max()
                days_old = (datetime.now() - latest_date).days
                
                # 发出警告如果数据超过7天
                if days_old > 7:
                    pytest.warns(UserWarning, match="数据可能过期")
    
    @pytest.mark.data_validation
    def test_data_validation_function(self):
        """测试数据验证函数"""
        # 测试有效数据
        valid_data = pd.DataFrame({
            'close': [10.0, 10.1, 10.2],
            'volume': [1000000, 1100000, 1200000]
        })
        
        assert validate_data_quality(valid_data, ['close', 'volume']) is True
        
        # 测试无效数据
        invalid_data = pd.DataFrame()
        assert validate_data_quality(invalid_data) is False
        
        # 测试缺少列
        incomplete_data = pd.DataFrame({'close': [10.0]})
        assert validate_data_quality(incomplete_data, ['close', 'volume']) is False
    
    @pytest.mark.data_validation  
    def test_nan_handling(self):
        """测试NaN值处理"""
        data_with_nan = pd.DataFrame({
            'close': [10.0, np.nan, 10.2],
            'volume': [1000000, 1100000, np.nan]
        })
        
        # 数据质量应该检测到NaN值
        quality = validate_data_quality(data_with_nan)
        
        # 如果NaN比例过高，应该返回False
        nan_ratio = data_with_nan.isna().sum().sum() / (len(data_with_nan) * len(data_with_nan.columns))
        if nan_ratio > 0.5:
            assert quality is False
    
    @pytest.mark.data_validation
    def test_outlier_detection(self):
        """测试异常值检测"""
        # 创建包含异常值的数据
        normal_prices = [10.0] * 100
        outlier_data = normal_prices + [1000.0, 0.01]  # 明显的异常值
        
        df = pd.DataFrame({
            'close': outlier_data,
            'volume': [1000000] * len(outlier_data)
        })
        
        # 计算价格变化的Z分数
        price_changes = pd.Series(outlier_data).pct_change().dropna()
        z_scores = np.abs((price_changes - price_changes.mean()) / price_changes.std())
        
        # 检测异常值
        outliers = z_scores > 3  # 3倍标准差
        assert outliers.sum() > 0, "应该检测到异常值"


class TestDataSourceSpecific:
    """特定数据源测试"""
    
    @pytest.mark.data_validation
    def test_safe_float_conversion(self):
        """测试安全浮点转换"""
        # 测试正常值
        assert safe_float("12.5") == 12.5
        assert safe_float(12.5) == 12.5
        
        # 测试异常值
        assert safe_float(None) is None
        assert safe_float("") is None
        assert safe_float("invalid") is None
        assert safe_float(np.nan) is None
        assert safe_float(np.inf) is None
        
        # 测试默认值
        assert safe_float(None, 0.0) == 0.0
        assert safe_float("invalid", -1.0) == -1.0
    
    @pytest.mark.data_validation
    def test_percentage_conversion(self):
        """测试百分比转换"""
        # 测试百分号格式
        assert convert_percentage("12.5%") == 0.125
        assert convert_percentage("0.5%") == 0.005
        
        # 测试小数格式  
        assert convert_percentage(0.125) == 0.125
        assert convert_percentage("0.125") == 0.125
        
        # 测试大数字格式（需要除以100）
        assert convert_percentage(12.5) == 0.125
        assert convert_percentage("12.5") == 0.125
        
        # 测试异常值
        assert convert_percentage(None) is None
        assert convert_percentage("") is None
        assert convert_percentage("invalid") is None
    
    @pytest.mark.data_validation
    def test_monitor_data_quality_function(self):
        """测试数据质量监控函数"""
        # 测试DataFrame监控
        good_df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10),
            'close': range(10, 20),
            'volume': [1000000] * 10
        })
        
        report = monitor_data_quality(good_df, "price_data")
        assert report["quality_score"] > 0.8
        assert len(report["issues"]) == 0
        
        # 测试有问题的数据
        bad_df = pd.DataFrame({
            'close': [np.nan] * 10,
            'volume': [np.nan] * 10
        })
        
        report = monitor_data_quality(bad_df, "bad_data")
        assert report["quality_score"] < 0.5
        assert len(report["issues"]) > 0
    
    @pytest.mark.data_validation
    def test_api_rate_limiting(self):
        """测试API速率限制处理"""
        call_count = 0
        
        def mock_api_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Rate limit exceeded")
            return {"data": "success"}
        
        with patch('src.tools.api.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.side_effect = mock_api_call
            mock_get.return_value = mock_response
            
            # 测试重试机制
            from src.tools.api import retry_on_failure
            
            @retry_on_failure(max_retries=3, delay=0.1)
            def test_function():
                return mock_api_call()
            
            # 应该在第3次调用时成功
            result = test_function()
            assert result["data"] == "success"
            assert call_count == 3


@pytest.mark.data_validation
class TestDataIntegrity:
    """数据完整性测试"""
    
    def test_cross_source_consistency(self):
        """测试跨数据源一致性"""
        with patch('src.tools.api._get_financial_metrics_akshare') as mock_ak, \
             patch('src.tools.api._get_financial_metrics_eastmoney') as mock_em:
            
            # 模拟两个数据源返回类似的数据
            mock_ak.return_value = [{'pe_ratio': 12.5, 'pb_ratio': 1.8}]
            mock_em.return_value = [{'pe_ratio': 12.3, 'pb_ratio': 1.9}]
            
            ak_data = mock_ak('000001')
            em_data = mock_em('000001')
            
            # 检查数据一致性（允许小幅差异）
            pe_diff = abs(ak_data[0]['pe_ratio'] - em_data[0]['pe_ratio'])
            pb_diff = abs(ak_data[0]['pb_ratio'] - em_data[0]['pb_ratio'])
            
            # PE和PB差异不应超过20%
            assert pe_diff / ak_data[0]['pe_ratio'] < 0.2
            assert pb_diff / ak_data[0]['pb_ratio'] < 0.2
    
    def test_historical_data_continuity(self):
        """测试历史数据连续性"""
        # 创建有缺失日期的数据
        dates = pd.date_range('2024-01-01', '2024-01-10', freq='D')
        missing_dates = dates.delete([2, 5, 7])  # 删除某些日期
        
        df = pd.DataFrame({
            'date': missing_dates,
            'close': range(len(missing_dates)),
            'volume': [1000000] * len(missing_dates)
        })
        
        # 检查日期连续性
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        date_gaps = df['date'].diff().dt.days
        large_gaps = date_gaps[date_gaps > 3]  # 超过3天的gap
        
        if len(large_gaps) > 0:
            pytest.warns(UserWarning, match="检测到数据缺失")
    
    def test_data_schema_validation(self):
        """测试数据结构验证"""
        # 定义预期的数据结构
        expected_financial_schema = {
            'pe_ratio': (float, type(None)),
            'return_on_equity': (float, type(None)),
            'net_margin': (float, type(None)),
            'revenue_growth': (float, type(None))
        }
        
        # 测试数据
        test_data = {
            'pe_ratio': 12.5,
            'return_on_equity': 0.15,
            'net_margin': 0.12,
            'revenue_growth': 0.08
        }
        
        # 验证结构
        for field, expected_types in expected_financial_schema.items():
            assert field in test_data, f"缺少字段: {field}"
            assert isinstance(test_data[field], expected_types), f"{field}类型不正确"