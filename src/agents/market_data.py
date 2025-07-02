from langchain_core.messages import HumanMessage
from src.tools.openrouter_config import get_chat_completion
from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from src.tools.api import get_financial_metrics, get_financial_statements, get_market_data, get_price_history, calculate_comprehensive_financial_metrics
from src.utils.logging_config import setup_logger
from src.utils.api_utils import agent_endpoint, log_llm_interaction

from datetime import datetime, timedelta
import pandas as pd
import json

# 设置日志记录
logger = setup_logger('market_data_agent')


@agent_endpoint("market_data", "市场数据收集，负责获取股价历史、财务指标和市场信息")
def market_data_agent(state: AgentState):
    """Responsible for gathering and preprocessing market data"""
    show_workflow_status("Market Data Agent")
    show_reasoning = state["metadata"]["show_reasoning"]

    messages = state["messages"]
    data = state["data"]

    # Set default dates
    current_date = datetime.now()
    yesterday = current_date - timedelta(days=1)
    end_date = data.get("end_date") or yesterday.strftime('%Y-%m-%d')

    # Ensure end_date is not in the future
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    if end_date_obj > yesterday:
        end_date = yesterday.strftime('%Y-%m-%d')
        end_date_obj = yesterday

    if not data.get("start_date"):
        # Calculate 1 year before end_date
        start_date = end_date_obj - timedelta(days=365)  # 默认获取一年的数据
        start_date = start_date.strftime('%Y-%m-%d')
    else:
        start_date = data["start_date"]

    # Get all required data
    ticker = data.get("ticker") or data.get("stock_symbol")

    # 获取价格数据并验证
    prices_df = get_price_history(ticker, start_date, end_date)
    if prices_df is None or prices_df.empty:
        logger.warning(f"警告：无法获取{ticker}的价格数据，将使用空数据继续")
        prices_df = pd.DataFrame(
            columns=['close', 'open', 'high', 'low', 'volume'])

    # 获取财务指标
    try:
        financial_metrics = get_financial_metrics(ticker)
    except Exception as e:
        logger.error(f"获取财务指标失败: {str(e)}")
        financial_metrics = [{}]

    # 获取财务报表
    try:
        financial_line_items = get_financial_statements(ticker)
    except Exception as e:
        logger.error(f"获取财务报表失败: {str(e)}")
        financial_line_items = [{}]

    # 获取市场数据
    try:
        market_data = get_market_data(ticker)
    except Exception as e:
        logger.error(f"获取市场数据失败: {str(e)}")
        market_data = {"market_cap": 0}

    # 使用增强的财务指标计算，从多个数据源补充缺失的指标
    try:
        logger.info("Computing comprehensive financial metrics from all available data sources...")
        enhanced_metrics = calculate_comprehensive_financial_metrics(
            symbol=ticker,
            financial_statements=financial_line_items,
            financial_indicators=financial_metrics,
            market_data=market_data
        )
        
        # 如果增强计算得到了更多指标，则更新financial_metrics
        if enhanced_metrics:
            # 保持原有的格式，但用增强的数据更新
            if financial_metrics and len(financial_metrics) > 0:
                financial_metrics[0].update(enhanced_metrics)
            else:
                financial_metrics = [enhanced_metrics]
            logger.info("✓ Financial metrics enhanced with calculated ratios")
        
    except Exception as e:
        logger.error(f"增强财务指标计算失败: {str(e)}")
        # 继续使用原有数据，不因增强计算失败而中断整个流程

    # 确保数据格式正确
    if not isinstance(prices_df, pd.DataFrame):
        prices_df = pd.DataFrame(
            columns=['close', 'open', 'high', 'low', 'volume'])

    # 转换价格数据为字典格式
    prices_dict = prices_df.to_dict('records')

    # 保存推理信息到metadata供API使用
    market_data_summary = {
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "data_collected": {
            "price_history": len(prices_dict) > 0,
            "financial_metrics": len(financial_metrics) > 0,
            "financial_statements": len(financial_line_items) > 0,
            "market_data": len(market_data) > 0
        },
        "summary": f"为{ticker}收集了从{start_date}到{end_date}的市场数据，包括价格历史、财务指标和市场信息"
    }

    if show_reasoning:
        show_agent_reasoning(market_data_summary, "Market Data Agent")
        state["metadata"]["agent_reasoning"] = market_data_summary

    # 创建消息
    message = HumanMessage(
        content=json.dumps(market_data_summary, ensure_ascii=False),
        name="market_data_agent",
    )

    return {
        "messages": [message],
        "data": {
            **data,
            "prices": prices_dict,
            "start_date": start_date,
            "end_date": end_date,
            "financial_metrics": financial_metrics,
            "financial_line_items": financial_line_items,
            "market_cap": market_data.get("market_cap", 0),
            "market_data": market_data,
        },
        "metadata": state["metadata"],
    }
