"""
pytest配置文件 - 全局测试配置和fixture

提供测试运行的通用配置、fixture和工具函数
"""

import pytest
import os
import sys
import json
import tempfile
import logging
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.mocks import (
    MockLLMResponse, MockAkshareData, MockEastmoneyAPI, 
    MockNewsData, MockFinancialData, create_mock_agent_state,
    create_mock_llm_client
)

# 测试配置
TEST_CONFIG = {
    'LOG_LEVEL': logging.WARNING,  # 测试时降低日志级别
    'TIMEOUT': 30,                 # 默认测试超时时间（秒）
    'RETRY_ATTEMPTS': 3,           # API调用重试次数
    'DATA_VALIDATION_STRICT': True,# 严格数据验证模式
}

# 测试数据路径
TEST_DATA_DIR = project_root / 'tests' / 'fixtures'
TEST_REPORTS_DIR = project_root / 'tests' / 'reports'

# 确保报告目录存在
TEST_REPORTS_DIR.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def test_config():
    """测试配置fixture"""
    return TEST_CONFIG


@pytest.fixture(scope="session")  
def setup_test_logging():
    """设置测试日志"""
    logging.basicConfig(
        level=TEST_CONFIG['LOG_LEVEL'],
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('test')


@pytest.fixture
def mock_agent_state():
    """模拟AgentState"""
    return create_mock_agent_state()


@pytest.fixture
def sample_financial_data():
    """样本财务数据"""
    return MockFinancialData.get_financial_metrics("000001")


@pytest.fixture
def sample_price_data():
    """样本价格数据"""
    return MockAkshareData.stock_zh_a_hist("000001")


@pytest.fixture
def mock_api_responses():
    """模拟API响应"""
    return {
        'akshare_success': MockAkshareData.stock_zh_a_spot_em(),
        'eastmoney_success': MockEastmoneyAPI.get_stock_data("000001"),
        'news_success': MockNewsData.get_stock_news("000001"),
        'llm_success': MockLLMResponse("bullish", 0.75, "Strong fundamental indicators").to_json(),
        'api_error': Exception("API connection failed")
    }


@pytest.fixture
def temp_test_db():
    """临时测试数据库"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    yield db_path
    
    # 清理
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_external_apis():
    """模拟外部API调用"""
    with patch('akshare.stock_zh_a_spot_em') as mock_ak, \
         patch('requests.get') as mock_requests, \
         patch('src.tools.openrouter_config.get_chat_completion') as mock_llm:
        
        # 设置默认返回值
        mock_ak.return_value = MockAkshareData.stock_zh_a_spot_em()
        
        mock_response = Mock()
        mock_response.json.return_value = MockEastmoneyAPI.get_stock_data("000001")
        mock_response.status_code = 200
        mock_requests.return_value = mock_response
        
        mock_llm.return_value = MockLLMResponse().to_json()
        
        yield {
            'akshare': mock_ak,
            'eastmoney': mock_requests,
            'llm': mock_llm
        }


@pytest.fixture
def data_quality_validator():
    """数据质量验证器"""
    def validate_data(data, data_type):
        """验证数据质量"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'quality_score': 1.0
        }
        
        if data_type == 'financial_metrics':
            if isinstance(data, dict):
                # 验证财务指标字典
                required_sections = ['basic_info', 'profitability', 'valuation']
                for section in required_sections:
                    if section not in data:
                        validation_result['errors'].append(f"Missing section: {section}")
                        validation_result['is_valid'] = False
            elif isinstance(data, list) and data:
                # 验证财务指标列表
                required_fields = ['pe_ratio', 'market_cap']
                for field in required_fields:
                    if field not in data[0]:
                        validation_result['errors'].append(f"Missing {field}")
                        validation_result['is_valid'] = False
            else:
                validation_result['errors'].append("Invalid financial data format")
                validation_result['is_valid'] = False
        
        elif data_type == 'price_data':
            if data is None or (hasattr(data, 'empty') and data.empty):
                validation_result['errors'].append("Empty price data")
                validation_result['is_valid'] = False
            elif hasattr(data, 'columns'):
                required_columns = ['开盘', '最高', '最低', '收盘', '成交量']
                missing_cols = [col for col in required_columns if col not in data.columns]
                if missing_cols:
                    validation_result['errors'].append(f"Missing columns: {missing_cols}")
                    validation_result['is_valid'] = False
        
        validation_result['quality_score'] = 1.0 if validation_result['is_valid'] else 0.0
        return validation_result
    
    return validate_data


@pytest.fixture
def performance_monitor():
    """性能监控器"""
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.metrics = {}
        
        def start(self):
            self.start_time = datetime.now()
        
        def stop(self, operation_name):
            if self.start_time:
                duration = (datetime.now() - self.start_time).total_seconds()
                self.metrics[operation_name] = duration
                return duration
            return None
        
        def get_metrics(self):
            return self.metrics.copy()
        
        def reset(self):
            self.start_time = None
            self.metrics = {}
    
    return PerformanceMonitor()


@pytest.fixture
def mock_llm_client():
    """模拟LLM客户端"""
    return create_mock_llm_client()


# pytest插件配置
def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "data_validation: 数据验证测试")
    config.addinivalue_line("markers", "performance: 性能测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "skip_ci: 跳过CI测试")


def pytest_collection_modifyitems(config, items):
    """自动标记测试"""
    for item in items:
        # 根据路径自动标记
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "data_validation" in str(item.fspath):
            item.add_marker(pytest.mark.data_validation)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        
        # 标记慢速测试
        if "slow" in item.name.lower() or any("slow" in marker.name for marker in item.iter_markers()):
            item.add_marker(pytest.mark.slow)


def pytest_runtest_setup(item):
    """测试运行前的设置"""
    # 跳过需要真实API的测试（在CI环境中）
    if "skip_ci" in [marker.name for marker in item.iter_markers()]:
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
            pytest.skip("跳过CI环境中的测试")


def pytest_sessionstart(session):
    """测试会话开始时的设置"""
    print(f"\n开始测试会话 - 项目根目录: {project_root}")
    print(f"测试数据目录: {TEST_DATA_DIR}")
    print(f"测试报告目录: {TEST_REPORTS_DIR}")


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时的清理"""
    print(f"\n测试会话结束 - 退出状态: {exitstatus}")
    
    # 生成测试报告摘要
    if hasattr(session, 'testscollected'):
        print(f"共收集到 {session.testscollected} 个测试")


# 测试用的实用函数
def load_test_data(filename):
    """加载测试数据文件"""
    file_path = TEST_DATA_DIR / filename
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            if filename.endswith('.json'):
                return json.load(f)
            else:
                return f.read()
    else:
        raise FileNotFoundError(f"测试数据文件不存在: {file_path}")


def create_test_report(test_name, results):
    """创建测试报告"""
    report_file = TEST_REPORTS_DIR / f"{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return report_file