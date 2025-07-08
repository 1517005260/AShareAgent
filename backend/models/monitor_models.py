"""
系统监控和日志管理数据模型
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, validator
from enum import Enum
import json


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SystemStatus(str, Enum):
    """系统状态枚举"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"


class SystemLogEntry(BaseModel):
    """系统日志条目"""
    id: int
    user_id: Optional[int] = None
    action: str
    resource: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime


class LogDisplayEntry(BaseModel):
    """日志显示条目（简化版，用于前端显示）"""
    id: int
    level: str
    message: str
    timestamp: str
    module: Optional[str] = None


class SystemLogFilter(BaseModel):
    """系统日志过滤器"""
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None


class HealthCheck(BaseModel):
    """健康检查结果"""
    service: str
    status: SystemStatus
    response_time: float
    message: Optional[str] = None
    last_check: datetime


class SystemMetrics(BaseModel):
    """系统指标"""
    timestamp: datetime
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    network_io: Optional[Dict[str, int]] = None
    active_connections: int
    error_rate: float
    avg_response_time: float


class AlertRule(BaseModel):
    """告警规则"""
    id: Optional[int] = None
    name: str
    metric: str  # cpu_usage, memory_usage, error_rate, etc.
    operator: str  # >, <, >=, <=, ==
    threshold: float
    duration: int  # 持续时间（分钟）
    is_active: bool = True
    notification_channels: List[str] = []
    created_at: Optional[datetime] = None


class Alert(BaseModel):
    """告警记录"""
    id: int
    rule_id: int
    rule_name: str
    metric: str
    current_value: float
    threshold: float
    message: str
    status: str  # active, resolved
    triggered_at: datetime
    resolved_at: Optional[datetime] = None


