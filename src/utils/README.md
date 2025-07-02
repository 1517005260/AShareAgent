# 智能投资系统 - 核心工具模块

## 概述

核心工具模块提供了智能投资系统的基础设施和共享功能，包括配置管理、LLM客户端、日志系统、序列化工具、异常处理等核心组件。这些工具模块为整个系统的各个组件提供统一的服务和接口。

## 系统架构

```
src/utils/
├── __init__.py                    # 模块初始化
├── config_manager.py              # 统一配置管理
├── llm_clients.py                 # LLM客户端封装
├── logging_config.py              # 日志配置系统
├── serialization.py               # 对象序列化工具
├── exceptions.py                  # 自定义异常类
├── api_utils.py                   # API工具和装饰器
├── llm_interaction_logger.py      # LLM交互日志记录
├── output_logger.py               # 输出重定向日志
├── structured_terminal.py         # 结构化终端输出
└── README.md                      # 说明文档
```

## 核心工具详述

### 1. 配置管理 (config_manager.py)

统一的配置管理系统，支持多种配置类型和环境变量自动加载。

#### 主要配置类

- **LLMConfig**: LLM相关配置
- **SystemConfig**: 系统级配置
- **AgentConfig**: Agent行为配置
- **MarketDataConfig**: 市场数据配置

#### 使用方法

```python
from src.utils.config_manager import get_config, get_llm_config

# 获取全局配置实例
config = get_config()

# 访问不同配置
llm_config = config.llm
system_config = config.system
agent_config = config.agent
market_data_config = config.market_data

# 便捷函数
llm_config = get_llm_config()
```

#### 环境变量配置

```bash
# LLM配置
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash

# OpenAI兼容API配置
OPENAI_COMPATIBLE_API_KEY=your-api-key
OPENAI_COMPATIBLE_BASE_URL=https://api.example.com/v1
OPENAI_COMPATIBLE_MODEL=claude-3-haiku

# 系统配置
LOG_LEVEL=INFO
MAX_OUTPUT_SIZE=10000
CACHE_ENABLED=true
CACHE_TTL=3600

# Agent配置
DEFAULT_CONFIDENCE_THRESHOLD=0.5
MAX_NEWS_COUNT=100
SENTIMENT_ANALYSIS_DAYS=7
RISK_SCORE_THRESHOLD=8
```

#### 配置验证

```python
config = get_config()
if config.validate_configuration():
    print("配置验证通过")
else:
    print("配置验证失败")

# 生成环境变量模板
config.save_env_template(".env.example")
```

### 2. LLM客户端 (llm_clients.py)

统一的LLM客户端封装，支持多种LLM提供商和自动重试机制。

#### 支持的客户端

- **GeminiClient**: Google Gemini API客户端
- **OpenAICompatibleClient**: OpenAI兼容API客户端

#### 使用方法

```python
from src.utils.llm_clients import get_chat_completion, LLMClientFactory

# 简单调用（自动选择客户端）
messages = [
    {"role": "system", "content": "你是一个专业的金融分析师"},
    {"role": "user", "content": "分析一下这只股票的投资价值"}
]

response = get_chat_completion(
    messages=messages,
    max_retries=3,
    client_type="auto"  # 自动选择可用的客户端
)

# 指定客户端类型
gemini_response = get_chat_completion(
    messages=messages,
    client_type="gemini"
)

openai_response = get_chat_completion(
    messages=messages,
    client_type="openai_compatible"
)
```

#### 工厂模式创建客户端

```python
from src.utils.llm_clients import LLMClientFactory

# 创建Gemini客户端
gemini_client = LLMClientFactory.create_client(
    client_type="gemini",
    api_key="your-api-key",
    model="gemini-1.5-flash"
)

# 创建OpenAI兼容客户端
openai_client = LLMClientFactory.create_client(
    client_type="openai_compatible",
    api_key="your-api-key",
    base_url="https://api.example.com/v1",
    model="claude-3-haiku"
)

# 直接调用
response = gemini_client.get_completion(messages)
```

