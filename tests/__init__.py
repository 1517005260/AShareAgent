"""
A股Agent测试框架

该测试框架遵循软件工程最佳实践，确保系统的可靠性和数据质量。

测试目录结构：
- unit/: 单元测试 - 测试各个组件的独立功能
- integration/: 集成测试 - 测试组件间的协作
- data_validation/: 数据验证测试 - 确保数据源可靠性
- performance/: 性能测试 - 监控系统性能指标
- mocks/: 模拟对象 - 隔离外部依赖
- fixtures/: 测试数据 - 标准化测试输入
- reports/: 测试报告 - 自动生成的测试结果

注意：这不是金融回测，而是软件质量保证。
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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