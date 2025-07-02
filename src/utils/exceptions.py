"""
自定义异常类，提供更精确的错误处理
"""


class AShareAgentException(Exception):
    """AI投资系统的基础异常类"""
    pass


class DataValidationError(AShareAgentException):
    """数据验证错误"""
    def __init__(self, message: str, field_name: str = None, expected_format: str = None):
        self.field_name = field_name
        self.expected_format = expected_format
        super().__init__(message)


class LLMConnectionError(AShareAgentException):
    """LLM连接错误"""
    def __init__(self, message: str, retry_count: int = 0):
        self.retry_count = retry_count
        super().__init__(message)


class MarketDataError(AShareAgentException):
    """市场数据获取错误"""
    def __init__(self, message: str, ticker: str = None, data_type: str = None):
        self.ticker = ticker
        self.data_type = data_type
        super().__init__(message)


class AgentExecutionError(AShareAgentException):
    """Agent执行错误"""
    def __init__(self, message: str, agent_name: str = None, state_info: str = None):
        self.agent_name = agent_name
        self.state_info = state_info
        super().__init__(message)


class ConfigurationError(AShareAgentException):
    """配置错误"""
    pass


class PortfolioError(AShareAgentException):
    """投资组合管理错误"""
    def __init__(self, message: str, portfolio_info: str = None):
        self.portfolio_info = portfolio_info
        super().__init__(message)


# 错误恢复策略
class ErrorRecoveryStrategy:
    """错误恢复策略"""
    
    @staticmethod
    def get_default_analysis_result(agent_name: str, error_msg: str = None):
        """获取默认的分析结果，用于错误恢复"""
        return {
            "signal": "neutral",
            "confidence": 0.0,
            "reasoning": f"{agent_name}分析失败" + (f": {error_msg}" if error_msg else "，返回中性信号"),
            "error": True
        }
    
    @staticmethod
    def get_safe_financial_metrics():
        """获取安全的默认财务指标"""
        return [{
            "pe_ratio": 0.0,
            "market_cap": 0.0,
            "revenue": 0.0,
            "net_income": 0.0,
            "error": "数据获取失败"
        }]
    
    @staticmethod
    def get_safe_price_data():
        """获取安全的默认价格数据"""
        return [{
            "close": 0.0,
            "open": 0.0,
            "high": 0.0,
            "low": 0.0,
            "volume": 0,
            "error": "价格数据获取失败"
        }]