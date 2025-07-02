# A股投资Agent回测系统测试框架

本测试框架为AShare Agent回测系统提供全面的质量保证，包括**细粒度Agent频率控制**和**VaR等金融指标计算**的完整测试覆盖。

## 🎯 新增核心测试功能

### 1. 细粒度Agent策略控制测试
- **Agent执行频率控制**: daily, weekly, monthly, conditional
- **条件触发机制**: 基于市场波动率和价格变化的智能触发
- **缓存优化**: 测试缓存机制的有效性和性能
- **执行统计**: Agent执行次数和优化率统计

### 2. VaR等金融指标计算测试
- **VaR (Value at Risk)**: 95%、99%等不同置信水平
- **Expected Shortfall (ES)**: 条件VaR计算
- **Beta & Alpha**: 市场敏感性和超额收益测试
- **夏普比率**: 风险调整后收益测试
- **最大回撤**: 风险控制指标测试
- **信息比率**: 主动管理能力测试

### 3. 回测系统集成测试
- **完整流程测试**: 端到端回测验证
- **多场景测试**: 牛市、熊市、震荡市场
- **压力测试**: 大数据量和高频交易测试
- **性能监控**: 执行时间、内存使用、CPU占用

注意：本项目使用 Poetry 管理依赖，所有测试命令都需要使用 `poetry run` 前缀执行。

## 测试目标

- **软件质量保证**: 确保代码功能正确性
- **数据质量验证**: 验证外部数据源的可靠性
- **系统性能监控**: 监控系统响应时间和资源使用
- **集成流程测试**: 验证完整的投资决策流程

## 目录结构

```
tests/
├── __init__.py                 # 测试框架说明
├── conftest.py                # pytest全局配置和fixtures
├── fixtures/                  # 测试数据和状态
│   ├── sample_data.json       # 样本数据
│   └── test_portfolio_states.py # 投资组合测试状态
├── mocks/                     # 模拟对象
│   └── __init__.py           # 外部依赖模拟
├── unit/                      # 单元测试
│   ├── test_base_agent.py     # 基础Agent测试
│   ├── test_portfolio_manager.py # 投资组合管理测试
│   ├── test_market_data_agent.py # 市场数据测试
│   ├── test_debate_room.py    # 辩论室测试
│   └── test_researcher_agents.py # 研究员测试
├── integration/               # 集成测试
│   └── test_workflow.py       # 完整工作流程测试
├── data_validation/           # 数据验证测试
│   ├── test_data_sources.py   # 数据源可靠性测试
│   └── test_api_reliability.py # API可靠性测试
├── performance/               # 性能测试
│   └── test_system_performance.py # 系统性能测试
└── reports/                   # 测试报告输出
```

## 快速开始

### 1. 安装测试依赖

使用 Poetry 安装，依赖已在 pyproject.toml 中定义：

```bash
poetry install
```

### 2. 检查测试环境

```bash
poetry run python scripts/run_tests.py --check-env
```

### 3. 运行测试

```bash
# 运行所有测试
poetry run python scripts/run_tests.py --all

# 运行特定类型的测试
poetry run python scripts/run_tests.py --unit           # 单元测试
poetry run python scripts/run_tests.py --integration    # 集成测试
poetry run python scripts/run_tests.py --fast          # 快速测试（排除慢速）

# 运行特定测试文件
poetry run python scripts/run_tests.py --test tests/unit/test_base_agent.py

# 带覆盖率报告
poetry run python scripts/run_tests.py --coverage

# 或直接使用 pytest（需要 poetry run 前缀）
poetry run pytest tests/unit/ -v
```

## 测试类型说明

### 单元测试 (Unit Tests)
- **目的**: 测试单个组件的功能
- **范围**: BaseAgent、投资组合管理、市场数据等
- **特点**: 快速执行，隔离外部依赖
- **运行**: `poetry run pytest tests/unit/ -m unit`

### 集成测试 (Integration Tests)
- **目的**: 测试组件间的协作
- **范围**: 完整的分析流程、多Agent协作
- **特点**: 模拟真实场景，验证数据流
- **运行**: `poetry run pytest tests/integration/ -m integration`

### 数据验证测试 (Data Validation Tests)
- **目的**: 确保数据源质量和API可靠性
- **范围**: akshare、东方财富、新闻数据等
- **特点**: 验证数据完整性和一致性
- **运行**: `poetry run pytest tests/data_validation/ -m data_validation`

### 性能测试 (Performance Tests)
- **目的**: 监控系统性能指标
- **范围**: 响应时间、内存使用、并发处理
- **特点**: 设置性能基准，检测性能回归
- **运行**: `poetry run pytest tests/performance/ -m performance`

