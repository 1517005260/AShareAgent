from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import sys
import os
import logging

from backend.middleware import add_stats_middleware
from backend.middleware.dual_logging_middleware import setup_dual_logging_middleware

from backend.routers import logs, runs
# 导入新增的路由器
from backend.routers import agents, workflow, analysis, api_runs, auth, portfolio, config, stats, monitor, backtest, stock

# 添加项目根目录到Python路径，确保可以导入初始化脚本
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# Create FastAPI app instance
app = FastAPI(
    title="A Share Investment Agent - Backend",
    description="API for monitoring LLM interactions within the agent workflow.",
    version="0.1.0"
)

# 初始化双写日志系统
from src.utils.dual_logger import get_dual_logger, logger_manager
from src.database.models import DatabaseManager

# 初始化数据库和日志系统
try:
    db_manager = DatabaseManager()
    logger_manager.set_database_manager(db_manager)
    logger = get_dual_logger('backend')
    logger.info("后端服务启动，双写日志系统已初始化")
except Exception as e:
    # 如果双写日志初始化失败，回退到标准日志
    logger = logging.getLogger(__name__)
    logger.warning(f"双写日志系统初始化失败，使用标准日志: {e}")


@app.on_event("startup")
async def startup_event():
    """Backend startup event - initialize agents in database"""
    try:
        logger.info("后端服务启动事件 - 开始初始化代理")
        
        # 导入并运行agent初始化脚本
        from scripts.init_system import init_agents
        init_agents()
        
        logger.info("代理初始化成功完成")
    except Exception as e:
        logger.error(f"代理初始化失败: {e}")
        # 不要阻止服务启动，只是记录错误

# Configure CORS (Cross-Origin Resource Sharing)
# Allows requests from any origin in this example.
# Adjust origins as needed for production environments.
origins = ["*"]  # Allow all origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# 添加双写日志中间件
setup_dual_logging_middleware(app)

# 添加API统计中间件
add_stats_middleware(app)

# 添加静态文件服务 - 用于服务生成的图表
plots_dir = os.path.join(project_root, "plots")
if os.path.exists(plots_dir):
    app.mount("/plots", StaticFiles(directory=plots_dir), name="plots")
    logger.info(f"静态文件服务已配置: /plots -> {plots_dir}")
else:
    logger.warning(f"Plots目录不存在，跳过静态文件配置: {plots_dir}")

# 包含现有路由器
app.include_router(logs.router)
app.include_router(runs.router)

# 包含新增的路由器
app.include_router(auth.router)
app.include_router(config.router)
app.include_router(stats.router)
app.include_router(portfolio.router)
app.include_router(monitor.router)
app.include_router(agents.router)
app.include_router(workflow.router)
app.include_router(analysis.router)
app.include_router(backtest.router)
app.include_router(api_runs.router)
app.include_router(stock.router, prefix="/api/stock", tags=["股票价格"])

# 根端点API导航


@app.get("/")
def read_root():
    return {
        "message": "欢迎使用A股投资Agent后端API! 访问 /docs 了解详情。",
        "api_navigation": {
            "文档": "/docs",
            "新API": {
                "介绍": "采用标准化的ApiResponse格式的新API",
                "端点": {
                    "认证": "/api/auth/",
                    "系统配置": "/api/config/",
                    "数据统计": "/api/stats/",
                    "投资组合": "/api/portfolios/",
                    "系统监控": "/api/monitor/",
                    "代理": "/api/agents/",
                    "分析": "/api/analysis/",
                    "回测": "/api/backtest/",
                    "运行": "/api/runs/",
                    "工作流": "/api/workflow/"
                }
            },
            "旧API": {
                "介绍": "为向后兼容保留的原有API",
                "端点": {
                    "日志": "/logs/",
                    "运行": "/runs/"
                }
            }
        }
    }


@app.get("/api")
def api_navigation():
    """提供API导航信息"""
    return {
        "message": "A股投资Agent API导航",
        "api_sections": {
            "/api/auth": "用户认证和权限管理",
            "/api/config": "系统配置和参数管理",
            "/api/stats": "数据统计和报表功能",
            "/api/portfolios": "投资组合管理和交易记录",
            "/api/monitor": "系统监控和日志管理",
            "/api/agents": "获取各个Agent的状态和数据",
            "/api/analysis": "启动和查询股票分析任务",
            "/api/backtest": "启动和查询回测任务",
            "/api/runs": "查询运行历史和状态(基于api_state)",
            "/api/workflow": "获取当前工作流状态"
        },
        "legacy_api": {
            "/logs": "查询历史LLM交互日志",
            "/runs": "详细查询运行历史和Agent执行数据(基于BaseLogStorage)"
        },
        "documentation": {
            "OpenAPI文档": "/docs",
            "ReDoc文档": "/redoc"
        }
    }
