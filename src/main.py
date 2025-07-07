import sys
import argparse
import uuid  # Import uuid for run IDs
import threading  # Import threading for background task
import uvicorn  # Import uvicorn to run FastAPI
from concurrent.futures import ThreadPoolExecutor, TimeoutError as ConcurrentTimeoutError

from datetime import datetime, timedelta
# Removed START as it's implicit with set_entry_point
from langgraph.graph import END, StateGraph
from langchain_core.messages import HumanMessage
import pandas as pd
import akshare as ak

# --- Agent Imports ---
from src.agents.valuation import valuation_agent
from src.agents.state import AgentState
from src.agents.sentiment import sentiment_agent
from src.agents.risk_manager import risk_management_agent
from src.agents.technicals import technical_analyst_agent
from src.agents.portfolio_manager import portfolio_management_agent
from src.agents.market_data import market_data_agent
from src.agents.fundamentals import fundamentals_agent
from src.agents.researcher_bull import researcher_bull_agent
from src.agents.researcher_bear import researcher_bear_agent
from src.agents.debate_room import debate_room_agent
from src.agents.macro_analyst import macro_analyst_agent
from src.agents.macro_news_agent import macro_news_agent

# --- Logging and Backend Imports ---
from src.utils.output_logger import OutputLogger
from src.tools.openrouter_config import get_chat_completion
from src.utils.llm_interaction_logger import (
    log_agent_execution,
    set_global_log_storage
)
from backend.dependencies import get_log_storage
from backend.main import app as fastapi_app
from src.utils.logging_config import setup_logger

# --- Import Summary Report Generator ---
try:
    from src.utils.summary_report import print_summary_report
    from src.utils.agent_collector import store_final_state, get_enhanced_final_state
    HAS_SUMMARY_REPORT = True
except ImportError:
    HAS_SUMMARY_REPORT = False

# --- Import Structured Terminal Output ---
try:
    from src.utils.structured_terminal import print_structured_output
    HAS_STRUCTURED_OUTPUT = True
except ImportError:
    HAS_STRUCTURED_OUTPUT = False

# --- Initialize Logging ---
log_storage = get_log_storage()
set_global_log_storage(log_storage)
sys.stdout = OutputLogger()
logger = setup_logger('main_workflow')

# --- Run the Hedge Fund Workflow ---


def run_hedge_fund(run_id: str, ticker: str, start_date: str, end_date: str, portfolio: dict, show_reasoning: bool = False, num_of_news: int = 5, show_summary: bool = False):
    print(f"--- Starting Workflow Run ID: {run_id} ---")
    try:
        from backend.state import api_state
        api_state.current_run_id = run_id
        print(f"--- API State updated with Run ID: {run_id} ---")
    except Exception as e:
        print(f"Note: Could not update API state: {str(e)}")

    initial_state = {
        "messages": [],  # 初始消息为空
        "data": {
            "ticker": ticker,
            "portfolio": portfolio,
            "start_date": start_date,
            "end_date": end_date,
            "num_of_news": num_of_news,
        },
        "metadata": {
            "show_reasoning": show_reasoning,
            "run_id": run_id,
            "show_summary": show_summary,
        }
    }

    try:
        from backend.utils.context_managers import workflow_run
        with workflow_run(run_id):
            # 使用线程池添加超时控制
            def run_workflow():
                return app.invoke(initial_state)
            
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_workflow)
                try:
                    final_state = future.result(timeout=600)  # 10分钟超时
                    print(f"--- Finished Workflow Run ID: {run_id} ---")
                except ConcurrentTimeoutError:
                    logger.error(f"Workflow timeout after 600 seconds for run {run_id}")
                    raise TimeoutError("Workflow execution timeout")

            if HAS_SUMMARY_REPORT and show_summary:
                store_final_state(final_state)
                enhanced_state = get_enhanced_final_state()
                print_summary_report(enhanced_state)

            if HAS_STRUCTURED_OUTPUT and show_reasoning:
                print_structured_output(final_state)
    except ImportError:
        # 使用线程池添加超时控制
        def run_workflow():
            return app.invoke(initial_state)
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_workflow)
            try:
                final_state = future.result(timeout=600)  # 10分钟超时
                print(f"--- Finished Workflow Run ID: {run_id} ---")
            except ConcurrentTimeoutError:
                logger.error(f"Workflow timeout after 600 seconds for run {run_id}")
                raise TimeoutError("Workflow execution timeout")

        if HAS_SUMMARY_REPORT and show_summary:
            store_final_state(final_state)
            enhanced_state = get_enhanced_final_state()
            print_summary_report(enhanced_state)

        if HAS_STRUCTURED_OUTPUT and show_reasoning:
            print_structured_output(final_state)
        try:
            api_state.complete_run(run_id, "completed")
        except Exception as e:
            logger.error(f"Failed to complete run {run_id}: {str(e)}")
            # 继续执行，但记录错误
    return final_state["messages"][-1].content


