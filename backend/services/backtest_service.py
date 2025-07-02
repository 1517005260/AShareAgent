"""
回测业务逻辑服务模块

此模块提供回测相关的业务逻辑，包括回测任务的执行、结果处理等
"""

import uuid
import json
import logging
from datetime import datetime, UTC
from typing import Dict, Any, Optional
from concurrent.futures import Future

from backend.models.api_models import BacktestRequest, BacktestResponse, BacktestResultData
from backend.models.auth_models import UserInDB
from backend.state import api_state
from backend.utils.api_utils import serialize_for_api
from src.database.models import DatabaseManager
from src.backtesting.backtester import IntelligentBacktester

logger = logging.getLogger("backtest_service")


def execute_backtest_with_user(request: BacktestRequest, run_id: str, user_id: int, db_manager: DatabaseManager) -> Dict[str, Any]:
    """执行回测任务，支持用户关联和数据库记录"""
    try:
        logger.info(f"开始执行回测任务 {run_id} for user {user_id}")
        
        # 动态导入agent函数以避免循环导入
        import importlib.util
        import sys
        
        # 加载src.main模块
        spec = importlib.util.spec_from_file_location("src.main", "/home/glk/project/AShareAgent/src/main.py")
        main_module = importlib.util.module_from_spec(spec)
        sys.modules["src.main"] = main_module
        spec.loader.exec_module(main_module)
        
        run_hedge_fund = main_module.run_hedge_fund
        
        # 设置默认的Agent频率配置
        default_frequencies = {
            'market_data': 'daily',
            'technical': 'daily', 
            'fundamentals': 'weekly',
            'sentiment': 'daily',
            'valuation': 'monthly',
            'macro': 'weekly',
            'portfolio': 'daily'
        }
        
        # 使用用户提供的频率配置或默认配置
        agent_frequencies = request.agent_frequencies or default_frequencies
        
        # 创建回测器实例
        backtester = IntelligentBacktester(
            agent=run_hedge_fund,
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            num_of_news=request.num_of_news,
            agent_frequencies=agent_frequencies
        )
        
        # 执行回测
        logger.info(f"开始运行回测: {request.ticker} ({request.start_date} to {request.end_date})")
        backtester.run_backtest()
        
        # 分析性能
        logger.info("开始分析回测性能")
        performance_df = backtester.analyze_performance(save_plots=False)
        
        # 获取回测结果
        result_data = {
            "performance_metrics": {
                "total_return": backtester.total_return if hasattr(backtester, 'total_return') else None,
                "annualized_return": backtester.annualized_return if hasattr(backtester, 'annualized_return') else None,
                "sharpe_ratio": backtester.sharpe_ratio if hasattr(backtester, 'sharpe_ratio') else None,
                "max_drawdown": backtester.max_drawdown if hasattr(backtester, 'max_drawdown') else None,
                "volatility": backtester.volatility if hasattr(backtester, 'volatility') else None,
            },
            "risk_metrics": {
                "var_95": backtester.var_95 if hasattr(backtester, 'var_95') else None,
                "expected_shortfall": backtester.expected_shortfall if hasattr(backtester, 'expected_shortfall') else None,
                "beta": backtester.beta if hasattr(backtester, 'beta') else None,
                "alpha": backtester.alpha if hasattr(backtester, 'alpha') else None,
            },
            "trades": [trade.to_dict() for trade in backtester.trades] if hasattr(backtester, 'trades') else [],
            "portfolio_values": {
                "dates": [str(date) for date in backtester.portfolio_values.index] if hasattr(backtester, 'portfolio_values') else [],
                "values": backtester.portfolio_values.tolist() if hasattr(backtester, 'portfolio_values') else []
            },
            "benchmark_comparison": backtester.benchmark_results if hasattr(backtester, 'benchmark_results') else None
        }
        
        # 更新数据库任务状态为完成
        update_query = """
        UPDATE user_backtest_tasks 
        SET status = ?, completed_at = ?, result = ? 
        WHERE task_id = ?
        """
        result_json = json.dumps(serialize_for_api(result_data))
        
        with db_manager.get_connection() as conn:
            conn.execute(update_query, ("completed", datetime.now(), result_json, run_id))
            conn.commit()
        
        logger.info(f"回测任务 {run_id} 执行完成")
        return result_data
        
    except Exception as e:
        logger.error(f"执行回测任务失败 {run_id}: {e}")
        
        # 更新任务状态为失败
        error_query = """
        UPDATE user_backtest_tasks 
        SET status = ?, completed_at = ?, error_message = ? 
        WHERE task_id = ?
        """
        with db_manager.get_connection() as conn:
            conn.execute(error_query, ("failed", datetime.now(), str(e), run_id))
            conn.commit()
        
        raise e


