"""
测试数据管道集成

测试从外部数据源到内部数据处理的完整数据流
"""

import pytest
import json
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.tools.api import (
    get_financial_metrics, get_market_data, get_price_history
)
from tests.mocks import (
    MockAkshareData, MockEastmoneyAPI, MockNewsData, MockFinancialData
)


class TestDataIngestionPipeline:
    """测试数据摄取管道"""
    
    @pytest.mark.integration
    def test_akshare_data_pipeline(self):
        """测试akshare数据管道"""
        with patch('src.tools.api.ak.stock_zh_a_spot_em') as mock_ak:
            # 模拟akshare数据
            mock_ak.return_value = MockAkshareData.stock_zh_a_spot_em()
            
            try:
                # 测试数据获取
                from src.tools.api import _get_market_data_akshare
                result = _get_market_data_akshare('000001')
                
                # 验证数据结构
                assert result is not None
                assert isinstance(result, dict)
                
                # 验证必要字段
                expected_fields = ['market_cap', 'pe_ratio', 'pb_ratio', 'current_price']
                for field in expected_fields:
                    if field in result:
                        assert isinstance(result[field], (int, float, type(None)))
                
            except ImportError:
                pytest.skip("akshare模块不可用")
    
    @pytest.mark.integration
    def test_eastmoney_data_pipeline(self):
        """测试东方财富数据管道"""
        with patch('requests.get') as mock_requests:
            # 模拟东方财富API响应
            mock_response = Mock()
            mock_response.json.return_value = MockEastmoneyAPI.get_stock_data('000001')
            mock_response.status_code = 200
            mock_requests.return_value = mock_response
            
            try:
                from src.tools.api import get_eastmoney_data
                result = get_eastmoney_data('000001', raw_response=True)
                
                # 验证数据结构
                assert result is not None
                assert 'rc' in result
                assert result['rc'] == 0
                assert 'data' in result
                
                # 验证数据字段
                data = result['data']
                assert 'f43' in data  # 价格
                assert 'f116' in data  # 总市值
                assert 'f114' in data  # 市盈率
                
            except ImportError:
                pytest.skip("requests模块不可用")
    
    @pytest.mark.integration
    def test_news_data_pipeline(self, mock_external_apis):
        """测试新闻数据管道"""
        # 模拟新闻数据获取
        mock_news = MockNewsData.get_stock_news('000001')
        
        # 验证新闻数据结构
        assert isinstance(mock_news, list)
        assert len(mock_news) > 0
        
        for news_item in mock_news:
            # 验证必要字段
            required_fields = ['title', 'content', 'sentiment_score', 'publish_time', 'source']
            for field in required_fields:
                assert field in news_item
            
            # 验证数据类型
            assert isinstance(news_item['title'], str)
            assert isinstance(news_item['content'], str)
            assert isinstance(news_item['sentiment_score'], (int, float))
            assert -1.0 <= news_item['sentiment_score'] <= 1.0
    
    @pytest.mark.integration
    def test_financial_metrics_integration(self):
        """测试财务指标数据集成"""
        # 模拟财务数据
        financial_data = MockFinancialData.get_financial_metrics('000001')
        
        # 验证数据完整性
        assert 'basic_info' in financial_data
        assert 'profitability' in financial_data
        assert 'growth' in financial_data
        assert 'financial_health' in financial_data
        assert 'valuation' in financial_data
        
        # 验证基本信息
        basic_info = financial_data['basic_info']
        assert 'stock_code' in basic_info
        assert 'stock_name' in basic_info
        assert 'market_cap' in basic_info
        
        # 验证盈利能力指标
        profitability = financial_data['profitability']
        assert 'roe' in profitability
        assert 'roa' in profitability
        assert 'net_margin' in profitability
        
        # 验证成长性指标
        growth = financial_data['growth']
        assert 'revenue_growth_yoy' in growth
        assert 'profit_growth_yoy' in growth
        
        # 验证财务健康指标
        health = financial_data['financial_health']
        assert 'current_ratio' in health
        assert 'debt_to_equity' in health
        
        # 验证估值指标
        valuation = financial_data['valuation']
        assert 'pe_ratio' in valuation
        assert 'pb_ratio' in valuation
    
    @pytest.mark.integration
    def test_price_data_pipeline(self):
        """测试价格数据管道"""
        # 模拟历史价格数据
        price_data = MockAkshareData.stock_zh_a_hist('000001')
        
        # 验证数据结构
        assert isinstance(price_data, pd.DataFrame)
        assert len(price_data) > 0
        
        # 验证必要列
        required_columns = ['日期', '开盘', '收盘', '最高', '最低', '成交量']
        for col in required_columns:
            assert col in price_data.columns
        
        # 验证数据质量
        for idx, row in price_data.iterrows():
            # 价格关系验证
            assert row['最高'] >= max(row['开盘'], row['收盘'])
            assert row['最低'] <= min(row['开盘'], row['收盘'])
            assert row['成交量'] >= 0
            
            # 价格合理性验证
            assert row['开盘'] > 0
            assert row['收盘'] > 0
            assert row['最高'] > 0
            assert row['最低'] > 0