#### 重试机制和错误处理

```python
# 带重试的LLM调用
response = get_chat_completion(
    messages=messages,
    max_retries=5,           # 最大重试次数
    initial_retry_delay=1,   # 初始重试延迟
    client_type="auto"
)

# 错误处理
if response is None:
    print("LLM调用失败，已达到最大重试次数")
else:
    print(f"成功获取响应: {response}")
```

### 3. 日志配置 (logging_config.py)

统一的日志配置系统，支持控制台和文件双重输出。

#### 使用方法

```python
from src.utils.logging_config import setup_logger, SUCCESS_ICON, ERROR_ICON, WAIT_ICON

# 创建logger
logger = setup_logger('my_module')

# 使用预定义图标
logger.info(f"{SUCCESS_ICON} 操作成功完成")
logger.error(f"{ERROR_ICON} 操作执行失败")
logger.info(f"{WAIT_ICON} 正在处理请求...")
```

#### 日志级别配置

- **控制台**: INFO级别及以上
- **文件**: DEBUG级别及以上
- **文件位置**: `logs/{module_name}.log`

#### 自定义日志目录

```python
# 指定日志目录
logger = setup_logger('my_module', log_dir='/custom/log/dir')
```

### 4. 序列化工具 (serialization.py)

提供复杂Python对象到JSON可序列化格式的转换。

#### 使用方法

```python
from src.utils.serialization import serialize_agent_state

# 序列化Agent状态
state = {
    "data": {"ticker": "600519"},
    "timestamp": datetime.now(),
    "pandas_data": some_dataframe,
    "custom_object": some_custom_object
}

serialized = serialize_agent_state(state)
print(json.dumps(serialized, indent=2))
```

#### 支持的对象类型

- **基础类型**: int, float, bool, str, None
- **容器类型**: list, tuple, dict
- **日期时间**: datetime对象 → ISO格式字符串
- **Pandas对象**: DataFrame, Series → dict格式
- **自定义对象**: 具有`__dict__`属性的对象
- **LangChain消息**: 具有content和type属性的对象

#### 错误恢复

```python
# 如果序列化失败，会返回错误信息
result = serialize_agent_state(problematic_state)
if result.get("serialization_error"):
    print(f"序列化失败: {result['error']}")
```

### 5. 异常处理 (exceptions.py)

定义了系统专用的异常类和错误恢复策略。

#### 异常类层次

```python
AShareAgentException                 # 基础异常类
├── DataValidationError             # 数据验证错误
├── LLMConnectionError              # LLM连接错误
├── MarketDataError                 # 市场数据错误
├── AgentExecutionError             # Agent执行错误
├── ConfigurationError              # 配置错误
└── PortfolioError                  # 投资组合错误
```

#### 使用方法

```python
from src.utils.exceptions import MarketDataError, ErrorRecoveryStrategy

try:
    # 市场数据获取逻辑
    data = get_market_data(ticker)
except MarketDataError as e:
    print(f"市场数据错误: {e}")
    print(f"股票代码: {e.ticker}")
    print(f"数据类型: {e.data_type}")
    
    # 使用错误恢复策略
    fallback_data = ErrorRecoveryStrategy.get_safe_price_data()
```

#### 错误恢复策略

```python
# 获取默认分析结果
default_result = ErrorRecoveryStrategy.get_default_analysis_result(
    agent_name="technical_agent",
    error_msg="数据获取失败"
)

# 获取安全的财务指标
safe_metrics = ErrorRecoveryStrategy.get_safe_financial_metrics()

# 获取安全的价格数据
safe_prices = ErrorRecoveryStrategy.get_safe_price_data()
```

### 6. API工具 (api_utils.py)

提供Agent API装饰器和LLM交互日志功能。

#### Agent端点装饰器

```python
from src.utils.api_utils import agent_endpoint

@agent_endpoint("sentiment", "情感分析代理")
def sentiment_agent(state):
    # Agent执行逻辑
    result = analyze_sentiment(state)
    return result
```

