"""
统一配置管理模块
"""
import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path

from src.utils.exceptions import ConfigurationError


@dataclass
class LLMConfig:
    """LLM配置"""
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"
    openai_compatible_api_key: Optional[str] = None
    openai_compatible_base_url: Optional[str] = None
    openai_compatible_model: Optional[str] = None
    max_retries: int = 3
    timeout: int = 30


@dataclass
class SystemConfig:
    """系统配置"""
    log_level: str = "INFO"
    max_output_size: int = 10000
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 缓存过期时间（秒）


@dataclass
class AgentConfig:
    """Agent配置"""
    default_confidence_threshold: float = 0.5
    max_news_count: int = 100
    sentiment_analysis_days: int = 7
    risk_score_threshold: int = 8


@dataclass
class MarketDataConfig:
    """市场数据配置"""
    default_history_days: int = 365
    api_timeout: int = 30
    max_retry_attempts: int = 3
    cache_enabled: bool = True


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self._llm_config: Optional[LLMConfig] = None
        self._system_config: Optional[SystemConfig] = None
        self._agent_config: Optional[AgentConfig] = None
        self._market_data_config: Optional[MarketDataConfig] = None
        self._logger = logging.getLogger(__name__)
        
        # 加载配置
        self._load_configs()
    
    def _load_configs(self):
        """加载所有配置"""
        try:
            self._llm_config = self._load_llm_config()
            self._system_config = self._load_system_config()
            self._agent_config = self._load_agent_config()
            self._market_data_config = self._load_market_data_config()
            self._logger.info("配置加载完成")
        except Exception as e:
            raise ConfigurationError(f"配置加载失败: {str(e)}")
    
    def _load_llm_config(self) -> LLMConfig:
        """加载LLM配置"""
        return LLMConfig(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            openai_compatible_api_key=os.getenv("OPENAI_COMPATIBLE_API_KEY"),
            openai_compatible_base_url=os.getenv("OPENAI_COMPATIBLE_BASE_URL"),
            openai_compatible_model=os.getenv("OPENAI_COMPATIBLE_MODEL"),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
            timeout=int(os.getenv("LLM_TIMEOUT", "30"))
        )
    
    def _load_system_config(self) -> SystemConfig:
        """加载系统配置"""
        return SystemConfig(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_output_size=int(os.getenv("MAX_OUTPUT_SIZE", "10000")),
            cache_enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            cache_ttl=int(os.getenv("CACHE_TTL", "3600"))
        )
    
    def _load_agent_config(self) -> AgentConfig:
        """加载Agent配置"""
        return AgentConfig(
            default_confidence_threshold=float(os.getenv("DEFAULT_CONFIDENCE_THRESHOLD", "0.5")),
            max_news_count=int(os.getenv("MAX_NEWS_COUNT", "100")),
            sentiment_analysis_days=int(os.getenv("SENTIMENT_ANALYSIS_DAYS", "7")),
            risk_score_threshold=int(os.getenv("RISK_SCORE_THRESHOLD", "8"))
        )
    
    def _load_market_data_config(self) -> MarketDataConfig:
        """加载市场数据配置"""
        return MarketDataConfig(
            default_history_days=int(os.getenv("DEFAULT_HISTORY_DAYS", "365")),
            api_timeout=int(os.getenv("MARKET_API_TIMEOUT", "30")),
            max_retry_attempts=int(os.getenv("MARKET_API_MAX_RETRIES", "3")),
            cache_enabled=os.getenv("MARKET_CACHE_ENABLED", "true").lower() == "true"
        )
    
    @property
    def llm(self) -> LLMConfig:
        """获取LLM配置"""
        return self._llm_config
    
    @property
    def system(self) -> SystemConfig:
        """获取系统配置"""
        return self._system_config
    
    @property
    def agent(self) -> AgentConfig:
        """获取Agent配置"""
        return self._agent_config
    
    @property
    def market_data(self) -> MarketDataConfig:
        """获取市场数据配置"""
        return self._market_data_config
    
    def validate_configuration(self) -> bool:
        """验证配置的有效性"""
        errors = []
        
        # 验证LLM配置
        if not self._llm_config.gemini_api_key and not self._llm_config.openai_compatible_api_key:
            errors.append("至少需要配置Gemini API Key或OpenAI兼容API Key")
        
        # 验证OpenAI兼容配置的完整性
        if self._llm_config.openai_compatible_api_key:
            if not self._llm_config.openai_compatible_base_url:
                errors.append("配置了OpenAI兼容API Key但缺少Base URL")
            if not self._llm_config.openai_compatible_model:
                errors.append("配置了OpenAI兼容API Key但缺少模型名称")
        
        # 验证数值配置的合理性
        if self._agent_config.default_confidence_threshold < 0 or self._agent_config.default_confidence_threshold > 1:
            errors.append("置信度阈值必须在0-1之间")
        
        if self._agent_config.max_news_count <= 0:
            errors.append("最大新闻数量必须大于0")
        
        if errors:
            error_msg = "配置验证失败:\n" + "\n".join(f"- {error}" for error in errors)
            self._logger.error(error_msg)
            return False
        
        return True
    
    def get_env_template(self) -> str:
        """获取环境变量模板"""
        return """# AI投资系统环境配置

# LLM配置
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash

# OpenAI兼容API配置（可选）
OPENAI_COMPATIBLE_API_KEY=your-openai-compatible-api-key
OPENAI_COMPATIBLE_BASE_URL=https://your-api-endpoint.com/v1
OPENAI_COMPATIBLE_MODEL=your-model-name

# LLM调用配置
LLM_MAX_RETRIES=3
LLM_TIMEOUT=30

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

# 市场数据配置
DEFAULT_HISTORY_DAYS=365
MARKET_API_TIMEOUT=30
MARKET_API_MAX_RETRIES=3
MARKET_CACHE_ENABLED=true
"""
    
    def save_env_template(self, file_path: str = ".env.example"):
        """保存环境变量模板到文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.get_env_template())
        self._logger.info(f"环境变量模板已保存到: {file_path}")


# 全局配置实例
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """获取全局配置实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def reload_config():
    """重新加载配置"""
    global _config_manager
    _config_manager = ConfigManager()


# 便捷函数
def get_llm_config() -> LLMConfig:
    """获取LLM配置"""
    return get_config().llm


def get_system_config() -> SystemConfig:
    """获取系统配置"""
    return get_config().system


def get_agent_config() -> AgentConfig:
    """获取Agent配置"""
    return get_config().agent


def get_market_data_config() -> MarketDataConfig:
    """获取市场数据配置"""
    return get_config().market_data