class TestDataTransformationPipeline:
    """测试数据转换管道"""
    
    @pytest.mark.integration
    def test_price_data_transformation(self):
        """测试价格数据转换"""
        # 获取原始价格数据
        raw_data = MockAkshareData.stock_zh_a_hist('000001')
        
        # 计算技术指标
        # 简单移动平均
        raw_data['MA5'] = raw_data['收盘'].rolling(window=5).mean()
        raw_data['MA20'] = raw_data['收盘'].rolling(window=20).mean()
        
        # 涨跌幅计算
        raw_data['涨跌幅_calc'] = raw_data['收盘'].pct_change() * 100
        
        # 验证转换结果
        assert 'MA5' in raw_data.columns
        assert 'MA20' in raw_data.columns
        assert '涨跌幅_calc' in raw_data.columns
        
        # 验证计算正确性
        ma5_values = raw_data['MA5'].dropna()
        assert len(ma5_values) > 0
        assert all(ma5_values > 0)
        
        # 验证涨跌幅计算
        pct_change = raw_data['涨跌幅_calc'].dropna()
        assert len(pct_change) > 0
        # 涨跌幅应该在合理范围内（-50%到50%）
        assert all(abs(pct) <= 50 for pct in pct_change)
    
    @pytest.mark.integration
    def test_financial_metrics_normalization(self):
        """测试财务指标标准化"""
        financial_data = MockFinancialData.get_financial_metrics('000001')
        
        # 提取关键指标
        metrics = {
            'pe_ratio': financial_data['valuation']['pe_ratio'],
            'pb_ratio': financial_data['valuation']['pb_ratio'],
            'roe': financial_data['profitability']['roe'],
            'debt_to_equity': financial_data['financial_health']['debt_to_equity'],
            'revenue_growth': financial_data['growth']['revenue_growth_yoy']
        }
        
        # 标准化处理（0-1缩放）
        normalized_metrics = {}
        for key, value in metrics.items():
            if key == 'pe_ratio':
                # PE比率标准化（假设合理范围0-50）
                normalized_metrics[key] = min(max(value / 50.0, 0), 1)
            elif key == 'pb_ratio':
                # PB比率标准化（假设合理范围0-10）
                normalized_metrics[key] = min(max(value / 10.0, 0), 1)
            elif key == 'roe':
                # ROE标准化（假设合理范围0-50%）
                normalized_metrics[key] = min(max(value / 50.0, 0), 1)
            elif key == 'debt_to_equity':
                # 负债比率标准化（假设合理范围0-1）
                normalized_metrics[key] = min(max(value, 0), 1)
            elif key == 'revenue_growth':
                # 增长率标准化（假设合理范围-50%到100%）
                normalized_metrics[key] = min(max((value + 50) / 150.0, 0), 1)
        
        # 验证标准化结果
        for key, value in normalized_metrics.items():
            assert 0 <= value <= 1, f"{key}的标准化值{value}不在[0,1]范围内"
    
    @pytest.mark.integration
    def test_sentiment_aggregation(self):
        """测试情绪数据聚合"""
        news_data = MockNewsData.get_stock_news('000001')
        
        # 计算情绪指标
        sentiment_scores = [item['sentiment_score'] for item in news_data]
        
        # 简单平均
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        
        # 加权平均（按时间衰减）
        weights = []
        for item in news_data:
            # 解析时间
            pub_time = datetime.strptime(item['publish_time'], '%Y-%m-%d %H:%M:%S')
            now = datetime.now()
            hours_diff = (now - pub_time).total_seconds() / 3600
            
            # 时间衰减权重（24小时内权重为1，之后指数衰减）
            weight = np.exp(-hours_diff / 24) if hours_diff > 24 else 1.0
            weights.append(weight)
        
        weighted_sentiment = sum(s * w for s, w in zip(sentiment_scores, weights)) / sum(weights)
        
        # 验证聚合结果
        assert -1.0 <= avg_sentiment <= 1.0
        assert -1.0 <= weighted_sentiment <= 1.0
        
        # 计算其他指标
        positive_ratio = sum(1 for s in sentiment_scores if s > 0.1) / len(sentiment_scores)
        negative_ratio = sum(1 for s in sentiment_scores if s < -0.1) / len(sentiment_scores)
        neutral_ratio = 1 - positive_ratio - negative_ratio
        
        assert 0 <= positive_ratio <= 1
        assert 0 <= negative_ratio <= 1
        assert 0 <= neutral_ratio <= 1
        assert abs(positive_ratio + negative_ratio + neutral_ratio - 1.0) < 0.01
    
    @pytest.mark.integration
    def test_multi_source_data_fusion(self):
        """测试多源数据融合"""
        # 获取不同源的数据
        akshare_data = MockAkshareData.stock_zh_a_spot_em()
        eastmoney_data = MockEastmoneyAPI.get_stock_data('000001')
        financial_data = MockFinancialData.get_financial_metrics('000001')
        
        # 数据融合
        fused_data = {}
        
        # 从akshare获取基础市场数据
        if not akshare_data.empty:
            stock_row = akshare_data.iloc[0]
            fused_data.update({
                'current_price': stock_row['最新价'],
                'market_cap': stock_row['总市值'],
                'pe_ratio': stock_row['市盈率-动态'],
                'pb_ratio': stock_row['市净率'],
                'volume': stock_row['成交量']
            })
        
        # 从东方财富补充数据
        if eastmoney_data['rc'] == 0:
            em_data = eastmoney_data['data']
            # 价格数据融合（优先使用更准确的源）
            if 'f43' in em_data:
                fused_data['current_price_em'] = em_data['f43'] / 100.0
        
        # 从财务数据补充详细指标
        fused_data.update({
            'roe': financial_data['profitability']['roe'],
            'roa': financial_data['profitability']['roa'],
            'debt_ratio': financial_data['financial_health']['debt_to_equity'],
            'revenue_growth': financial_data['growth']['revenue_growth_yoy']
        })
        
        # 验证融合结果
        assert len(fused_data) > 0
        assert 'current_price' in fused_data
        assert 'market_cap' in fused_data
        assert 'roe' in fused_data
        
        # 验证数据一致性
        if 'current_price_em' in fused_data:
            price_diff = abs(fused_data['current_price'] - fused_data['current_price_em'])
            # 不同源的价格差异应该在合理范围内
            assert price_diff / fused_data['current_price'] < 0.1  # 10%以内