class BacktestService:
    """回测服务类"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def start_backtest(self, request: BacktestRequest, current_user: UserInDB) -> BacktestResponse:
        """启动回测任务"""
        try:
            # 生成唯一任务ID
            task_id = str(uuid.uuid4())
            
            # 保存任务到数据库
            query = """
            INSERT INTO user_backtest_tasks (user_id, task_id, ticker, start_date, end_date, status, parameters, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            parameters = {
                "initial_capital": request.initial_capital,
                "num_of_news": request.num_of_news,
                "agent_frequencies": request.agent_frequencies
            }
            
            with self.db_manager.get_connection() as conn:
                conn.execute(query, (
                    current_user.id,
                    task_id,
                    request.ticker,
                    request.start_date,
                    request.end_date,
                    "pending",
                    json.dumps(parameters),
                    datetime.now()
                ))
                conn.commit()
            
            # 更新任务状态为运行中
            update_query = "UPDATE user_backtest_tasks SET status = ?, started_at = ? WHERE task_id = ?"
            with self.db_manager.get_connection() as conn:
                conn.execute(update_query, ("running", datetime.now(), task_id))
                conn.commit()
            
            # 将任务提交到线程池
            future = api_state._executor.submit(
                execute_backtest_with_user,
                request=request,
                run_id=task_id,
                user_id=current_user.id,
                db_manager=self.db_manager
            )

            # 注册任务到状态管理器
            api_state.register_backtest_task(task_id, future)
            api_state.register_run(task_id)
            
            # 创建响应对象
            response = BacktestResponse(
                run_id=task_id,
                ticker=request.ticker,
                start_date=request.start_date,
                end_date=request.end_date,
                status="running",
                message="回测任务已启动",
                submitted_at=datetime.now(UTC)
            )
            
            return response
            
        except Exception as e:
            logger.error(f"启动回测任务失败: {e}")
            raise e
    
    async def get_backtest_status(self, run_id: str, current_user: UserInDB) -> Dict[str, Any]:
        """获取回测任务状态"""
        try:
            # 从数据库获取任务信息
            query = """
            SELECT * FROM user_backtest_tasks 
            WHERE task_id = ? AND user_id = ?
            """
            result = self.db_manager.execute_query(query, (run_id, current_user.id))
            
            if not result:
                raise ValueError(f"回测任务 '{run_id}' 不存在或无权限访问")
            
            task_data = dict(result[0])
            
            # 获取内存中的任务状态
            task = api_state.get_backtest_task(run_id)
            
            status_data = {
                "task_id": task_data["task_id"],
                "ticker": task_data["ticker"],
                "start_date": task_data["start_date"],
                "end_date": task_data["end_date"],
                "status": task_data["status"],
                "created_at": task_data["created_at"],
                "started_at": task_data["started_at"],
                "completed_at": task_data["completed_at"],
                "error_message": task_data["error_message"]
            }
            
            # 如果任务还在内存中运行，获取实时状态
            if task and not task.done():
                status_data["is_running"] = True
            elif task and task.done():
                status_data["is_running"] = False
                if task.exception():
                    status_data["runtime_error"] = str(task.exception())
            
            return status_data
            
        except Exception as e:
            logger.error(f"获取回测任务状态失败: {e}")
            raise e
    
    async def get_backtest_result(self, run_id: str, current_user: UserInDB) -> Dict[str, Any]:
        """获取回测任务结果"""
        try:
            # 从数据库获取任务信息，确保用户权限
            query = """
            SELECT * FROM user_backtest_tasks 
            WHERE task_id = ? AND user_id = ?
            """
            result = self.db_manager.execute_query(query, (run_id, current_user.id))
            
            if not result:
                raise ValueError(f"回测任务 '{run_id}' 不存在或无权限访问")
            
            task_data = dict(result[0])
            
            # 检查任务是否完成
            if task_data["status"] != "completed":
                raise ValueError(f"回测任务尚未完成或已失败，当前状态: {task_data['status']}")
            
            # 从数据库获取保存的结果
            if task_data["result"]:
                try:
                    stored_result = json.loads(task_data["result"])
                    return {
                        "task_id": task_data["task_id"],
                        "ticker": task_data["ticker"],
                        "start_date": task_data["start_date"],
                        "end_date": task_data["end_date"],
                        "completion_time": task_data["completed_at"],
                        "result": stored_result
                    }
                except json.JSONDecodeError:
                    logger.error(f"解析存储的回测结果失败: {run_id}")
                    raise ValueError("回测结果数据格式错误")
            
            raise ValueError("回测结果不可用")
            
        except Exception as e:
            logger.error(f"获取回测结果时出错: {str(e)}")
            raise e
    
    async def get_backtest_history(self, current_user: UserInDB, skip: int = 0, limit: int = 20, 
                                   status: str = None, ticker: str = None) -> Dict[str, Any]:
        """获取用户的回测历史记录"""
        try:
            # 构建查询条件
            where_conditions = ["user_id = ?"]
            params = [current_user.id]
            
            if status:
                where_conditions.append("status = ?")
                params.append(status)
            
            if ticker:
                where_conditions.append("ticker = ?")
                params.append(ticker)
            
            where_clause = " AND ".join(where_conditions)
            
            # 获取总数
            count_query = f"SELECT COUNT(*) as total FROM user_backtest_tasks WHERE {where_clause}"
            count_result = self.db_manager.execute_query(count_query, params)
            total = count_result[0]["total"] if count_result else 0
            
            # 获取分页数据
            query = f"""
            SELECT task_id, ticker, start_date, end_date, status, parameters, 
                   created_at, started_at, completed_at, error_message
            FROM user_backtest_tasks 
            WHERE {where_clause}
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
            """
            params.extend([limit, skip])
            
            tasks = self.db_manager.execute_query(query, params)
            
            # 转换参数JSON字符串为对象
            task_list = []
            for task in tasks:
                task_dict = dict(task)
                if task_dict["parameters"]:
                    try:
                        task_dict["parameters"] = json.loads(task_dict["parameters"])
                    except json.JSONDecodeError:
                        task_dict["parameters"] = {}
                task_list.append(task_dict)
            
            return {
                "tasks": task_list,
                "total": total,
                "skip": skip,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"获取回测历史失败: {e}")
            raise e
    
    async def delete_backtest_task(self, task_id: str, current_user: UserInDB) -> bool:
        """删除回测任务记录（仅限已完成或失败的任务）"""
        try:
            # 检查任务是否存在且属于当前用户
            check_query = """
            SELECT status FROM user_backtest_tasks 
            WHERE task_id = ? AND user_id = ?
            """
            result = self.db_manager.execute_query(check_query, (task_id, current_user.id))
            
            if not result:
                raise ValueError("任务不存在或无权限删除")
            
            task_status = result[0]["status"]
            
            # 只允许删除已完成或失败的任务
            if task_status in ["running", "pending"]:
                raise ValueError("无法删除正在运行或待处理的任务")
            
            # 删除任务记录
            delete_query = "DELETE FROM user_backtest_tasks WHERE task_id = ? AND user_id = ?"
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(delete_query, (task_id, current_user.id))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"删除回测任务失败: {e}")
            raise e