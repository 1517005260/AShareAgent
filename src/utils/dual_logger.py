"""
双写日志系统 - 同时写入文件系统和数据库
"""
import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager

from src.database.models import DatabaseManager


class DatabaseLogHandler(logging.Handler):
    """数据库日志处理器 - 将日志写入数据库"""
    
    def __init__(self, db_manager: DatabaseManager, user_id: Optional[int] = None):
        super().__init__()
        self.db_manager = db_manager
        self.user_id = user_id
    
    def emit(self, record):
        """发送日志记录到数据库"""
        try:
            # 构建日志记录数据
            log_data = {
                'user_id': self.user_id,
                'action': f"{record.levelname}: {record.getMessage()}",
                'resource': record.name,  # 模块名称
                'resource_id': getattr(record, 'resource_id', None),
                'details': json.dumps({
                    'level': record.levelname,
                    'pathname': record.pathname,
                    'lineno': record.lineno,
                    'funcName': record.funcName,
                    'created': record.created
                }) if hasattr(record, 'pathname') else None,
                'ip_address': getattr(record, 'ip_address', None),
                'user_agent': getattr(record, 'user_agent', None)
            }
            
            # 插入到数据库
            self._insert_log_to_db(log_data)
            
        except Exception as e:
            # 避免日志记录本身导致错误循环
            pass
    
    def _insert_log_to_db(self, log_data: Dict[str, Any]):
        """插入日志到数据库"""
        try:
            query = """
            INSERT INTO system_logs 
            (user_id, action, resource, resource_id, details, ip_address, user_agent, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                log_data['user_id'],
                log_data['action'],
                log_data['resource'],
                log_data['resource_id'],
                log_data['details'],
                log_data['ip_address'],
                log_data['user_agent'],
                datetime.now().isoformat()
            )
            
            self.db_manager.execute_update(query, params)
            
        except Exception as e:
            # 静默失败，避免影响主程序
            pass


class DualLogger:
    """双写日志系统 - 同时写入文件和数据库"""
    
    def __init__(self, name: str, db_manager: Optional[DatabaseManager] = None, 
                 user_id: Optional[int] = None):
        self.name = name
        self.db_manager = db_manager
        self.user_id = user_id
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        # 创建日志记录器
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 文件处理器
        self._setup_file_handler()
        
        # 数据库处理器
        if self.db_manager:
            self._setup_database_handler()
        
        # 控制台处理器
        self._setup_console_handler()
    
    def _setup_file_handler(self):
        """设置文件处理器"""
        # 确保logs目录存在
        logs_dir = Path(__file__).parent.parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # 创建文件处理器
        log_file = logs_dir / f"{self.name}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def _setup_database_handler(self):
        """设置数据库处理器"""
        db_handler = DatabaseLogHandler(self.db_manager, self.user_id)
        db_handler.setLevel(logging.INFO)  # 只有INFO及以上级别才写入数据库
        
        self.logger.addHandler(db_handler)
    
    def _setup_console_handler(self):
        """设置控制台处理器"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def set_user_context(self, user_id: int, ip_address: str = None, user_agent: str = None):
        """设置用户上下文信息"""
        self.user_id = user_id
        
        # 更新数据库处理器的用户信息
        for handler in self.logger.handlers:
            if isinstance(handler, DatabaseLogHandler):
                handler.user_id = user_id
        
        # 创建一个上下文适配器
        return LoggerAdapter(self.logger, {
            'user_id': user_id,
            'ip_address': ip_address,
            'user_agent': user_agent
        })
    
    def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        self.logger.error(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        self.logger.debug(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """记录CRITICAL级别日志"""
        self.logger.critical(message, extra=kwargs)


class LoggerAdapter(logging.LoggerAdapter):
    """日志适配器 - 为日志记录添加上下文信息"""
    
    def process(self, msg, kwargs):
        """处理日志消息，添加上下文信息"""
        # 将extra信息合并到kwargs中
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        
        return msg, kwargs


class DualLoggerManager:
    """双写日志管理器 - 管理所有日志实例"""
    
    _instance = None
    _loggers = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.db_manager = None
            self.initialized = True
    
    def set_database_manager(self, db_manager: DatabaseManager):
        """设置数据库管理器"""
        self.db_manager = db_manager
        
        # 更新现有的日志记录器
        for logger_name, dual_logger in self._loggers.items():
            if dual_logger.db_manager is None:
                dual_logger.db_manager = db_manager
                dual_logger._setup_logger()  # 重新设置以添加数据库处理器
    
    def get_logger(self, name: str, user_id: Optional[int] = None) -> DualLogger:
        """获取双写日志记录器"""
        logger_key = f"{name}_{user_id}" if user_id else name
        
        if logger_key not in self._loggers:
            self._loggers[logger_key] = DualLogger(
                name=name,
                db_manager=self.db_manager,
                user_id=user_id
            )
        
        return self._loggers[logger_key]


# 全局日志管理器实例
logger_manager = DualLoggerManager()


def get_dual_logger(name: str, user_id: Optional[int] = None) -> DualLogger:
    """获取双写日志记录器的便捷函数"""
    return logger_manager.get_logger(name, user_id)


def init_dual_logging_system(db_manager: DatabaseManager):
    """初始化双写日志系统"""
    logger_manager.set_database_manager(db_manager)
    
    # 创建系统级别的日志记录器
    system_logger = get_dual_logger('system')
    system_logger.info("双写日志系统初始化完成")
    
    return system_logger