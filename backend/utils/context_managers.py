"""
上下文管理器模块

提供各种API相关的上下文管理器
"""

from contextlib import contextmanager
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from ..state import api_state

logger = logging.getLogger("context_managers")

# 导入数据库模型
try:
    from src.database.models import DatabaseManager, AgentDecisionModel, AnalysisResultModel
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False
    logger.warning("数据库模型导入失败，将不保存到数据库")


@contextmanager
def workflow_run(run_id: str):
    """
    工作流运行上下文管理器

    用法:
    with workflow_run(run_id):
        # 执行工作流
    """
    api_state.register_run(run_id)
    
    # 初始化数据库连接
    db_manager = None
    decision_model = None
    analysis_model = None
    
    if HAS_DATABASE:
        try:
            db_manager = DatabaseManager()
            decision_model = AgentDecisionModel(db_manager)
            analysis_model = AnalysisResultModel(db_manager)
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
    
    try:
        yield
        api_state.complete_run(run_id, "completed")
        
        # 在工作流完成时保存数据到数据库
        if HAS_DATABASE and decision_model and analysis_model:
            _save_run_data_to_database(run_id, decision_model, analysis_model)
            
    except Exception as e:
        api_state.complete_run(run_id, "error")
        raise


def _save_run_data_to_database(run_id: str, decision_model, analysis_model):
    """将运行数据保存到数据库"""
    try:
        # 获取运行信息
        run_info = api_state.get_run(run_id)
        if not run_info:
            logger.warning(f"未找到运行信息: {run_id}")
            return
        
        # 统计保存的记录数
        saved_decisions = 0
        saved_analyses = 0
        
        # 遍历所有agent的历史记录，合并同一个agent在同一次运行中的数据
        for agent_name in api_state._agent_data:
            agent_data = api_state._agent_data[agent_name]
            
            # 收集该agent在此次运行的所有数据
            run_entries = [entry for entry in agent_data["history"] if entry.get("run_id") == run_id]
            
            if not run_entries:
                continue
            
            # 合并同一运行的数据
            merged_entry = {"run_id": run_id, "agent_name": agent_name}
            latest_timestamp = None
            
            for entry in run_entries:
                if entry.get("timestamp"):
                    if not latest_timestamp or entry["timestamp"] > latest_timestamp:
                        latest_timestamp = entry["timestamp"]
                        
                # 合并所有字段
                for key, value in entry.items():
                    if key not in ["run_id", "timestamp"] and value is not None:
                        merged_entry[key] = value
            
            merged_entry["timestamp"] = latest_timestamp
            
            # 从input_state或latest数据中提取ticker
            ticker = "UNKNOWN"
            if "input_state" in merged_entry:
                input_state = merged_entry["input_state"]
                if isinstance(input_state, dict) and "data" in input_state:
                    ticker = input_state["data"].get("ticker", "UNKNOWN")
            
            # 如果没有从input_state找到，尝试从最新数据中获取
            if ticker == "UNKNOWN":
                latest_data = agent_data.get("latest", {})
                if "input_state" in latest_data and isinstance(latest_data["input_state"], dict):
                    data_section = latest_data["input_state"].get("data", {})
                    ticker = data_section.get("ticker", "UNKNOWN")
            
            # 保存决策记录 - 只有当有输出状态时才保存
            if "output_state" in merged_entry and merged_entry["output_state"]:
                output_state = merged_entry["output_state"]
                decision_data = {
                    "agent_output": output_state,
                    "timestamp": merged_entry["timestamp"].isoformat() if merged_entry.get("timestamp") else None,
                    "input_state": merged_entry.get("input_state"),
                    "llm_request": merged_entry.get("llm_request"),
                    "llm_response": merged_entry.get("llm_response"),
                }
                
                # 提取决策类型和置信度
                decision_type = "analysis"
                confidence_score = None
                reasoning = None
                
                # 尝试从推理数据中提取置信度
                if "reasoning" in merged_entry and isinstance(merged_entry["reasoning"], dict):
                    reasoning_data = merged_entry["reasoning"]
                    confidence_score = reasoning_data.get("confidence")
                    reasoning = str(reasoning_data)[:1000]
                
                # 如果output_state包含messages，尝试解析
                if isinstance(output_state, dict) and "messages" in output_state and output_state["messages"]:
                    last_message = output_state["messages"][-1]
                    if isinstance(last_message, dict) and "content" in last_message:
                        content = last_message["content"]
                        if not reasoning:  # 只有当reasoning为空时才使用message content
                            reasoning = content[:1000] if isinstance(content, str) else str(content)[:1000]
                
                # 保存决策记录
                success = decision_model.save_decision(
                    run_id=run_id,
                    agent_name=agent_name,
                    ticker=ticker,
                    decision_type=decision_type,
                    decision_data=decision_data,
                    confidence_score=confidence_score,
                    reasoning=reasoning
                )
                if success:
                    saved_decisions += 1
                    logger.debug(f"保存决策记录: {agent_name} for {ticker}")
            
            # 保存分析结果 - 只有当有推理数据时才保存
            if "reasoning" in merged_entry and merged_entry["reasoning"]:
                reasoning_data = merged_entry["reasoning"]
                result_data = {
                    "reasoning": reasoning_data,
                    "timestamp": merged_entry["timestamp"].isoformat() if merged_entry.get("timestamp") else None,
                    "output_state": merged_entry.get("output_state"),
                    "llm_interaction": {
                        "request": merged_entry.get("llm_request"),
                        "response": merged_entry.get("llm_response")
                    }
                }
                
                # 提取执行时间和置信度
                confidence_score = None
                execution_time = None
                if isinstance(reasoning_data, dict):
                    confidence_score = reasoning_data.get("confidence")
                
                success = analysis_model.save_result(
                    run_id=run_id,
                    agent_name=agent_name,
                    ticker=ticker,
                    analysis_date=merged_entry["timestamp"].strftime('%Y-%m-%d') if merged_entry.get("timestamp") else None,
                    analysis_type=agent_name.replace("_agent", "").replace("_", " "),
                    result_data=result_data,
                    confidence_score=confidence_score,
                    execution_time=execution_time
                )
                if success:
                    saved_analyses += 1
                    logger.debug(f"保存分析结果: {agent_name} for {ticker}")
        
        logger.info(f"成功保存运行数据到数据库: {run_id}, 决策记录: {saved_decisions}, 分析结果: {saved_analyses}")
        
    except Exception as e:
        logger.error(f"保存运行数据到数据库失败: {e}")
        import traceback
        traceback.print_exc()
