import os
import json
from datetime import datetime
import akshare as ak
from src.utils.logging_config import setup_logger
# from langgraph.graph import AgentState # Changed import
# Added for alignment
from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from typing import Dict, Any, List
from src.utils.api_utils import agent_endpoint  # Added for alignment
from src.tools.openrouter_config import get_chat_completion
from langchain_core.messages import HumanMessage  # Added import

# LLM Prompt for analyzing full news data
LLM_PROMPT_MACRO_ANALYSIS = """你是一名资深的A股市场宏观分析师。请根据以下提供的沪深300指数（代码：000300）当日的**全部新闻数据**，进行深入分析并生成一份专业的宏观总结报告。

报告应包含以下几个方面：
1.  **市场情绪解读**：整体评估当前市场情绪（如：乐观、谨慎、悲观），并简述判断依据。
2.  **热点板块识别**：找出新闻中反映出的1-3个主要热点板块或主题，并说明其驱动因素。
3.  **潜在风险提示**：揭示新闻中可能隐藏的1-2个宏观层面或市场层面的潜在风险点。
4.  **政策影响分析**：如果新闻提及重要政策变动，请分析其可能对市场产生的短期和长期影响。
5.  **综合展望**：基于以上分析，对短期市场走势给出一个简明扼要的展望。

请确保分析客观、逻辑清晰，语言专业。直接返回分析报告内容，不要包含任何额外说明或客套话。

**当日新闻数据如下：**
{news_data_json_string}
"""

# 初始化 logger
logger = setup_logger('macro_news_agent')


