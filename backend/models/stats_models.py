"""
数据统计和报表数据模型
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, validator
from enum import Enum


class TimeRange(str, Enum):
    """时间范围枚举"""
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1m"
    MONTH_3 = "3m"
    MONTH_6 = "6m"
    YEAR_1 = "1y"
    ALL = "all"


class StatsType(str, Enum):
    """统计类型枚举"""
    USER = "user"
    ANALYSIS = "analysis"
    PORTFOLIO = "portfolio"
    SYSTEM = "system"
    API = "api"


class UserStats(BaseModel):
    """用户统计"""
    total_users: int
    active_users: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int
    user_distribution_by_role: Dict[str, int]
    login_stats: Dict[str, int]


class AnalysisStats(BaseModel):
    """分析任务统计"""
    total_tasks: int
    completed_tasks: int
    running_tasks: int
    failed_tasks: int
    success_rate: float
    avg_execution_time: Optional[float] = None
    tasks_by_date: List[Dict[str, Union[str, int]]]
    popular_stocks: List[Dict[str, Union[str, int]]]
    tasks_by_user: List[Dict[str, Union[str, int]]]


class PortfolioStats(BaseModel):
    """投资组合统计"""
    total_portfolios: int
    active_portfolios: int
    total_capital: float
    total_market_value: float
    total_return: float
    avg_return_rate: float
    top_performing_portfolios: List[Dict[str, Any]]
    portfolio_distribution: Dict[str, int]
    holdings_distribution: List[Dict[str, Union[str, int]]]


class SystemStats(BaseModel):
    """系统统计"""
    uptime: str
    total_configs: int
    database_size: str
    memory_usage: Optional[str] = None
    cpu_usage: Optional[float] = None
    active_sessions: int
    error_rate: float
    response_time_avg: float


class APIStats(BaseModel):
    """API调用统计"""
    total_calls: int
    calls_today: int
    success_rate: float
    avg_response_time: float
    calls_by_endpoint: List[Dict[str, Union[str, int]]]
    calls_by_user: List[Dict[str, Union[str, int]]]
    error_distribution: Dict[str, int]
    hourly_distribution: List[Dict[str, Union[str, int]]]


class OverallStats(BaseModel):
    """总体统计"""
    user_stats: UserStats
    analysis_stats: AnalysisStats
    portfolio_stats: PortfolioStats
    system_stats: SystemStats
    api_stats: APIStats
    generated_at: datetime


class StatsService:
    """统计服务"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_user_stats(self, time_range: TimeRange = TimeRange.ALL) -> UserStats:
        """获取用户统计"""
        # 计算时间范围
        start_date = self._get_start_date(time_range)
        
        # 基础用户统计
        user_query = """
        SELECT 
            COUNT(*) as total_users,
            COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_users,
            COUNT(CASE WHEN DATE(created_at) = DATE('now') THEN 1 END) as new_users_today,
            COUNT(CASE WHEN created_at >= datetime('now', '-7 days') THEN 1 END) as new_users_this_week,
            COUNT(CASE WHEN created_at >= datetime('now', '-30 days') THEN 1 END) as new_users_this_month
        FROM users
        """
        if start_date:
            user_query += f" WHERE created_at >= '{start_date}'"
        
        user_result = self.db.execute_query(user_query)
        user_data = dict(user_result[0]) if user_result else {}
        
        # 按角色分布
        role_query = """
        SELECT r.name, COUNT(ur.user_id) as count
        FROM roles r
        LEFT JOIN user_roles ur ON r.id = ur.role_id
        GROUP BY r.id, r.name
        ORDER BY count DESC
        """
        role_result = self.db.execute_query(role_query)
        user_distribution_by_role = {row['name']: row['count'] for row in role_result}
        
        # 登录统计
        login_query = """
        SELECT 
            COUNT(CASE WHEN last_login >= datetime('now', '-24 hours') THEN 1 END) as logins_today,
            COUNT(CASE WHEN last_login >= datetime('now', '-7 days') THEN 1 END) as logins_this_week,
            COUNT(CASE WHEN login_count > 0 THEN 1 END) as users_with_logins
        FROM users
        WHERE is_active = 1
        """
        login_result = self.db.execute_query(login_query)
        login_stats = dict(login_result[0]) if login_result else {}
        
        return UserStats(
            total_users=user_data.get('total_users', 0),
            active_users=user_data.get('active_users', 0),
            new_users_today=user_data.get('new_users_today', 0),
            new_users_this_week=user_data.get('new_users_this_week', 0),
            new_users_this_month=user_data.get('new_users_this_month', 0),
            user_distribution_by_role=user_distribution_by_role,
            login_stats=login_stats
        )
    
    def get_analysis_stats(self, time_range: TimeRange = TimeRange.ALL) -> AnalysisStats:
        """获取分析任务统计"""
        start_date = self._get_start_date(time_range)
        
        # 基础任务统计
        task_query = """
        SELECT 
            COUNT(*) as total_tasks,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
            COUNT(CASE WHEN status = 'running' THEN 1 END) as running_tasks,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
            AVG(CASE 
                WHEN status = 'completed' AND started_at IS NOT NULL AND completed_at IS NOT NULL 
                THEN (julianday(completed_at) - julianday(started_at)) * 24 * 3600 
            END) as avg_execution_time
        FROM user_analysis_tasks
        """
        params = []
        if start_date:
            task_query += " WHERE created_at >= ?"
            params.append(start_date)
        
        task_result = self.db.execute_query(task_query, params)
        task_data = dict(task_result[0]) if task_result else {}
        
        # 计算成功率
        total = task_data.get('total_tasks', 0)
        completed = task_data.get('completed_tasks', 0)
        success_rate = (completed / total * 100) if total > 0 else 0
        
        # 按日期统计任务
        date_query = """
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM user_analysis_tasks
        """
        if start_date:
            date_query += " WHERE created_at >= ?"
        date_query += " GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 30"
        
        date_result = self.db.execute_query(date_query, params)
        tasks_by_date = [{"date": row['date'], "count": row['count']} for row in date_result]
        
        # 热门股票
        stock_query = """
        SELECT ticker, COUNT(*) as count
        FROM user_analysis_tasks
        """
        if start_date:
            stock_query += " WHERE created_at >= ?"
        stock_query += " GROUP BY ticker ORDER BY count DESC LIMIT 10"
        
        stock_result = self.db.execute_query(stock_query, params)
        popular_stocks = [{"ticker": row['ticker'], "count": row['count']} for row in stock_result]
        
        # 按用户统计
        user_query = """
        SELECT u.username, COUNT(t.id) as count
        FROM users u
        LEFT JOIN user_analysis_tasks t ON u.id = t.user_id
        """
        if start_date:
            user_query += " WHERE t.created_at >= ? OR t.created_at IS NULL"
        user_query += " GROUP BY u.id, u.username ORDER BY count DESC LIMIT 10"
        
        user_result = self.db.execute_query(user_query, params)
        tasks_by_user = [{"username": row['username'], "count": row['count']} for row in user_result]
        
        return AnalysisStats(
            total_tasks=task_data.get('total_tasks', 0),
            completed_tasks=task_data.get('completed_tasks', 0),
            running_tasks=task_data.get('running_tasks', 0),
            failed_tasks=task_data.get('failed_tasks', 0),
            success_rate=success_rate,
            avg_execution_time=task_data.get('avg_execution_time'),
            tasks_by_date=tasks_by_date,
            popular_stocks=popular_stocks,
            tasks_by_user=tasks_by_user
        )
    
    def get_portfolio_stats(self, time_range: TimeRange = TimeRange.ALL) -> PortfolioStats:
        """获取投资组合统计"""
        start_date = self._get_start_date(time_range)
        
        # 基础组合统计
        portfolio_query = """
        SELECT 
            COUNT(*) as total_portfolios,
            COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_portfolios,
            SUM(initial_capital) as total_capital,
            SUM(COALESCE(current_value, initial_capital)) as total_market_value
        FROM user_portfolios
        """
        params = []
        if start_date:
            portfolio_query += " WHERE created_at >= ?"
            params.append(start_date)
        
        portfolio_result = self.db.execute_query(portfolio_query, params)
        portfolio_data = dict(portfolio_result[0]) if portfolio_result else {}
        
        # 计算总收益
        total_capital = portfolio_data.get('total_capital', 0) or 0
        total_market_value = portfolio_data.get('total_market_value', 0) or 0
        total_return = total_market_value - total_capital
        avg_return_rate = (total_return / total_capital * 100) if total_capital > 0 else 0
        
        # 表现最好的组合
        top_query = """
        SELECT 
            p.name, 
            p.initial_capital,
            COALESCE(p.current_value, p.initial_capital) as current_value,
            (COALESCE(p.current_value, p.initial_capital) - p.initial_capital) as return_amount,
            ((COALESCE(p.current_value, p.initial_capital) - p.initial_capital) / p.initial_capital * 100) as return_rate,
            u.username
        FROM user_portfolios p
        JOIN users u ON p.user_id = u.id
        WHERE p.is_active = 1 AND p.initial_capital > 0
        """
        if start_date:
            top_query += " AND p.created_at >= ?"
        top_query += " ORDER BY return_rate DESC LIMIT 10"
        
        top_result = self.db.execute_query(top_query, params)
        top_performing_portfolios = [dict(row) for row in top_result]
        
        # 组合分布
        dist_query = """
        SELECT 
            CASE 
                WHEN initial_capital < 50000 THEN '小额(<5万)'
                WHEN initial_capital < 100000 THEN '中额(5-10万)'
                WHEN initial_capital < 500000 THEN '大额(10-50万)'
                ELSE '巨额(>=50万)'
            END as category,
            COUNT(*) as count
        FROM user_portfolios
        WHERE is_active = 1
        """
        if start_date:
            dist_query += " AND created_at >= ?"
        dist_query += " GROUP BY category"
        
        dist_result = self.db.execute_query(dist_query, params)
        portfolio_distribution = {row['category']: row['count'] for row in dist_result}
        
        # 持仓分布
        holdings_query = """
        SELECT h.ticker, COUNT(*) as portfolio_count, SUM(h.quantity) as total_quantity
        FROM user_holdings h
        JOIN user_portfolios p ON h.portfolio_id = p.id
        WHERE p.is_active = 1
        """
        if start_date:
            holdings_query += " AND p.created_at >= ?"
        holdings_query += " GROUP BY h.ticker ORDER BY portfolio_count DESC LIMIT 20"
        
        holdings_result = self.db.execute_query(holdings_query, params)
        holdings_distribution = [
            {"ticker": row['ticker'], "portfolio_count": row['portfolio_count'], "total_quantity": row['total_quantity']}
            for row in holdings_result
        ]
        
        return PortfolioStats(
            total_portfolios=portfolio_data.get('total_portfolios', 0),
            active_portfolios=portfolio_data.get('active_portfolios', 0),
            total_capital=total_capital,
            total_market_value=total_market_value,
            total_return=total_return,
            avg_return_rate=avg_return_rate,
            top_performing_portfolios=top_performing_portfolios,
            portfolio_distribution=portfolio_distribution,
            holdings_distribution=holdings_distribution
        )
    
    def get_system_stats(self) -> SystemStats:
        """获取系统统计"""
        import psutil
        import os
        
        # 系统运行时间（简化实现）
        uptime = "N/A"
        
        # 配置数量
        config_query = "SELECT COUNT(*) as count FROM system_config"
        config_result = self.db.execute_query(config_query)
        total_configs = config_result[0]['count'] if config_result else 0
        
        # 数据库大小
        try:
            db_size = os.path.getsize(self.db.db_path)
            database_size = f"{db_size / 1024 / 1024:.2f} MB"
        except:
            database_size = "N/A"
        
        # 系统资源使用（如果可用）
        memory_usage = None
        cpu_usage = None
        try:
            memory_usage = f"{psutil.virtual_memory().percent}%"
            cpu_usage = psutil.cpu_percent()
        except:
            pass
        
        # 活跃会话数（简化实现，基于最近登录用户）
        session_query = """
        SELECT COUNT(*) as count 
        FROM users 
        WHERE last_login >= datetime('now', '-1 hour') AND is_active = 1
        """
        session_result = self.db.execute_query(session_query)
        active_sessions = session_result[0]['count'] if session_result else 0
        
        # 错误率和响应时间（基于API统计）
        api_query = """
        SELECT 
            COUNT(*) as total_calls,
            COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_calls,
            AVG(response_time) as avg_response_time
        FROM api_usage_stats
        WHERE created_at >= datetime('now', '-24 hours')
        """
        api_result = self.db.execute_query(api_query)
        api_data = dict(api_result[0]) if api_result else {}
        
        total_calls = api_data.get('total_calls', 0)
        error_calls = api_data.get('error_calls', 0)
        error_rate = (error_calls / total_calls * 100) if total_calls > 0 else 0
        response_time_avg = api_data.get('avg_response_time', 0) or 0
        
        return SystemStats(
            uptime=uptime,
            total_configs=total_configs,
            database_size=database_size,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            active_sessions=active_sessions,
            error_rate=error_rate,
            response_time_avg=response_time_avg
        )
    
    def get_api_stats(self, time_range: TimeRange = TimeRange.ALL) -> APIStats:
        """获取API调用统计"""
        start_date = self._get_start_date(time_range)
        
        # 基础API统计
        api_query = """
        SELECT 
            COUNT(*) as total_calls,
            COUNT(CASE WHEN DATE(created_at) = DATE('now') THEN 1 END) as calls_today,
            COUNT(CASE WHEN status_code < 400 THEN 1 END) as success_calls,
            AVG(response_time) as avg_response_time
        FROM api_usage_stats
        """
        params = []
        if start_date:
            api_query += " WHERE created_at >= ?"
            params.append(start_date)
        
        api_result = self.db.execute_query(api_query, params)
        api_data = dict(api_result[0]) if api_result else {}
        
        total_calls = api_data.get('total_calls', 0)
        success_calls = api_data.get('success_calls', 0)
        success_rate = (success_calls / total_calls * 100) if total_calls > 0 else 0
        
        # 按端点统计
        endpoint_query = """
        SELECT endpoint, COUNT(*) as count
        FROM api_usage_stats
        """
        if start_date:
            endpoint_query += " WHERE created_at >= ?"
        endpoint_query += " GROUP BY endpoint ORDER BY count DESC LIMIT 20"
        
        endpoint_result = self.db.execute_query(endpoint_query, params)
        calls_by_endpoint = [{"endpoint": row['endpoint'], "count": row['count']} for row in endpoint_result]
        
        # 按用户统计
        user_query = """
        SELECT u.username, COUNT(a.id) as count
        FROM users u
        LEFT JOIN api_usage_stats a ON u.id = a.user_id
        """
        if start_date:
            user_query += " WHERE a.created_at >= ? OR a.created_at IS NULL"
        user_query += " GROUP BY u.id, u.username ORDER BY count DESC LIMIT 10"
        
        user_result = self.db.execute_query(user_query, params)
        calls_by_user = [{"username": row['username'], "count": row['count']} for row in user_result]
        
        # 错误分布
        error_query = """
        SELECT 
            CASE 
                WHEN status_code < 400 THEN 'Success (2xx-3xx)'
                WHEN status_code < 500 THEN 'Client Error (4xx)'
                ELSE 'Server Error (5xx)'
            END as category,
            COUNT(*) as count
        FROM api_usage_stats
        """
        if start_date:
            error_query += " WHERE created_at >= ?"
        error_query += " GROUP BY category"
        
        error_result = self.db.execute_query(error_query, params)
        error_distribution = {row['category']: row['count'] for row in error_result}
        
        # 按小时分布
        hourly_query = """
        SELECT 
            CAST(strftime('%H', created_at) AS INTEGER) as hour,
            COUNT(*) as count
        FROM api_usage_stats
        """
        if start_date:
            hourly_query += " WHERE created_at >= ?"
        hourly_query += " GROUP BY hour ORDER BY hour"
        
        hourly_result = self.db.execute_query(hourly_query, params)
        hourly_distribution = [{"hour": row['hour'], "count": row['count']} for row in hourly_result]
        
        return APIStats(
            total_calls=total_calls,
            calls_today=api_data.get('calls_today', 0),
            success_rate=success_rate,
            avg_response_time=api_data.get('avg_response_time', 0) or 0,
            calls_by_endpoint=calls_by_endpoint,
            calls_by_user=calls_by_user,
            error_distribution=error_distribution,
            hourly_distribution=hourly_distribution
        )
    
    def get_overall_stats(self, time_range: TimeRange = TimeRange.ALL) -> OverallStats:
        """获取总体统计"""
        return OverallStats(
            user_stats=self.get_user_stats(time_range),
            analysis_stats=self.get_analysis_stats(time_range),
            portfolio_stats=self.get_portfolio_stats(time_range),
            system_stats=self.get_system_stats(),
            api_stats=self.get_api_stats(time_range),
            generated_at=datetime.now()
        )
    
    def _get_start_date(self, time_range: TimeRange) -> Optional[str]:
        """根据时间范围获取开始日期"""
        if time_range == TimeRange.ALL:
            return None
        
        now = datetime.now()
        if time_range == TimeRange.DAY_1:
            start = now - timedelta(days=1)
        elif time_range == TimeRange.WEEK_1:
            start = now - timedelta(weeks=1)
        elif time_range == TimeRange.MONTH_1:
            start = now - timedelta(days=30)
        elif time_range == TimeRange.MONTH_3:
            start = now - timedelta(days=90)
        elif time_range == TimeRange.MONTH_6:
            start = now - timedelta(days=180)
        elif time_range == TimeRange.YEAR_1:
            start = now - timedelta(days=365)
        else:
            return None
        
        return start.isoformat()
    
    def generate_report(self, stats_type: StatsType, time_range: TimeRange = TimeRange.ALL, 
                       format_type: str = "json") -> Dict[str, Any]:
        """生成统计报告"""
        report_data = {
            "report_type": stats_type.value,
            "time_range": time_range.value,
            "generated_at": datetime.now().isoformat(),
            "data": None
        }
        
        if stats_type == StatsType.USER:
            report_data["data"] = self.get_user_stats(time_range).dict()
        elif stats_type == StatsType.ANALYSIS:
            report_data["data"] = self.get_analysis_stats(time_range).dict()
        elif stats_type == StatsType.PORTFOLIO:
            report_data["data"] = self.get_portfolio_stats(time_range).dict()
        elif stats_type == StatsType.SYSTEM:
            report_data["data"] = self.get_system_stats().dict()
        elif stats_type == StatsType.API:
            report_data["data"] = self.get_api_stats(time_range).dict()
        
        return report_data