# --- Define the Workflow Graph ---
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("market_data_agent", market_data_agent)
workflow.add_node("technical_analyst_agent", technical_analyst_agent)
workflow.add_node("fundamentals_agent", fundamentals_agent)
workflow.add_node("sentiment_agent", sentiment_agent)
workflow.add_node("valuation_agent", valuation_agent)
workflow.add_node("macro_news_agent", macro_news_agent)  # 新闻 agent
workflow.add_node("researcher_bull", researcher_bull_agent)
workflow.add_node("researcher_bear", researcher_bear_agent)
workflow.add_node("debate_room_agent", debate_room_agent)
workflow.add_node("risk_management_agent", risk_management_agent)
workflow.add_node("macro_analyst_agent", macro_analyst_agent)
workflow.add_node("portfolio_management_agent", portfolio_management_agent)

# Set entry point
workflow.set_entry_point("market_data_agent")

# Edges from market_data_agent to the five parallel agents
workflow.add_edge("market_data_agent", "technical_analyst_agent")
workflow.add_edge("market_data_agent", "fundamentals_agent")
workflow.add_edge("market_data_agent", "sentiment_agent")
workflow.add_edge("market_data_agent", "valuation_agent")
# macro_news_agent 也从 market_data_agent 并行出来
workflow.add_edge("market_data_agent", "macro_news_agent")

# Main analysis path (technical, fundamentals, sentiment, valuation -> researchers -> ... -> macro_analyst)
workflow.add_edge("technical_analyst_agent", "researcher_bull")
workflow.add_edge("fundamentals_agent", "researcher_bull")
workflow.add_edge("sentiment_agent", "researcher_bull")
workflow.add_edge("valuation_agent", "researcher_bull")

workflow.add_edge("technical_analyst_agent", "researcher_bear")
workflow.add_edge("fundamentals_agent", "researcher_bear")
workflow.add_edge("sentiment_agent", "researcher_bear")
workflow.add_edge("valuation_agent", "researcher_bear")

workflow.add_edge("researcher_bull", "debate_room_agent")
workflow.add_edge("researcher_bear", "debate_room_agent")

workflow.add_edge("debate_room_agent", "risk_management_agent")
workflow.add_edge("risk_management_agent", "macro_analyst_agent")

# Edges to portfolio_management_agent (汇聚点)
# macro_analyst_agent (end of main analysis path) and macro_news_agent (parallel news path)
# both feed into portfolio_management_agent.
# LangGraph will wait for both parent nodes to complete before running portfolio_management_agent.
workflow.add_edge("macro_analyst_agent", "portfolio_management_agent")
workflow.add_edge("macro_news_agent", "portfolio_management_agent")

# Final node
workflow.add_edge("portfolio_management_agent", END)

app = workflow.compile()

# --- FastAPI Background Task ---


def run_fastapi():
    print("--- Starting FastAPI server in background (port 8000) ---")
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000, log_config=None)


# --- Main Execution Block ---
if __name__ == "__main__":
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    parser = argparse.ArgumentParser(
        description='Run the hedge fund trading system')
    parser.add_argument('--ticker', type=str, required=True,
                        help='Stock ticker symbol')
    parser.add_argument('--start-date', type=str,
                        help='Start date (YYYY-MM-DD). Defaults to 1 year before end date')
    parser.add_argument('--end-date', type=str,
                        help='End date (YYYY-MM-DD). Defaults to yesterday')
    parser.add_argument('--show-reasoning', action='store_true',
                        help='Show reasoning from each agent')
    parser.add_argument('--num-of-news', type=int, default=20,
                        help='Number of news articles to analyze for sentiment (default: 20)')
    parser.add_argument('--initial-capital', type=float, default=100000.0,
                        help='Initial cash amount (default: 100,000)')
    parser.add_argument('--initial-position', type=int,
                        default=0, help='Initial stock position (default: 0)')
    parser.add_argument('--summary', action='store_true',
                        help='Show beautiful summary report at the end')
    args = parser.parse_args()
    current_date = datetime.now()
    yesterday = current_date - timedelta(days=1)
    end_date = yesterday if not args.end_date else min(
        datetime.strptime(args.end_date, '%Y-%m-%d'), yesterday)
    if not args.start_date:
        start_date = end_date - timedelta(days=365)
    else:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    if start_date > end_date:
        raise ValueError("Start date cannot be after end date")
    if args.num_of_news < 1:
        raise ValueError("Number of news articles must be at least 1")
    if args.num_of_news > 100:
        raise ValueError("Number of news articles cannot exceed 100")
    portfolio = {"cash": args.initial_capital, "stock": args.initial_position}
    main_run_id = str(uuid.uuid4())
    result = run_hedge_fund(
        run_id=main_run_id,
        ticker=args.ticker,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        portfolio=portfolio,
        show_reasoning=args.show_reasoning,
        num_of_news=args.num_of_news,
        show_summary=args.summary
    )
    print("\nFinal Result:")
    print(result)