#### LLM交互日志装饰器

```python
from src.utils.api_utils import log_llm_interaction

# 装饰器模式
@log_llm_interaction(state)
def my_llm_function(messages, **kwargs):
    return get_chat_completion(messages, **kwargs)

# 直接调用模式
logger = log_llm_interaction("agent_name")
response = some_llm_call()
logger(request_data, response)
```

#### API服务器启动

```python
from src.utils.api_utils import start_api_server
import threading

# 在独立线程中启动API服务器
stop_event = threading.Event()
server_thread = threading.Thread(
    target=start_api_server,
    args=("0.0.0.0", 8000, stop_event),
    daemon=True
)
server_thread.start()

# 停止服务器
stop_event.set()
```

### 7. LLM交互日志记录 (llm_interaction_logger.py)

基于Context Variables的LLM交互日志系统。

#### 上下文变量

```python
from src.utils.llm_interaction_logger import (
    log_storage_context,
    current_agent_name_context,
    current_run_id_context
)

# 设置上下文
log_storage_context.set(storage_instance)
current_agent_name_context.set("fundamentals_agent")
current_run_id_context.set("run_123")
```

#### Agent执行装饰器

```python
from src.utils.llm_interaction_logger import log_agent_execution

@log_agent_execution("fundamentals_agent")
def fundamentals_agent(state):
    # Agent逻辑
    result = analyze_fundamentals(state)
    return result
```

#### LLM调用包装

```python
from src.utils.llm_interaction_logger import wrap_llm_call
from src.utils.llm_clients import get_chat_completion

# 包装LLM调用函数
wrapped_llm_call = wrap_llm_call(get_chat_completion)

# 使用包装后的函数（会自动记录日志）
response = wrapped_llm_call(messages)
```

#### 输出捕获

```python
from src.utils.llm_interaction_logger import OutputCapture

with OutputCapture() as capture:
    print("这会被捕获")
    logger.info("这也会被捕获")

print(f"捕获的输出: {capture.outputs}")
```

### 8. 输出日志 (output_logger.py)

重定向stdout到文件和控制台的工具。

#### 使用方法

```python
from src.utils.output_logger import OutputLogger
import sys

# 重定向stdout
output_logger = OutputLogger("custom_output.txt")
sys.stdout = output_logger

print("这会同时显示在控制台和文件中")

# 恢复原始stdout
sys.stdout = output_logger.terminal
```

#### 自动时间戳文件名

```python
# 不指定文件名，会自动生成带时间戳的文件名
output_logger = OutputLogger()  # logs/output_20240131_143052.txt
```

### 9. 结构化终端输出 (structured_terminal.py)

美观的终端输出格式化工具。

#### 使用方法

```python
from src.utils.structured_terminal import (
    StructuredTerminalOutput,
    print_structured_output,
    terminal
)

# 使用全局终端实例
terminal.set_metadata("ticker", "600519")
terminal.set_metadata("start_date", "2024-01-01")
terminal.set_metadata("end_date", "2024-01-31")

# 添加Agent数据
terminal.add_agent_data("fundamentals_agent", {
    "signal": "bullish",
    "confidence": 0.8,
    "reasoning": "基本面分析显示公司财务状况良好"
})

# 打印格式化输出
terminal.print_output()
```

#### 从工作流状态生成输出

```python
# 直接从最终状态生成结构化输出
final_state = {
    "data": {"ticker": "600519"},
    "metadata": {"all_agent_reasoning": {...}}
}

print_structured_output(final_state)
```

#### 自定义Agent映射

```python
# 在structured_terminal.py中添加新Agent
AGENT_MAP["new_agent"] = {
    "icon": "🔧", 
    "name": "新分析工具"
}

AGENT_ORDER.append("new_agent")
```

## 集成使用示例

### 完整的Agent开发示例