class TestDataQualityPipeline:
    """测试数据质量管道"""
    
    @pytest.mark.integration
    def test_data_completeness_check(self):
        """测试数据完整性检查"""
        # 完整数据
        complete_data = {
            'stock_code': '000001',
            'current_price': 12.5,
            'market_cap': 1000000000,
            'pe_ratio': 15.0,
            'pb_ratio': 1.8,
            'roe': 12.5
        }
        
        required_fields = ['stock_code', 'current_price', 'market_cap', 'pe_ratio']
        
        # 检查完整性
        missing_fields = [field for field in required_fields if field not in complete_data]
        completeness_score = 1.0 - len(missing_fields) / len(required_fields)
        
        assert completeness_score == 1.0
        assert len(missing_fields) == 0
        
        # 不完整数据
        incomplete_data = {
            'stock_code': '000001',
            'current_price': 12.5
            # 缺少其他字段
        }
        
        missing_fields = [field for field in required_fields if field not in incomplete_data]
        completeness_score = 1.0 - len(missing_fields) / len(required_fields)
        
        assert completeness_score < 1.0
        assert len(missing_fields) > 0
    
    @pytest.mark.integration
    def test_data_accuracy_validation(self):
        """测试数据准确性验证"""
        # 合理数据
        valid_data = {
            'pe_ratio': 15.0,      # 合理的PE比率
            'pb_ratio': 1.8,       # 合理的PB比率
            'roe': 12.5,           # 合理的ROE
            'current_ratio': 1.5,  # 合理的流动比率
            'debt_ratio': 0.4      # 合理的负债比率
        }
        
        # 验证规则
        validation_rules = {
            'pe_ratio': (0, 100),      # PE比率应该在0-100之间
            'pb_ratio': (0, 20),       # PB比率应该在0-20之间
            'roe': (-50, 100),         # ROE应该在-50%-100%之间
            'current_ratio': (0, 10),  # 流动比率应该在0-10之间
            'debt_ratio': (0, 1)       # 负债比率应该在0-1之间
        }
        
        accuracy_issues = []
        for field, (min_val, max_val) in validation_rules.items():
            if field in valid_data:
                value = valid_data[field]
                if not (min_val <= value <= max_val):
                    accuracy_issues.append(f"{field}值{value}超出合理范围[{min_val}, {max_val}]")
        
        assert len(accuracy_issues) == 0
        
        # 异常数据
        invalid_data = {
            'pe_ratio': -5.0,      # 负的PE比率
            'pb_ratio': 50.0,      # 过高的PB比率
            'roe': 200.0,          # 过高的ROE
            'current_ratio': -1.0, # 负的流动比率
            'debt_ratio': 2.0      # 过高的负债比率
        }
        
        accuracy_issues = []
        for field, (min_val, max_val) in validation_rules.items():
            if field in invalid_data:
                value = invalid_data[field]
                if not (min_val <= value <= max_val):
                    accuracy_issues.append(f"{field}值{value}超出合理范围[{min_val}, {max_val}]")
        
        assert len(accuracy_issues) > 0
    
    @pytest.mark.integration
    def test_data_timeliness_check(self):
        """测试数据时效性检查"""
        now = datetime.now()
        
        # 新鲜数据
        fresh_timestamp = now - timedelta(minutes=5)
        fresh_data = {
            'timestamp': fresh_timestamp.isoformat(),
            'data': {'price': 12.5}
        }
        
        # 检查时效性
        data_time = datetime.fromisoformat(fresh_data['timestamp'])
        age_minutes = (now - data_time).total_seconds() / 60
        is_fresh = age_minutes < 30  # 30分钟内为新鲜数据
        
        assert is_fresh
        assert age_minutes < 30
        
        # 过期数据
        stale_timestamp = now - timedelta(hours=2)
        stale_data = {
            'timestamp': stale_timestamp.isoformat(),
            'data': {'price': 12.5}
        }
        
        data_time = datetime.fromisoformat(stale_data['timestamp'])
        age_minutes = (now - data_time).total_seconds() / 60
        is_fresh = age_minutes < 30
        
        assert not is_fresh
        assert age_minutes > 30
    
    @pytest.mark.integration
    def test_data_consistency_check(self):
        """测试数据一致性检查"""
        # 一致的数据
        consistent_data = {
            'open': 12.0,
            'high': 12.8,
            'low': 11.5,
            'close': 12.5,
            'volume': 1000000,
            'market_cap': 1000000000,
            'shares_outstanding': 80000000  # 总股本
        }
        
        # 检查价格一致性
        price_consistency_issues = []
        
        # 最高价应该 >= max(开盘价, 收盘价)
        if consistent_data['high'] < max(consistent_data['open'], consistent_data['close']):
            price_consistency_issues.append("最高价低于开盘价或收盘价")
        
        # 最低价应该 <= min(开盘价, 收盘价)
        if consistent_data['low'] > min(consistent_data['open'], consistent_data['close']):
            price_consistency_issues.append("最低价高于开盘价或收盘价")
        
        # 检查市值一致性
        calculated_market_cap = consistent_data['close'] * consistent_data['shares_outstanding']
        market_cap_diff = abs(consistent_data['market_cap'] - calculated_market_cap)
        
        if market_cap_diff / consistent_data['market_cap'] > 0.1:  # 10%误差
            price_consistency_issues.append("市值与股价*股本不一致")
        
        assert len(price_consistency_issues) == 0
        
        # 不一致的数据
        inconsistent_data = {
            'open': 12.0,
            'high': 11.0,    # 最高价低于开盘价
            'low': 13.0,     # 最低价高于开盘价
            'close': 12.5,
            'volume': 1000000
        }
        
        price_consistency_issues = []
        
        if inconsistent_data['high'] < max(inconsistent_data['open'], inconsistent_data['close']):
            price_consistency_issues.append("最高价低于开盘价或收盘价")
        
        if inconsistent_data['low'] > min(inconsistent_data['open'], inconsistent_data['close']):
            price_consistency_issues.append("最低价高于开盘价或收盘价")
        
        assert len(price_consistency_issues) > 0