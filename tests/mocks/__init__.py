"""
模拟对象模块

提供测试用的模拟对象和数据，隔离外部依赖
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock


class MockLLMResponse:
    """模拟LLM响应"""
    
    def __init__(self, signal="neutral", confidence=0.5, reasoning="默认推理"):
        self.signal = signal
        self.confidence = confidence
        self.reasoning = reasoning
    
    def to_json(self):
        return json.dumps({
            "signal": self.signal,
            "confidence": self.confidence,
            "reasoning": self.reasoning
        }, ensure_ascii=False)


class MockAkshareData:
    """模拟akshare数据"""
    
    @staticmethod
    def stock_zh_a_spot_em():
        """模拟股票实时数据"""
        return pd.DataFrame({
            '代码': ['000001', '000002', '600519'],
            '名称': ['平安银行', '万科A', '贵州茅台'],
            '最新价': [12.50, 18.30, 1680.00],
            '涨跌幅': [2.45, -1.20, 0.80],
            '总市值': [241728000000, 201564000000, 2107200000000],
            '市盈率-动态': [5.23, 7.89, 28.50],
            '市净率': [0.67, 0.98, 9.80],
            '成交量': [42156789, 15234567, 8765432]
        })
    
    @staticmethod
    def stock_zh_a_hist(symbol, period="daily", start_date=None, end_date=None):
        """模拟历史价格数据"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=100)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        base_price = 12.50 if symbol == '000001' else 18.30
        
        return pd.DataFrame({
            '日期': dates,
            '开盘': base_price + (dates - dates[0]).days * 0.01,
            '收盘': base_price + (dates - dates[0]).days * 0.01 + 0.1,
            '最高': base_price + (dates - dates[0]).days * 0.01 + 0.2,
            '最低': base_price + (dates - dates[0]).days * 0.01 - 0.1,
            '成交量': [1000000 + i * 10000 for i in range(len(dates))],
            '成交额': [base_price * 1000000 * (1 + i * 0.001) for i in range(len(dates))],
            '振幅': [2.5] * len(dates),
            '涨跌幅': [0.8] * len(dates),
            '涨跌额': [0.1] * len(dates),
            '换手率': [1.2] * len(dates)
        })


class MockEastmoneyAPI:
    """模拟东方财富API"""
    
    @staticmethod
    def get_stock_data(stock_code):
        """模拟获取股票数据"""
        return {
            'rc': 0,
            'rt': 1,
            'data': {
                'f43': 1250,    # 价格*100
                'f44': 25,      # 涨跌额*100
                'f45': 2.04,    # 涨跌幅
                'f46': 120000,  # 成交量(手)
                'f47': 150000000, # 成交额
                'f116': 241728000000, # 总市值
                'f117': 180000000000, # 流通市值  
                'f114': 5.23,   # 市盈率
                'f115': 5.23,   # 市盈率(动态)
                'f167': 0.67,   # 市净率
                'f168': 1.8,    # 市销率
                'f169': 15.2    # 股息率
            }
        }


class MockNewsData:
    """模拟新闻数据"""
    
    @staticmethod
    def get_stock_news(stock_code, count=10):
        """模拟股票新闻"""
        return [
            {
                'title': f'{stock_code}公司发布三季度财报，业绩超预期',
                'content': '公司营收同比增长15%，净利润增长20%，超出市场预期',
                'publish_time': '2024-01-15 09:30:00',
                'source': '财经网',
                'sentiment_score': 0.8
            },
            {
                'title': f'{stock_code}获得大额订单，业务前景看好',
                'content': '公司与多家知名企业签署战略合作协议，未来增长可期',
                'publish_time': '2024-01-14 14:20:00',
                'source': '证券时报',
                'sentiment_score': 0.7
            },
            {
                'title': f'行业监管政策调整，{stock_code}面临挑战',
                'content': '新的行业政策对公司业务模式提出了更高要求',
                'publish_time': '2024-01-13 16:45:00',
                'source': '财新网',
                'sentiment_score': -0.3
            }
        ]


class MockFinancialData:
    """模拟财务数据"""
    
    @staticmethod
    def get_financial_metrics(stock_code):
        """模拟财务指标"""
        return {
            'basic_info': {
                'stock_code': stock_code,
                'stock_name': '测试股票',
                'industry': '金融业',
                'market_cap': 241728000000,
                'total_shares': 19356000000
            },
            'profitability': {
                'roe': 12.5,          # 净资产收益率
                'roa': 0.8,           # 总资产收益率
                'gross_margin': 45.2,  # 毛利率
                'net_margin': 28.6,    # 净利率
                'operating_margin': 35.8 # 营业利润率
            },
            'growth': {
                'revenue_growth_yoy': 15.2,     # 营收同比增长
                'profit_growth_yoy': 18.7,      # 净利润同比增长
                'revenue_growth_3y_avg': 12.8,  # 三年平均营收增长
                'profit_growth_3y_avg': 16.3    # 三年平均利润增长
            },
            'financial_health': {
                'current_ratio': 1.45,      # 流动比率
                'quick_ratio': 1.12,        # 速动比率
                'debt_to_equity': 0.38,     # 资产负债率
                'interest_coverage': 8.5    # 利息保障倍数
            },
            'valuation': {
                'pe_ratio': 12.5,      # 市盈率
                'pb_ratio': 1.8,       # 市净率
                'ps_ratio': 2.2,       # 市销率
                'peg_ratio': 0.8,      # PEG比率
                'ev_ebitda': 8.5       # EV/EBITDA
            }
        }


def create_mock_agent_state(stock_symbol="000001", portfolio_cash=100000.0):
    """创建模拟的Agent状态"""
    return {
        "messages": [],
        "data": {
            "stock_symbol": stock_symbol,
            "portfolio": {
                "cash": portfolio_cash,
                "stock": 0,
                "total_value": portfolio_cash
            },
            "market_data": MockFinancialData.get_financial_metrics(stock_symbol),
            "price_data": MockAkshareData.stock_zh_a_hist(stock_symbol),
            "news_data": MockNewsData.get_stock_news(stock_symbol)
        },
        "metadata": {
            "show_reasoning": False,
            "current_agent_name": "test_agent",
            "analysis_timestamp": datetime.now().isoformat(),
            "market_session": "regular"
        }
    }


def create_mock_llm_client():
    """创建模拟的LLM客户端"""
    mock_client = MagicMock()
    
    def mock_chat_completion(messages, *args, **kwargs):
        """模拟聊天完成响应"""
        # 根据消息内容返回不同的响应
        if any("技术分析" in str(msg) for msg in messages):
            return MockLLMResponse("bullish", 0.75, "技术指标显示上涨趋势").to_json()
        elif any("基本面" in str(msg) for msg in messages):
            return MockLLMResponse("bullish", 0.7, "基本面数据良好").to_json()
        elif any("情绪分析" in str(msg) for msg in messages):
            return MockLLMResponse("neutral", 0.6, "市场情绪中性").to_json()
        else:
            return MockLLMResponse().to_json()
    
    mock_client.chat_completion = mock_chat_completion
    return mock_client