from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from backend.schemas import LLMInteractionLog
from backend.storage.base import BaseLogStorage
from backend.dependencies import get_log_storage

router = APIRouter(
    prefix="/logs",
    tags=["LLM Interaction Logs"]  # Tag for Swagger UI grouping
)


@router.get("/", response_model=List[LLMInteractionLog])
def read_logs(
    agent_name: Optional[str] = Query(
        None, description="Filter logs by agent name"),
    run_id: Optional[str] = Query(None, description="Filter logs by run ID"),
    # Default limit 50, non-negative
    limit: Optional[int] = Query(
        50, description="Maximum number of logs to return (most recent)", ge=0),
    storage: BaseLogStorage = Depends(get_log_storage)
):
    """Retrieve LLM interaction logs, with optional filtering and limit."""
    try:
        logs = storage.get_logs(agent_name=agent_name,
                                run_id=run_id, limit=limit)
        return logs
    except Exception as e:
        # Basic error handling
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve logs: {str(e)}")