class MonitorService:
    """监控服务"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_system_logs(self, filters: SystemLogFilter = None, 
                       limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取系统日志（从文件系统和数据库）"""
        import os
        import glob
        from pathlib import Path
        
        # 获取日志文件路径
        logs_dir = Path(__file__).parent.parent.parent / "logs"
        
        # 收集所有日志文件
        log_files = []
        if logs_dir.exists():
            # 获取所有.log文件
            for log_file in logs_dir.glob("*.log"):
                if log_file.is_file():
                    log_files.append(log_file)
        
        # 从文件系统读取日志
        file_logs = []
        for log_file in sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 读取最后的日志条目
                    for i, line in enumerate(reversed(lines[-200:])):  # 最多读取200行
                        if line.strip():
                            parsed_log = self._parse_log_line(line.strip())
                            if parsed_log:
                                parsed_log["id"] = len(file_logs) + 1
                                parsed_log["module"] = log_file.stem
                                file_logs.append(parsed_log)
            except Exception as e:
                continue
        
        # 从数据库读取操作日志
        db_logs = []
        try:
            where_conditions = []
            params = []
            
            if filters:
                if filters.user_id is not None:
                    where_conditions.append("user_id = ?")
                    params.append(filters.user_id)
                
                if filters.action:
                    where_conditions.append("action LIKE ?")
                    params.append(f"%{filters.action}%")
                
                if filters.resource:
                    where_conditions.append("resource = ?")
                    params.append(filters.resource)
                
                if filters.start_date:
                    where_conditions.append("created_at >= ?")
                    params.append(filters.start_date.isoformat())
                
                if filters.end_date:
                    where_conditions.append("created_at <= ?")
                    params.append(filters.end_date.isoformat())
                
                if filters.ip_address:
                    where_conditions.append("ip_address = ?")
                    params.append(filters.ip_address)
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            query = f"""
            SELECT * FROM system_logs 
            WHERE {where_clause}
            ORDER BY created_at DESC 
            LIMIT ?
            """
            params.append(50)  # 限制数据库日志数量
            
            result = self.db.execute_query(query, params)
            
            for row in result:
                log_data = dict(row)
                db_logs.append({
                    "id": log_data.get('id', 0),
                    "level": "INFO",
                    "message": f"[{log_data.get('action', 'Unknown')}] {log_data.get('resource', '')}",
                    "timestamp": log_data.get('created_at', datetime.now().isoformat()),
                    "module": log_data.get('resource', 'system')
                })
        except Exception as e:
            pass
        
        # 合并并排序日志
        all_logs = file_logs + db_logs
        
        def safe_parse_timestamp(timestamp_str):
            """安全解析时间戳"""
            try:
                if isinstance(timestamp_str, str):
                    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    return datetime.now()
            except:
                return datetime.now()
        
        all_logs.sort(key=lambda x: safe_parse_timestamp(x.get('timestamp')), reverse=True)
        
        # 应用分页
        start_idx = offset
        end_idx = offset + limit
        
        return all_logs[start_idx:end_idx]
    
    def _parse_log_line(self, line: str) -> Dict[str, Any]:
        """解析日志行，返回结构化数据"""
        import re
        
        # 匹配标准格式: 2025-07-02 12:39:28 - api - INFO - message
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (\w+) - (\w+) - (.+)'
        match = re.match(pattern, line)
        
        if match:
            timestamp_str, module, level, message = match.groups()
            try:
                # 解析时间戳
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                timestamp = datetime.now()
            
            return {
                "level": level.upper(),
                "message": message.strip(),
                "timestamp": timestamp.isoformat()
            }
        else:
            # 如果不匹配标准格式，使用原始逻辑
            return {
                "level": self._extract_log_level(line),
                "message": line,
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_log_level(self, line: str) -> str:
        """从日志行中提取日志级别"""
        line_upper = line.upper()
        if " - ERROR - " in line_upper or " - EXCEPTION - " in line_upper:
            return "ERROR"
        elif " - WARNING - " in line_upper or " - WARN - " in line_upper:
            return "WARNING"
        elif " - DEBUG - " in line_upper:
            return "DEBUG"
        elif " - INFO - " in line_upper:
            return "INFO"
        elif "ERROR" in line_upper or "EXCEPTION" in line_upper:
            return "ERROR"
        elif "WARNING" in line_upper or "WARN" in line_upper:
            return "WARNING"
        elif "DEBUG" in line_upper:
            return "DEBUG"
        else:
            return "INFO"
    
    def get_log_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取日志摘要"""
        start_time = datetime.now() - timedelta(hours=hours)
        
        # 按操作类型统计
        action_query = """
        SELECT action, COUNT(*) as count
        FROM system_logs
        WHERE created_at >= ?
        GROUP BY action
        ORDER BY count DESC
        LIMIT 20
        """
        action_result = self.db.execute_query(action_query, (start_time.isoformat(),))
        actions_by_type = [{"action": row['action'], "count": row['count']} for row in action_result]
        
        # 按用户统计
        user_query = """
        SELECT u.username, COUNT(l.id) as count
        FROM users u
        LEFT JOIN system_logs l ON u.id = l.user_id AND l.created_at >= ?
        WHERE l.id IS NOT NULL
        GROUP BY u.id, u.username
        ORDER BY count DESC
        LIMIT 10
        """
        user_result = self.db.execute_query(user_query, (start_time.isoformat(),))
        actions_by_user = [{"username": row['username'], "count": row['count']} for row in user_result]
        
        # 按资源统计
        resource_query = """
        SELECT resource, COUNT(*) as count
        FROM system_logs
        WHERE created_at >= ? AND resource IS NOT NULL
        GROUP BY resource
        ORDER BY count DESC
        LIMIT 10
        """
        resource_result = self.db.execute_query(resource_query, (start_time.isoformat(),))
        actions_by_resource = [{"resource": row['resource'], "count": row['count']} for row in resource_result]
        
        # 按IP地址统计
        ip_query = """
        SELECT ip_address, COUNT(*) as count
        FROM system_logs
        WHERE created_at >= ? AND ip_address IS NOT NULL
        GROUP BY ip_address
        ORDER BY count DESC
        LIMIT 10
        """
        ip_result = self.db.execute_query(ip_query, (start_time.isoformat(),))
        actions_by_ip = [{"ip_address": row['ip_address'], "count": row['count']} for row in ip_result]
        
        # 总计
        total_query = """
        SELECT COUNT(*) as total
        FROM system_logs
        WHERE created_at >= ?
        """
        total_result = self.db.execute_query(total_query, (start_time.isoformat(),))
        total_logs = total_result[0]['total'] if total_result else 0
        
        return {
            "time_range_hours": hours,
            "total_logs": total_logs,
            "actions_by_type": actions_by_type,
            "actions_by_user": actions_by_user,
            "actions_by_resource": actions_by_resource,
            "actions_by_ip": actions_by_ip
        }
    
    def perform_health_checks(self) -> List[HealthCheck]:
        """执行健康检查"""
        health_checks = []
        
        # 数据库健康检查
        db_health = self._check_database_health()
        health_checks.append(db_health)
        
        # API健康检查
        api_health = self._check_api_health()
        health_checks.append(api_health)
        
        # 存储健康检查
        storage_health = self._check_storage_health()
        health_checks.append(storage_health)
        
        return health_checks
    
    def _check_database_health(self) -> HealthCheck:
        """检查数据库健康状态"""
        import time
        
        try:
            start_time = time.time()
            # 执行简单查询测试数据库连接
            self.db.execute_query("SELECT 1")
            response_time = (time.time() - start_time) * 1000
            
            if response_time < 100:
                status = SystemStatus.HEALTHY
                message = "数据库响应正常"
            elif response_time < 500:
                status = SystemStatus.WARNING
                message = f"数据库响应较慢: {response_time:.1f}ms"
            else:
                status = SystemStatus.CRITICAL
                message = f"数据库响应异常缓慢: {response_time:.1f}ms"
            
            return HealthCheck(
                service="database",
                status=status,
                response_time=response_time,
                message=message,
                last_check=datetime.now()
            )
            
        except Exception as e:
            return HealthCheck(
                service="database",
                status=SystemStatus.DOWN,
                response_time=0,
                message=f"数据库连接失败: {str(e)}",
                last_check=datetime.now()
            )
    
    def _check_api_health(self) -> HealthCheck:
        """检查API健康状态"""
        try:
            # 检查最近API调用的成功率
            query = """
            SELECT 
                COUNT(*) as total_calls,
                COUNT(CASE WHEN status_code < 400 THEN 1 END) as success_calls,
                AVG(response_time) as avg_response_time
            FROM api_usage_stats
            WHERE created_at >= datetime('now', '-1 hour')
            """
            result = self.db.execute_query(query)
            
            if result:
                data = dict(result[0])
                total_calls = data.get('total_calls', 0)
                success_calls = data.get('success_calls', 0)
                avg_response_time = data.get('avg_response_time', 0) or 0
                
                if total_calls > 0:
                    success_rate = (success_calls / total_calls) * 100
                    
                    if success_rate >= 99 and avg_response_time < 1000:
                        status = SystemStatus.HEALTHY
                        message = f"API运行正常，成功率: {success_rate:.1f}%"
                    elif success_rate >= 95:
                        status = SystemStatus.WARNING
                        message = f"API运行状况一般，成功率: {success_rate:.1f}%"
                    else:
                        status = SystemStatus.CRITICAL
                        message = f"API运行异常，成功率: {success_rate:.1f}%"
                else:
                    status = SystemStatus.WARNING
                    message = "最近一小时无API调用"
                
                return HealthCheck(
                    service="api",
                    status=status,
                    response_time=avg_response_time,
                    message=message,
                    last_check=datetime.now()
                )
            
            return HealthCheck(
                service="api",
                status=SystemStatus.WARNING,
                response_time=0,
                message="无法获取API统计数据",
                last_check=datetime.now()
            )
            
        except Exception as e:
            return HealthCheck(
                service="api",
                status=SystemStatus.DOWN,
                response_time=0,
                message=f"API健康检查失败: {str(e)}",
                last_check=datetime.now()
            )
    
    def _check_storage_health(self) -> HealthCheck:
        """检查存储健康状态"""
        import os
        import shutil
        
        try:
            # 检查数据库文件大小和磁盘空间
            db_size = os.path.getsize(self.db.db_path)
            db_dir = os.path.dirname(self.db.db_path)
            disk_usage = shutil.disk_usage(db_dir)
            
            free_space_gb = disk_usage.free / (1024**3)
            used_space_percent = (disk_usage.used / disk_usage.total) * 100
            
            if free_space_gb > 1 and used_space_percent < 90:
                status = SystemStatus.HEALTHY
                message = f"存储空间充足，剩余: {free_space_gb:.1f}GB"
            elif free_space_gb > 0.5 and used_space_percent < 95:
                status = SystemStatus.WARNING
                message = f"存储空间不足，剩余: {free_space_gb:.1f}GB"
            else:
                status = SystemStatus.CRITICAL
                message = f"存储空间严重不足，剩余: {free_space_gb:.1f}GB"
            
            return HealthCheck(
                service="storage",
                status=status,
                response_time=0,
                message=message,
                last_check=datetime.now()
            )
            
        except Exception as e:
            return HealthCheck(
                service="storage",
                status=SystemStatus.DOWN,
                response_time=0,
                message=f"存储检查失败: {str(e)}",
                last_check=datetime.now()
            )
    
    def get_system_metrics(self, hours: int = 1) -> List[SystemMetrics]:
        """获取系统指标"""
        import psutil
        
        try:
            # 获取当前系统指标
            current_metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=psutil.cpu_percent(),
                memory_usage=psutil.virtual_memory().percent,
                disk_usage=psutil.disk_usage('/').percent,
                active_connections=len(psutil.net_connections()),
                error_rate=self._calculate_error_rate(hours),
                avg_response_time=self._calculate_avg_response_time(hours)
            )
            
            # TODO: 如果需要历史指标，可以从数据库或缓存中获取
            return [current_metrics]
            
        except Exception as e:
            # 如果psutil不可用，返回基础指标
            return [SystemMetrics(
                timestamp=datetime.now(),
                active_connections=self._get_active_sessions(),
                error_rate=self._calculate_error_rate(hours),
                avg_response_time=self._calculate_avg_response_time(hours)
            )]
    
    def _calculate_error_rate(self, hours: int) -> float:
        """计算错误率"""
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            query = """
            SELECT 
                COUNT(*) as total_calls,
                COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_calls
            FROM api_usage_stats
            WHERE created_at >= ?
            """
            result = self.db.execute_query(query, (start_time.isoformat(),))
            
            if result:
                data = dict(result[0])
                total_calls = data.get('total_calls', 0)
                error_calls = data.get('error_calls', 0)
                
                if total_calls > 0:
                    return (error_calls / total_calls) * 100
            
            return 0.0
        except:
            return 0.0
    
    def _calculate_avg_response_time(self, hours: int) -> float:
        """计算平均响应时间"""
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            query = """
            SELECT AVG(response_time) as avg_time
            FROM api_usage_stats
            WHERE created_at >= ?
            """
            result = self.db.execute_query(query, (start_time.isoformat(),))
            
            if result and result[0]['avg_time']:
                return float(result[0]['avg_time'])
            
            return 0.0
        except:
            return 0.0
    
    def _get_active_sessions(self) -> int:
        """获取活跃会话数"""
        try:
            query = """
            SELECT COUNT(*) as count
            FROM users
            WHERE last_login >= datetime('now', '-1 hour') AND is_active = 1
            """
            result = self.db.execute_query(query)
            return result[0]['count'] if result else 0
        except:
            return 0
    
    def get_error_logs(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """获取错误日志"""
        start_time = datetime.now() - timedelta(hours=hours)
        
        # 从系统日志中获取错误相关的操作
        error_actions = [
            'login_failed', 'analysis_failed', 'portfolio_error', 
            'api_error', 'system_error', 'database_error'
        ]
        
        placeholders = ','.join(['?' for _ in error_actions])
        query = f"""
        SELECT * FROM system_logs
        WHERE created_at >= ? AND (
            action IN ({placeholders}) OR
            action LIKE '%_failed' OR
            action LIKE '%_error'
        )
        ORDER BY created_at DESC
        LIMIT ?
        """
        
        params = [start_time.isoformat()] + error_actions + [limit]
        result = self.db.execute_query(query, params)
        
        error_logs = []
        for row in result:
            log_data = dict(row)
            if log_data.get('details'):
                try:
                    log_data['details'] = json.loads(log_data['details'])
                except json.JSONDecodeError:
                    log_data['details'] = {}
            error_logs.append(log_data)
        
        return error_logs
    
    def get_performance_analysis(self, hours: int = 24) -> Dict[str, Any]:
        """获取性能分析"""
        start_time = datetime.now() - timedelta(hours=hours)
        
        # API性能分析
        api_query = """
        SELECT 
            endpoint,
            COUNT(*) as call_count,
            AVG(response_time) as avg_response_time,
            MIN(response_time) as min_response_time,
            MAX(response_time) as max_response_time,
            COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count
        FROM api_usage_stats
        WHERE created_at >= ?
        GROUP BY endpoint
        ORDER BY avg_response_time DESC
        """
        api_result = self.db.execute_query(api_query, (start_time.isoformat(),))
        
        api_performance = []
        for row in api_result:
            data = dict(row)
            data['error_rate'] = (data['error_count'] / data['call_count'] * 100) if data['call_count'] > 0 else 0
            api_performance.append(data)
        
        # 用户活动分析
        user_query = """
        SELECT 
            COUNT(DISTINCT user_id) as active_users,
            COUNT(*) as total_actions
        FROM system_logs
        WHERE created_at >= ? AND user_id IS NOT NULL
        """
        user_result = self.db.execute_query(user_query, (start_time.isoformat(),))
        user_activity = dict(user_result[0]) if user_result else {}
        
        # 资源使用分析
        resource_query = """
        SELECT 
            resource,
            COUNT(*) as usage_count,
            COUNT(DISTINCT user_id) as unique_users
        FROM system_logs
        WHERE created_at >= ? AND resource IS NOT NULL
        GROUP BY resource
        ORDER BY usage_count DESC
        """
        resource_result = self.db.execute_query(resource_query, (start_time.isoformat(),))
        resource_usage = [dict(row) for row in resource_result]
        
        return {
            "time_range_hours": hours,
            "api_performance": api_performance,
            "user_activity": user_activity,
            "resource_usage": resource_usage
        }