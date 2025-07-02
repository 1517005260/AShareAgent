from pydantic import BaseModel, Field
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional


class LLMInteractionLog(BaseModel):
    """Schema for logging LLM interactions."""
    agent_name: str = Field(...,
                            description="The name of the agent initiating the interaction.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Timestamp of the log entry.")
    request_data: Any = Field(..., description="Data sent to the LLM.")
    response_data: Any = Field(..., description="Data received from the LLM.")
    run_id: Optional[str] = Field(
        None, description="Optional identifier for a single workflow run.")

    class Config:
        # Allow arbitrary types for request/response data initially
        # Might need refinement based on actual LLM interaction objects
        arbitrary_types_allowed = True
        from_attributes = True  # For potential ORM integration later


# 以下是新增模型

class AgentExecutionLog(BaseModel):
    """Agent执行日志"""
    agent_name: str = Field(..., description="Agent名称")
    run_id: str = Field(..., description="执行ID")
    timestamp_start: datetime = Field(..., description="开始时间")
    timestamp_end: datetime = Field(..., description="结束时间")
    input_state: Optional[Dict[str, Any]] = Field(None, description="输入状态")
    output_state: Optional[Dict[str, Any]] = Field(None, description="输出状态")
    reasoning_details: Optional[Any] = Field(None, description="推理细节")
    terminal_outputs: List[str] = Field(
        default_factory=list, description="终端输出")


class RunSummary(BaseModel):
    """运行概述信息"""
    run_id: str = Field(..., description="运行ID")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    agents_executed: List[str] = Field(..., description="执行的Agent列表")
    status: str = Field(...,
                        description="运行状态，如completed, in_progress, failed")


class AgentSummary(BaseModel):
    """Agent执行概述"""
    agent_name: str = Field(..., description="Agent名称")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    execution_time_seconds: float = Field(..., description="执行耗时(秒)")
    status: str = Field(..., description="状态，如completed, failed")


class AgentDetail(AgentSummary):
    """Agent执行详情"""
    input_state: Optional[Dict[str, Any]] = Field(None, description="输入状态")
    output_state: Optional[Dict[str, Any]] = Field(None, description="输出状态")
    reasoning: Optional[Dict[str, Any]] = Field(None, description="推理详情")
    llm_interactions: List[str] = Field(
        default_factory=list, description="LLM交互ID列表")


class StateTransition(BaseModel):
    """状态转换信息"""
    from_agent: str = Field(..., description="源Agent")
    to_agent: str = Field(..., description="目标Agent")
    state_size: int = Field(..., description="状态大小估计")
    timestamp: str = Field(..., description="转换时间")


class WorkflowFlow(BaseModel):
    """完整工作流程数据流"""
    run_id: str = Field(..., description="运行ID")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    agents: Dict[str, AgentSummary] = Field(..., description="执行的Agents")
    state_transitions: List[Dict] = Field(..., description="状态转换")
    final_decision: Optional[str] = Field(None, description="最终决策")