```python
# 导入必要的工具
from src.utils.config_manager import get_config
from src.utils.llm_clients import get_chat_completion
from src.utils.logging_config import setup_logger, SUCCESS_ICON, ERROR_ICON
from src.utils.api_utils import agent_endpoint, log_llm_interaction
from src.utils.exceptions import AgentExecutionError, ErrorRecoveryStrategy
from src.utils.serialization import serialize_agent_state

# 设置日志
logger = setup_logger('custom_agent')

@agent_endpoint("custom_agent", "自定义分析代理")
def custom_agent(state):
    """自定义分析代理示例"""
    try:
        # 获取配置
        config = get_config()
        
        # 数据验证
        ticker = state["data"].get("ticker")
        if not ticker:
            raise AgentExecutionError("缺少股票代码", "custom_agent")
        
        logger.info(f"{SUCCESS_ICON} 开始分析股票: {ticker}")
        
        # 构造LLM请求
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的金融分析师"
            },
            {
                "role": "user", 
                "content": f"请分析股票 {ticker} 的投资价值"
            }
        ]
        
        # 调用LLM（带日志记录）
        llm_logger = log_llm_interaction("custom_agent")
        response = get_chat_completion(
            messages=messages,
            max_retries=config.llm.max_retries,
            client_type="auto"
        )
        llm_logger(messages, response)
        
        if not response:
            raise AgentExecutionError("LLM调用失败", "custom_agent")
        
        # 处理结果
        analysis_result = {
            "signal": "neutral",
            "confidence": 0.6,
            "reasoning": response,
            "ticker": ticker
        }
        
        logger.info(f"{SUCCESS_ICON} 分析完成")
        
        # 更新状态
        new_state = {
            "messages": state["messages"] + [
                {"role": "assistant", "content": response, "name": "custom_agent"}
            ],
            "data": {**state["data"], "custom_analysis": analysis_result},
            "metadata": state["metadata"]
        }
        
        return new_state
        
    except Exception as e:
        logger.error(f"{ERROR_ICON} 分析失败: {str(e)}")
        
        # 错误恢复
        fallback_result = ErrorRecoveryStrategy.get_default_analysis_result(
            "custom_agent", str(e)
        )
        
        return {
            "messages": state["messages"],
            "data": {**state["data"], "custom_analysis": fallback_result},
            "metadata": state["metadata"]
        }
```

### 配置驱动的LLM调用

```python
from src.utils.config_manager import get_llm_config
from src.utils.llm_clients import LLMClientFactory

def intelligent_llm_call(messages, agent_name="unknown"):
    """配置驱动的智能LLM调用"""
    config = get_llm_config()
    
    # 根据配置选择客户端
    if config.openai_compatible_api_key:
        client = LLMClientFactory.create_client(
            client_type="openai_compatible",
            api_key=config.openai_compatible_api_key,
            base_url=config.openai_compatible_base_url,
            model=config.openai_compatible_model
        )
    else:
        client = LLMClientFactory.create_client(
            client_type="gemini",
            api_key=config.gemini_api_key,
            model=config.gemini_model
        )
    
    # 执行调用
    return client.get_completion(
        messages=messages,
        max_retries=config.max_retries
    )
```

### 统一错误处理和日志

```python
from src.utils.exceptions import AShareAgentException
from src.utils.logging_config import setup_logger, ERROR_ICON
from src.utils.serialization import serialize_agent_state

logger = setup_logger('error_handler')

def safe_agent_execution(agent_func, state, agent_name):
    """安全的Agent执行包装器"""
    try:
        # 序列化输入状态用于调试
        input_state = serialize_agent_state(state)
        logger.debug(f"Agent {agent_name} 输入状态: {input_state}")
        
        # 执行Agent
        result = agent_func(state)
        
        # 序列化输出状态
        output_state = serialize_agent_state(result)
        logger.debug(f"Agent {agent_name} 输出状态: {output_state}")
        
        return result
        
    except AShareAgentException as e:
        logger.error(f"{ERROR_ICON} Agent {agent_name} 执行失败: {str(e)}")
        # 返回错误恢复状态
        return create_error_state(state, agent_name, str(e))
    
    except Exception as e:
        logger.error(f"{ERROR_ICON} Agent {agent_name} 意外错误: {str(e)}")
        # 返回通用错误状态
        return create_error_state(state, agent_name, f"意外错误: {str(e)}")

def create_error_state(original_state, agent_name, error_msg):
    """创建错误状态"""
    from src.utils.exceptions import ErrorRecoveryStrategy
    
    fallback_result = ErrorRecoveryStrategy.get_default_analysis_result(
        agent_name, error_msg
    )
    
    return {
        "messages": original_state["messages"],
        "data": {
            **original_state["data"],
            f"{agent_name}_analysis": fallback_result
        },
        "metadata": {
            **original_state["metadata"],
            "error": True,
            "error_agent": agent_name,
            "error_message": error_msg
        }
    }
```

