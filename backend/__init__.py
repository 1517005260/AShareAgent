"""
A股投资Agent后端包

提供API服务、状态管理和数据模型等后端功能
"""

from .state import api_state
from .models import ApiResponse, AgentInfo, RunInfo, StockAnalysisRequest, StockAnalysisResponse
from .utils import serialize_for_api, safe_parse_json, workflow_run
from .services import execute_stock_analysis
from .main import app 