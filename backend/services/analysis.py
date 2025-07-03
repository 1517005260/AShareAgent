"""
股票分析服务模块

提供股票分析相关的后台功能服务
"""

import logging
from typing import Dict, Any
from datetime import datetime, UTC

from ..models.api_models import StockAnalysisRequest
from ..utils.context_managers import workflow_run
from ..state import api_state
from ..schemas import AgentExecutionLog
from ..dependencies import get_log_storage

logger = logging.getLogger("analysis_service")


def _map_agent_name(agent_name: str) -> str:
    """Map internal agent names to frontend expected names"""
    mapping = {
        "technical_analyst_agent": "technical_analyst",
        "fundamentals_agent": "fundamentals", 
        "sentiment_agent": "sentiment",
        "valuation_agent": "valuation",
        "researcher_bull_agent": "researcher_bull",
        "researcher_bear_agent": "researcher_bear",
        "risk_management_agent": "risk_management",
        "portfolio_management_agent": "portfolio_management",
        "market_data_agent": "market_data",
        "macro_analyst_agent": "macro_analyst",
        "macro_news_agent": "macro_news",
        "debate_room_agent": "debate_room"
    }
    return mapping.get(agent_name, agent_name)


def execute_stock_analysis(request: StockAnalysisRequest, run_id: str) -> Dict[str, Any]:
    """执行股票分析任务"""
    from src.main import run_hedge_fund  # 避免循环导入

    try:
        # 获取日志存储器
        log_storage = get_log_storage()

        # 初始化投资组合
        portfolio = {
            "cash": request.initial_capital,
            "stock": request.initial_position
        }

        # 执行分析 - 让系统自动计算日期
        logger.info(f"开始执行股票 {request.ticker} 的分析任务 (运行ID: {run_id})")

        # 创建主工作流日志记录
        workflow_log = AgentExecutionLog(
            agent_name="workflow_manager",
            run_id=run_id,
            timestamp_start=datetime.now(UTC),
            timestamp_end=datetime.now(UTC),  # 初始化为相同值，稍后更新
            input_state={"request": request.dict()},
            output_state=None  # 稍后更新
        )

        # 还不添加到存储，等待工作流完成后再更新

        with workflow_run(run_id):
            # Execute the analysis workflow  
            raw_result = run_hedge_fund(
                run_id=run_id,
                ticker=request.ticker,
                start_date=request.start_date,  # 使用用户指定日期或None(系统默认)
                end_date=request.end_date,      # 使用用户指定日期或None(系统默认)
                portfolio=portfolio,
                show_reasoning=request.show_reasoning,
                num_of_news=request.num_of_news,
                show_summary=request.show_summary
            )

        # Collect agent results from api_state AFTER workflow completes
        agent_results = {}
        run_info = api_state.get_run(run_id)
        
        # Get all available agents from api_state
        all_agents = api_state.get_all_agent_data()
        logger.info(f"Available agents: {list(all_agents.keys())}")
        
        # Get agents that participated in this run
        if run_info and run_info.agents:
            logger.info(f"Agents that participated in run {run_id}: {run_info.agents}")
            
            for agent_name in run_info.agents:
                agent_data = all_agents.get(agent_name)
                if agent_data and "latest" in agent_data and agent_data["latest"].get("reasoning"):
                    try:
                        from ..utils.api_utils import safe_parse_json, serialize_for_api
                        reasoning_data = agent_data["latest"]["reasoning"]
                        
                        # If reasoning_data is a string, try to parse it as JSON
                        if isinstance(reasoning_data, str):
                            reasoning_data = safe_parse_json(reasoning_data)
                        
                        # Map agent names to expected frontend names
                        frontend_name = _map_agent_name(agent_name)
                        agent_results[frontend_name] = serialize_for_api(reasoning_data)
                        logger.info(f"Successfully collected data from agent: {agent_name} -> {frontend_name}")
                    except Exception as e:
                        logger.warning(f"Failed to process agent {agent_name} data: {e}")
        else:
            # Fallback: check all agents if run_info doesn't have agent list
            logger.warning(f"No agent list found in run_info for {run_id}, checking all agents")
            for agent_name, agent_data in all_agents.items():
                if agent_data and "latest" in agent_data and agent_data["latest"].get("reasoning"):
                    # Check if this agent participated in the current run by checking timestamp
                    try:
                        from ..utils.api_utils import safe_parse_json, serialize_for_api
                        reasoning_data = agent_data["latest"]["reasoning"]
                        
                        # If reasoning_data is a string, try to parse it as JSON
                        if isinstance(reasoning_data, str):
                            reasoning_data = safe_parse_json(reasoning_data)
                        
                        # Map agent names to expected frontend names
                        frontend_name = _map_agent_name(agent_name)
                        agent_results[frontend_name] = serialize_for_api(reasoning_data)
                        logger.info(f"Successfully collected data from agent: {agent_name} -> {frontend_name}")
                    except Exception as e:
                        logger.warning(f"Failed to process agent {agent_name} data: {e}")
        
        logger.info(f"Collected agent results: {list(agent_results.keys())}")
        
        # Log detailed agent results for debugging
        for agent_name, result in agent_results.items():
            logger.info(f"Agent {agent_name} result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")

        # Structure the result properly for frontend
        structured_result = {
            "ticker": request.ticker,
            "run_id": run_id,
            "final_decision": raw_result,
            "agent_results": agent_results,
            "completion_time": datetime.now(UTC).isoformat()
        }
        
        logger.info(f"Final structured result keys: {list(structured_result.keys())}")
        logger.info(f"Agent results count: {len(agent_results)}")

        logger.info(f"股票分析任务完成 (运行ID: {run_id})")
        return structured_result
    except Exception as e:
        logger.error(f"股票分析任务失败: {str(e)}")

        # 在出错时也记录日志
        # try:
        #     workflow_log.timestamp_end = datetime.now(UTC)
        #     workflow_log.output_state = {"error": str(e)}
        #     log_storage.add_agent_log(workflow_log)
        # except Exception as log_err:
        #     logger.error(f"记录错误日志时发生异常: {str(log_err)}")

        # 更新运行状态为错误
        api_state.complete_run(run_id, "error")
        raise