## 配置管理最佳实践

### 环境配置管理

```python
# .env 文件配置
GEMINI_API_KEY=your-key-here
OPENAI_COMPATIBLE_API_KEY=your-openai-key
OPENAI_COMPATIBLE_BASE_URL=https://api.openrouter.ai/api/v1
OPENAI_COMPATIBLE_MODEL=anthropic/claude-3-haiku

# 系统配置
LOG_LEVEL=INFO
CACHE_ENABLED=true
CACHE_TTL=3600

# Agent配置
DEFAULT_CONFIDENCE_THRESHOLD=0.5
MAX_NEWS_COUNT=100
```

### 配置验证

```python
from src.utils.config_manager import get_config

def validate_system_config():
    """验证系统配置"""
    config = get_config()
    
    if not config.validate_configuration():
        print("配置验证失败！")
        return False
        
    print("配置验证通过")
    return True

# 在系统启动时验证配置
if __name__ == "__main__":
    if validate_system_config():
        # 启动系统
        main()
    else:
        exit(1)
```

### 动态配置重载

```python
from src.utils.config_manager import reload_config

def reload_system_config():
    """重新加载系统配置"""
    try:
        reload_config()
        print("配置重载成功")
    except Exception as e:
        print(f"配置重载失败: {e}")
```

## 性能优化建议

### LLM调用优化

```python
# 使用连接池减少初始化开销
from src.utils.llm_clients import LLMClientFactory

class LLMClientPool:
    def __init__(self):
        self._clients = {}
    
    def get_client(self, client_type="auto"):
        if client_type not in self._clients:
            self._clients[client_type] = LLMClientFactory.create_client(client_type)
        return self._clients[client_type]

# 全局客户端池
client_pool = LLMClientPool()
```

### 日志性能优化

```python
# 批量日志写入
from src.utils.logging_config import setup_logger
import logging

# 设置缓冲区大小
logger = setup_logger('performance_agent')
for handler in logger.handlers:
    if isinstance(handler, logging.FileHandler):
        handler.flush = lambda: None  # 禁用立即刷新
        
# 定期手动刷新
import atexit
atexit.register(lambda: [h.flush() for h in logger.handlers])
```

### 序列化优化

```python
from src.utils.serialization import serialize_agent_state
import json

def optimized_serialize(state, max_depth=5):
    """优化的序列化，限制递归深度"""
    def limited_serialize(obj, depth=0):
        if depth > max_depth:
            return f"<max_depth_reached: {type(obj).__name__}>"
        
        # 使用原始序列化逻辑但限制深度
        return serialize_agent_state(obj)
    
    return limited_serialize(state)
```

## 故障排除

### 常见问题

1. **配置加载失败**
   ```python
   from src.utils.config_manager import get_config
   
   try:
       config = get_config()
   except Exception as e:
       print(f"配置加载失败: {e}")
       # 检查环境变量是否正确设置
   ```

2. **LLM调用超时**
   ```python
   # 增加超时设置
   response = get_chat_completion(
       messages=messages,
       max_retries=5,
       client_type="auto"
   )
   ```