## 测试标记 (Markers)

使用pytest标记来分类和过滤测试：

```bash
# 按标记运行测试
poetry run pytest -m unit                 # 只运行单元测试
poetry run pytest -m "unit or integration" # 运行单元和集成测试
poetry run pytest -m "not slow"           # 排除慢速测试
poetry run pytest -m data_validation      # 只运行数据验证测试
```

可用标记：
- `unit`: 单元测试
- `integration`: 集成测试
- `data_validation`: 数据验证测试
- `performance`: 性能测试
- `slow`: 慢速测试（如真实API调用）
- `skip_ci`: 在CI环境中跳过

## 模拟对象 (Mocks)

测试框架提供完整的模拟对象系统：

### 可用的模拟类
- `MockLLMResponse`: 模拟LLM响应
- `MockAkshareData`: 模拟akshare数据
- `MockEastmoneyAPI`: 模拟东方财富API
- `MockNewsData`: 模拟新闻数据
- `MockFinancialData`: 模拟财务数据

### 示例用法

```python
from tests.mocks import MockAkshareData, create_mock_agent_state

def test_market_data():
    # 使用模拟数据
    mock_data = MockAkshareData.stock_zh_a_spot_em()
    
    # 创建模拟状态
    state = create_mock_agent_state("000001", 100000.0)
    
    # 测试逻辑...
```

## 测试fixtures

提供丰富的测试fixtures：

- `mock_agent_state`: 模拟Agent状态
- `sample_financial_data`: 样本财务数据
- `sample_price_data`: 样本价格数据
- `mock_external_apis`: 模拟外部API
- `data_quality_validator`: 数据质量验证器
- `performance_monitor`: 性能监控器

## 配置文件

### pytest.ini
主要配置选项：
- 测试发现路径
- 标记定义
- 输出格式
- 超时设置

### conftest.py
全局配置包括：
- fixture定义
- 测试hooks
- 自动标记逻辑
- 环境检查

## 测试报告

测试报告自动生成在 `tests/reports/` 目录：

```bash
# 生成HTML覆盖率报告
poetry run pytest --cov=src --cov-report=html

# 查看报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 调试测试

### 运行单个测试
```bash
poetry run pytest tests/unit/test_base_agent.py::TestBaseAgent::test_init -v
```

### 调试模式
```bash
poetry run pytest tests/unit/test_base_agent.py -v -s --pdb
```

### 显示print输出
```bash
poetry run pytest tests/unit/test_base_agent.py -v -s
```

## 编写新测试

### 1. 选择测试类型
- 新功能 → 单元测试
- 多组件交互 → 集成测试
- 数据源变更 → 数据验证测试
- 性能优化 → 性能测试

### 2. 使用合适的fixtures
```python
def test_new_feature(mock_agent_state, mock_external_apis):
    # 测试代码
    pass
```

### 3. 添加适当的标记
```python
@pytest.mark.unit
def test_unit_feature():
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_integration_feature():
    pass
```

### 4. 模拟外部依赖
```python
@patch('src.agents.some_agent.get_chat_completion')
def test_with_mock_llm(mock_llm):
    mock_llm.return_value = '{"result": "success"}'
    # 测试代码
```

## 注意事项

1. **不要依赖真实API**: 测试应该能离线运行
2. **保持测试独立**: 测试间不应有依赖关系
3. **使用描述性名称**: 测试名称应该说明被测试的功能
4. **验证边界条件**: 测试正常和异常情况
5. **控制测试时间**: 避免长时间运行的测试

## 最佳实践

1. **测试驱动开发**: 先写测试，再写实现
2. **定期运行测试**: 每次提交前运行相关测试
3. **维护测试数据**: 保持测试数据的真实性和完整性
4. **监控覆盖率**: 目标覆盖率 > 80%
5. **重构测试**: 定期清理和优化测试代码

## 相关文档

- [pytest官方文档](https://docs.pytest.org/)
- [unittest.mock文档](https://docs.python.org/3/library/unittest.mock.html)
- [项目架构说明](../README.md)

## 问题排查

### 常见问题

1. **导入错误**: 确保Python路径正确设置
2. **Mock失败**: 检查mock路径是否正确
3. **测试超时**: 调整timeout设置或优化测试逻辑
4. **依赖缺失**: 运行 `--install-deps` 安装依赖

### 获取帮助

```bash
# 查看可用命令
poetry run python scripts/run_tests.py --help

# 检查环境配置
poetry run python scripts/run_tests.py --check-env

# 查看pytest帮助
poetry run pytest --help
```