"""
系统监控和日志管理API路由
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from backend.models.api_models import ApiResponse
from backend.models.auth_models import UserInDB
from backend.models.monitor_models import (
    MonitorService, SystemLogEntry, SystemLogFilter, HealthCheck,
    SystemMetrics, LogLevel
)
from backend.services.auth_service import get_current_active_user, require_permission, require_admin
from backend.dependencies import get_database_manager
from src.database.models import DatabaseManager
import logging

logger = logging.getLogger("monitor_router")

# 创建路由器
router = APIRouter(prefix="/api/monitor", tags=["系统监控和日志管理"])


def get_monitor_service(db_manager: DatabaseManager = Depends(get_database_manager)) -> MonitorService:
    """获取监控服务实例"""
    return MonitorService(db_manager)


@router.get("/health", response_model=ApiResponse[List[HealthCheck]])
async def get_health_status(
    current_user: UserInDB = Depends(require_permission("system:monitor")),
    monitor_service: MonitorService = Depends(get_monitor_service)
):
    """
    获取系统健康状态检查
    
    执行数据库、API、存储等核心服务的健康检查
    """
    try:
        health_checks = monitor_service.perform_health_checks()
        
        return ApiResponse(
            success=True,
            message="系统健康检查完成",
            data=health_checks
        )
        
    except Exception as e:
        logger.error(f"系统健康检查失败: {e}")
        return ApiResponse(
            success=False,
            message=f"系统健康检查失败: {str(e)}",
            data=[]
        )


@router.get("/metrics", response_model=ApiResponse[List[SystemMetrics]])
async def get_system_metrics(
    hours: int = Query(1, description="获取过去几小时的指标", ge=1, le=24),
    current_user: UserInDB = Depends(require_permission("system:monitor")),
    monitor_service: MonitorService = Depends(get_monitor_service)
):
    """获取系统性能指标"""
    try:
        metrics = monitor_service.get_system_metrics(hours)
        
        return ApiResponse(
            success=True,
            message="获取系统指标成功",
            data=metrics
        )
        
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取系统指标失败: {str(e)}",
            data=[]
        )


@router.get("/logs", response_model=ApiResponse[List[SystemLogEntry]])
async def get_system_logs(
    user_id: Optional[int] = Query(None, description="用户ID过滤"),
    action: Optional[str] = Query(None, description="操作类型过滤"),
    resource: Optional[str] = Query(None, description="资源类型过滤"),
    hours: Optional[int] = Query(24, description="时间范围（小时）", ge=1, le=168),
    limit: int = Query(100, description="返回记录数", ge=1, le=1000),
    offset: int = Query(0, description="跳过记录数", ge=0),
    current_user: UserInDB = Depends(require_permission("system:logs")),
    monitor_service: MonitorService = Depends(get_monitor_service)
):
    """
    获取系统日志
    
    - **user_id**: 筛选特定用户的操作日志
    - **action**: 筛选特定操作类型
    - **resource**: 筛选特定资源类型
    - **hours**: 获取过去几小时的日志
    """
    try:
        # 构建过滤器
        filters = SystemLogFilter()
        if user_id is not None:
            filters.user_id = user_id
        if action:
            filters.action = action
        if resource:
            filters.resource = resource
        if hours:
            filters.start_date = datetime.now() - timedelta(hours=hours)
        
        logs = monitor_service.get_system_logs(filters, limit, offset)
        
        return ApiResponse(
            success=True,
            message=f"获取系统日志成功，共 {len(logs)} 条记录",
            data=logs
        )
        
    except Exception as e:
        logger.error(f"获取系统日志失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取系统日志失败: {str(e)}",
            data=[]
        )


@router.get("/logs/summary", response_model=ApiResponse[Dict[str, Any]])
async def get_log_summary(
    hours: int = Query(24, description="统计过去几小时的日志", ge=1, le=168),
    current_user: UserInDB = Depends(require_permission("system:logs")),
    monitor_service: MonitorService = Depends(get_monitor_service)
):
    """获取日志统计摘要"""
    try:
        summary = monitor_service.get_log_summary(hours)
        
        return ApiResponse(
            success=True,
            message="获取日志摘要成功",
            data=summary
        )
        
    except Exception as e:
        logger.error(f"获取日志摘要失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取日志摘要失败: {str(e)}",
            data={}
        )


@router.get("/logs/errors", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_error_logs(
    hours: int = Query(24, description="获取过去几小时的错误日志", ge=1, le=168),
    limit: int = Query(100, description="返回记录数", ge=1, le=1000),
    current_user: UserInDB = Depends(require_permission("system:logs")),
    monitor_service: MonitorService = Depends(get_monitor_service)
):
    """获取系统错误日志"""
    try:
        error_logs = monitor_service.get_error_logs(hours, limit)
        
        return ApiResponse(
            success=True,
            message=f"获取错误日志成功，共 {len(error_logs)} 条记录",
            data=error_logs
        )
        
    except Exception as e:
        logger.error(f"获取错误日志失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取错误日志失败: {str(e)}",
            data=[]
        )


@router.get("/performance", response_model=ApiResponse[Dict[str, Any]])
async def get_performance_analysis(
    hours: int = Query(24, description="分析过去几小时的性能", ge=1, le=168),
    current_user: UserInDB = Depends(require_permission("system:monitor")),
    monitor_service: MonitorService = Depends(get_monitor_service)
):
    """获取系统性能分析"""
    try:
        performance = monitor_service.get_performance_analysis(hours)
        
        return ApiResponse(
            success=True,
            message="获取性能分析成功",
            data=performance
        )
        
    except Exception as e:
        logger.error(f"获取性能分析失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取性能分析失败: {str(e)}",
            data={}
        )


@router.get("/dashboard", response_model=ApiResponse[Dict[str, Any]])
async def get_monitor_dashboard(
    current_user: UserInDB = Depends(require_permission("system:monitor")),
    monitor_service: MonitorService = Depends(get_monitor_service)
):
    """获取监控仪表板数据"""
    try:
        # 健康检查
        health_checks = monitor_service.perform_health_checks()
        overall_health = "healthy"
        if any(check.status == "critical" for check in health_checks):
            overall_health = "critical"
        elif any(check.status == "warning" for check in health_checks):
            overall_health = "warning"
        
        # 系统指标
        metrics = monitor_service.get_system_metrics(1)
        current_metrics = metrics[0] if metrics else None
        
        # 日志摘要
        log_summary = monitor_service.get_log_summary(24)
        
        # 错误日志数量
        error_logs = monitor_service.get_error_logs(24, 10)
        
        # 性能分析
        performance = monitor_service.get_performance_analysis(24)
        
        dashboard_data = {
            "overall_health": overall_health,
            "health_checks": health_checks,
            "current_metrics": current_metrics,
            "log_summary": {
                "total_logs_24h": log_summary.get("total_logs", 0),
                "error_logs_24h": len(error_logs),
                "top_actions": log_summary.get("actions_by_type", [])[:5]
            },
            "performance_summary": {
                "api_count": len(performance.get("api_performance", [])),
                "active_users": performance.get("user_activity", {}).get("active_users", 0),
                "avg_response_time": sum(api["avg_response_time"] for api in performance.get("api_performance", [])) / max(len(performance.get("api_performance", [])), 1)
            }
        }
        
        return ApiResponse(
            success=True,
            message="获取监控仪表板数据成功",
            data=dashboard_data
        )
        
    except Exception as e:
        logger.error(f"获取监控仪表板数据失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取监控仪表板数据失败: {str(e)}",
            data={}
        )


@router.get("/logs/user/{user_id}", response_model=ApiResponse[List[SystemLogEntry]])
async def get_user_logs(
    user_id: int,
    hours: int = Query(24, description="获取过去几小时的日志", ge=1, le=168),
    limit: int = Query(50, description="返回记录数", ge=1, le=500),
    current_user: UserInDB = Depends(get_current_active_user),
    monitor_service: MonitorService = Depends(get_monitor_service)
):
    """获取指定用户的操作日志"""
    try:
        # 检查权限：用户只能查看自己的日志，管理员可以查看所有用户的日志
        from backend.services.auth_service import get_auth_service
        auth_service = get_auth_service()
        has_admin_permission = auth_service.user_auth.has_permission(current_user.id, "system:logs")
        
        if not has_admin_permission and current_user.id != user_id:
            return ApiResponse(
                success=False,
                message="无权限查看其他用户的日志",
                data=[]
            )
        
        # 构建过滤器
        filters = SystemLogFilter()
        filters.user_id = user_id
        filters.start_date = datetime.now() - timedelta(hours=hours)
        
        logs = monitor_service.get_system_logs(filters, limit, 0)
        
        return ApiResponse(
            success=True,
            message=f"获取用户日志成功，共 {len(logs)} 条记录",
            data=logs
        )
        
    except Exception as e:
        logger.error(f"获取用户日志失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取用户日志失败: {str(e)}",
            data=[]
        )


@router.get("/api-usage", response_model=ApiResponse[Dict[str, Any]])
async def get_api_usage_analysis(
    hours: int = Query(24, description="分析过去几小时的API使用", ge=1, le=168),
    current_user: UserInDB = Depends(require_permission("system:monitor")),
    monitor_service: MonitorService = Depends(get_monitor_service)
):
    """获取API使用情况分析"""
    try:
        start_time = datetime.now() - timedelta(hours=hours)
        
        # API调用统计
        api_query = """
        SELECT 
            endpoint,
            method,
            COUNT(*) as call_count,
            AVG(response_time) as avg_response_time,
            COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count,
            COUNT(CASE WHEN status_code >= 500 THEN 1 END) as server_error_count
        FROM api_usage_stats
        WHERE created_at >= ?
        GROUP BY endpoint, method
        ORDER BY call_count DESC
        """
        api_result = monitor_service.db.execute_query(api_query, (start_time.isoformat(),))
        
        api_stats = []
        for row in api_result:
            data = dict(row)
            data['error_rate'] = (data['error_count'] / data['call_count'] * 100) if data['call_count'] > 0 else 0
            data['server_error_rate'] = (data['server_error_count'] / data['call_count'] * 100) if data['call_count'] > 0 else 0
            api_stats.append(data)
        
        # 状态码分布
        status_query = """
        SELECT 
            CASE 
                WHEN status_code < 300 THEN 'Success (2xx)'
                WHEN status_code < 400 THEN 'Redirect (3xx)'
                WHEN status_code < 500 THEN 'Client Error (4xx)'
                ELSE 'Server Error (5xx)'
            END as category,
            COUNT(*) as count
        FROM api_usage_stats
        WHERE created_at >= ?
        GROUP BY category
        """
        status_result = monitor_service.db.execute_query(status_query, (start_time.isoformat(),))
        status_distribution = {row['category']: row['count'] for row in status_result}
        
        # 按小时分布
        hourly_query = """
        SELECT 
            strftime('%H', created_at) as hour,
            COUNT(*) as count,
            AVG(response_time) as avg_response_time
        FROM api_usage_stats
        WHERE created_at >= ?
        GROUP BY hour
        ORDER BY hour
        """
        hourly_result = monitor_service.db.execute_query(hourly_query, (start_time.isoformat(),))
        hourly_stats = [dict(row) for row in hourly_result]
        
        return ApiResponse(
            success=True,
            message="获取API使用分析成功",
            data={
                "time_range_hours": hours,
                "api_endpoints": api_stats,
                "status_distribution": status_distribution,
                "hourly_distribution": hourly_stats
            }
        )
        
    except Exception as e:
        logger.error(f"获取API使用分析失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取API使用分析失败: {str(e)}",
            data={}
        )


@router.get("/alerts", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_system_alerts(
    current_user: UserInDB = Depends(require_admin),
    monitor_service: MonitorService = Depends(get_monitor_service)
):
    """获取系统告警信息（简化实现）"""
    try:
        alerts = []
        
        # 检查系统健康状态并生成告警
        health_checks = monitor_service.perform_health_checks()
        for check in health_checks:
            if check.status in ["warning", "critical"]:
                alerts.append({
                    "id": f"health_{check.service}",
                    "type": "system_health",
                    "service": check.service,
                    "status": check.status,
                    "message": check.message,
                    "timestamp": check.last_check,
                    "response_time": check.response_time
                })
        
        # 检查错误率
        error_rate = monitor_service._calculate_error_rate(1)
        if error_rate > 5:  # 错误率超过5%
            alerts.append({
                "id": "high_error_rate",
                "type": "performance",
                "service": "api",
                "status": "warning" if error_rate < 10 else "critical",
                "message": f"API错误率过高: {error_rate:.1f}%",
                "timestamp": datetime.now(),
                "error_rate": error_rate
            })
        
        # 检查响应时间
        avg_response_time = monitor_service._calculate_avg_response_time(1)
        if avg_response_time > 2000:  # 响应时间超过2秒
            alerts.append({
                "id": "slow_response",
                "type": "performance",
                "service": "api",
                "status": "warning" if avg_response_time < 5000 else "critical",
                "message": f"API响应时间过慢: {avg_response_time:.0f}ms",
                "timestamp": datetime.now(),
                "response_time": avg_response_time
            })
        
        return ApiResponse(
            success=True,
            message=f"获取系统告警成功，共 {len(alerts)} 个告警",
            data=alerts
        )
        
    except Exception as e:
        logger.error(f"获取系统告警失败: {e}")
        return ApiResponse(
            success=False,
            message=f"获取系统告警失败: {str(e)}",
            data=[]
        )