@agent_endpoint("macro_news_agent", "获取沪深300全量新闻并进行宏观分析，为投资决策提供市场层面的宏观环境评估")
def macro_news_agent(state: AgentState) -> Dict[str, Any]:
    """
    获取沪深300全量新闻，调用LLM进行宏观分析，并保存结果。
    该Agent独立运行，不依赖特定上游数据，结果注入AgentState。
    """
    agent_name = "macro_news_agent"
    show_workflow_status(f"{agent_name}: --- Executing Macro News Agent ---")
    symbol = "000300"  # 沪深300指数
    news_list_for_llm: List[Dict[str, str]] = []
    summary = f"宏观新闻分析过程中发生错误: 未知错误"  # Default error summary
    retrieved_news_count = 0
    from_cache = False  # Flag to indicate if summary was loaded from cache

    today_str = datetime.now().strftime("%Y-%m-%d")
    # 改为按月缓存：使用年-月作为缓存键
    month_str = datetime.now().strftime("%Y-%m")
    output_file_path = os.path.join("src", "data", "macro_summary.json")

    # Attempt to load from cache first
    if os.path.exists(output_file_path):
        try:
            with open(output_file_path, 'r', encoding='utf-8') as f:
                all_summaries = json.load(f)
            # 检查本月是否已有缓存
            if month_str in all_summaries and all_summaries[month_str].get("summary_content"):
                cached_data = all_summaries[month_str]
                summary = cached_data["summary_content"]
                retrieved_news_count = cached_data.get(
                    "retrieved_news_count", 0)  # Get cached news count
                from_cache = True
                show_workflow_status(
                    f"{agent_name}: 从缓存加载 {month_str} 月的宏观新闻总结。")
                show_agent_reasoning(
                    f"Loaded macro summary for {month_str} from cache. News count: {retrieved_news_count}", agent_name)
        except json.JSONDecodeError:
            show_agent_reasoning(
                f"JSONDecodeError for {output_file_path} when trying to load cache. Will fetch fresh data.", agent_name)
            all_summaries = {}  # Reset if file is corrupt
        except Exception as e:
            show_agent_reasoning(
                f"Error loading cache from {output_file_path}: {str(e)}. Will fetch fresh data.", agent_name)
            all_summaries = {}  # Reset on other errors

    if not from_cache:
        show_workflow_status(f"{agent_name}: 缓存中未找到本月({month_str})总结或缓存无效，开始获取实时新闻。")
        try:
            show_workflow_status(
                f"{agent_name}: Fetching news for symbol {symbol}")
            news_df = ak.stock_news_em(symbol=symbol)
            if news_df is None or news_df.empty:
                message = f"未获取到 {symbol} 的新闻数据。"
                show_workflow_status(f"{agent_name}: {message}")
                show_agent_reasoning(
                    f"No news found for {symbol}. Proceeding with no data summary.", agent_name)
                summary = "今日未获取到相关宏观新闻数据。"
            else:
                retrieved_news_count = len(news_df)
                message = f"成功获取到 {symbol} 的 {retrieved_news_count} 条新闻数据。"
                show_workflow_status(f"{agent_name}: {message}")
                show_agent_reasoning(
                    f"Successfully fetched {retrieved_news_count} news items for {symbol}. Preparing for LLM analysis.", agent_name)
                for _, row in news_df.iterrows():
                    news_item = {
                        "title": str(row.get("新闻标题", "")).strip(),
                        "content": str(row.get("新闻内容", "")).strip(),  # 全量内容
                        "publish_time": str(row.get("发布时间", "")).strip()
                    }
                    news_list_for_llm.append(news_item)

                news_data_json_string = json.dumps(
                    news_list_for_llm, ensure_ascii=False, indent=2)
                prompt_filled = LLM_PROMPT_MACRO_ANALYSIS.format(
                    news_data_json_string=news_data_json_string)

                show_workflow_status(
                    f"{agent_name}: Calling LLM for analysis.")
                llm_response = get_chat_completion(
                    messages=[{"role": "user", "content": prompt_filled}]
                )
                summary = llm_response.strip() if llm_response else "LLM分析未能返回有效结果。"
                show_workflow_status(f"{agent_name}: LLM宏观分析结果获取成功.")
                show_agent_reasoning(
                    f"LLM analysis complete. Summary (first 100 chars): {summary[:100]}...", agent_name)

        except Exception as e:
            error_message = f"{agent_name}: 执行出错: {e}"
            show_workflow_status(error_message)
            show_agent_reasoning(
                f"Exception during execution: {str(e)}", agent_name)
            summary = f"宏观新闻分析过程中发生错误: {str(e)}"

    # 保存总结到JSON文件 (only if not from cache and successful, or if updating existing)
    if not from_cache:  # Also save if summary was updated, even if initially from cache but e.g. re-analyzed
        show_workflow_status(
            f"{agent_name}: Preparing to save summary to {output_file_path}")

        # Ensure all_summaries is initialized if cache loading failed or file didn't exist
        if not os.path.exists(output_file_path) or 'all_summaries' not in locals():
            all_summaries = {}
            # if file exists but all_summaries wasn't set (e.g. decode error)
            if os.path.exists(output_file_path):
                try:
                    with open(output_file_path, 'r', encoding='utf-8') as f:
                        all_summaries = json.load(f)
                except json.JSONDecodeError:
                    all_summaries = {}  # If still error, start fresh

        os.makedirs(os.path.dirname(output_file_path),
                    exist_ok=True)  # Ensure directory exists

        current_summary_details = {
            "summary_content": summary,
            "retrieved_news_count": retrieved_news_count,
            "last_updated": datetime.now().isoformat(),
            "analysis_date": today_str  # 记录实际分析的日期
        }
        all_summaries[month_str] = current_summary_details

        try:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(all_summaries, f, ensure_ascii=False, indent=4)
            show_workflow_status(
                f"{agent_name}: 宏观新闻总结已保存到: {output_file_path}")
        except Exception as e:
            show_workflow_status(f"{agent_name}: 保存宏观新闻总结文件失败: {e}")
            show_agent_reasoning(
                f"Failed to save summary to {output_file_path}: {str(e)}", agent_name)

    show_workflow_status(f"{agent_name}: Execution finished.")

    new_message_content = f"Macro News Agent Analysis for {month_str} (from_cache={from_cache}):\\n{summary}"
    new_message = HumanMessage(content=new_message_content, name=agent_name)

    agent_details_for_metadata = {
        "summary_generated_on": month_str,
        "analysis_period": "monthly",  # 新增字段表示分析周期
        "news_count_for_summary": retrieved_news_count,
        "llm_summary_preview": summary[:150] + "..." if len(summary) > 150 else summary,
        "loaded_from_cache": from_cache
    }
    # logger.info(f"--- DEBUG: macro_news_agent COMPLETED ---")
    # logger.info(
    # f"--- DEBUG: macro_news_agent RETURN messages: {[msg.name for msg in [new_message]]} ---")
    return {
        "messages": [new_message],
        "data": {**state["data"], "macro_news_analysis_result": summary},
        "metadata": {
            **state["metadata"],
            f"{agent_name}_details": agent_details_for_metadata
        }
    }