3. **日志文件权限问题**
   ```bash
   # 确保logs目录存在且有写权限
   mkdir -p logs
   chmod 755 logs
   ```

4. **序列化失败**
   ```python
   # 检查对象是否包含不可序列化的内容
   from src.utils.serialization import serialize_agent_state
   
   result = serialize_agent_state(state)
   if result.get("serialization_error"):
       print(f"序列化错误: {result['error']}")
   ```

### 调试工具

```python
# 配置调试信息
from src.utils.config_manager import get_config

config = get_config()
print("LLM配置:")
print(f"  Gemini API Key: {'已设置' if config.llm.gemini_api_key else '未设置'}")
print(f"  OpenAI API Key: {'已设置' if config.llm.openai_compatible_api_key else '未设置'}")

# LLM调用调试
from src.utils.llm_clients import get_chat_completion

def debug_llm_call(messages):
    print(f"发送消息: {messages}")
    response = get_chat_completion(messages, client_type="auto")
    print(f"收到响应: {response}")
    return response

# 日志级别调试
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### 性能监控

```python
import time
from src.utils.logging_config import setup_logger

logger = setup_logger('performance')

def monitor_execution(func_name):
    """执行时间监控装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func_name} 执行时间: {execution_time:.2f}秒")
            return result
        return wrapper
    return decorator

# 使用监控装饰器
@monitor_execution("LLM调用")
def monitored_llm_call(messages):
    return get_chat_completion(messages)
```

## 扩展开发

### 添加新的配置类

```python
from dataclasses import dataclass
from src.utils.config_manager import ConfigManager

@dataclass
class NewFeatureConfig:
    """新功能配置"""
    feature_enabled: bool = True
    feature_timeout: int = 30

# 扩展ConfigManager
class ExtendedConfigManager(ConfigManager):
    def __init__(self):
        super().__init__()
        self._new_feature_config = self._load_new_feature_config()
    
    def _load_new_feature_config(self) -> NewFeatureConfig:
        return NewFeatureConfig(
            feature_enabled=os.getenv("NEW_FEATURE_ENABLED", "true").lower() == "true",
            feature_timeout=int(os.getenv("NEW_FEATURE_TIMEOUT", "30"))
        )
    
    @property
    def new_feature(self) -> NewFeatureConfig:
        return self._new_feature_config
```

### 自定义LLM客户端

```python
from src.utils.llm_clients import LLMClient

class CustomLLMClient(LLMClient):
    """自定义LLM客户端"""
    
    def __init__(self, api_key, custom_param):
        self.api_key = api_key
        self.custom_param = custom_param
    
    def get_completion(self, messages, **kwargs):
        # 实现自定义LLM调用逻辑
        return self._call_custom_api(messages)
    
    def _call_custom_api(self, messages):
        # 具体实现
        pass

# 注册到工厂
from src.utils.llm_clients import LLMClientFactory

def create_custom_client(**kwargs):
    return CustomLLMClient(**kwargs)

# 扩展工厂方法
original_create = LLMClientFactory.create_client

def extended_create_client(client_type="auto", **kwargs):
    if client_type == "custom":
        return create_custom_client(**kwargs)
    return original_create(client_type, **kwargs)

LLMClientFactory.create_client = extended_create_client
```

### 自定义异常类

```python
from src.utils.exceptions import AShareAgentException

class NewFeatureError(AShareAgentException):
    """新功能相关错误"""
    def __init__(self, message: str, feature_name: str = None):
        self.feature_name = feature_name
        super().__init__(message)

# 扩展错误恢复策略
from src.utils.exceptions import ErrorRecoveryStrategy

class ExtendedErrorRecovery(ErrorRecoveryStrategy):
    @staticmethod
    def get_new_feature_fallback():
        return {"status": "fallback", "error": "新功能执行失败"}
```

这个综合的README.md文档涵盖了智能投资系统utils模块的所有核心功能，提供了详细的使用指南、配置说明、集成示例和扩展开发指导，帮助开发者全面理解和有效使用这些基础工具组件。