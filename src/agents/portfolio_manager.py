from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
import json
from src.utils.logging_config import setup_logger
from concurrent.futures import ThreadPoolExecutor, TimeoutError as ConcurrentTimeoutError

from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from src.tools.openrouter_config import get_chat_completion
from src.utils.api_utils import agent_endpoint, log_llm_interaction

# 初始化 logger
logger = setup_logger('portfolio_management_agent')

##### Portfolio Management Agent #####

# Helper function to get the latest message by agent name


def get_latest_message_by_name(messages: list, name: str):
    for msg in reversed(messages):
        if msg.name == name:
            return msg
    logger.debug(
        f"Message from agent '{name}' not found in portfolio_management_agent.")
    # Return a dummy message object or raise an error, depending on desired handling
    # For now, returning a dummy message to avoid crashing, but content will be None.
    return HumanMessage(content=json.dumps({"signal": "error", "details": f"Message from {name} not found"}), name=name)


@agent_endpoint("portfolio_management", "负责投资组合管理和最终交易决策")
def portfolio_management_agent(state: AgentState):
    """Responsible for portfolio management"""
    agent_name = "portfolio_management_agent"
    logger.info(f"\n--- DEBUG: {agent_name} START ---")

    # Log raw incoming messages
    # logger.info(
    # f"--- DEBUG: {agent_name} RAW INCOMING messages: {[msg.name for msg in state['messages']]} ---")
    # for i, msg in enumerate(state['messages']):
    #     logger.info(
    #         f"  DEBUG RAW MSG {i}: name='{msg.name}', content_preview='{str(msg.content)[:100]}...'")

    # Clean and unique messages by agent name, taking the latest if duplicates exist
    # This is crucial because this agent is a sink for multiple paths.
    unique_incoming_messages = {}
    for msg in state["messages"]:
        # Keep overriding with later messages to get the latest by name
        unique_incoming_messages[msg.name] = msg

    cleaned_messages_for_processing = list(unique_incoming_messages.values())
    # logger.info(
    # f"--- DEBUG: {agent_name} CLEANED messages for processing: {[msg.name for msg in cleaned_messages_for_processing]} ---")

    show_workflow_status(f"{agent_name}: --- Executing Portfolio Manager ---")
    show_reasoning_flag = state["metadata"]["show_reasoning"]
    portfolio = state["data"]["portfolio"]

    # Get messages from other agents using the cleaned list
    technical_message = get_latest_message_by_name(
        cleaned_messages_for_processing, "technical_analyst_agent")
    fundamentals_message = get_latest_message_by_name(
        cleaned_messages_for_processing, "fundamentals_agent")
    sentiment_message = get_latest_message_by_name(
        cleaned_messages_for_processing, "sentiment_agent")
    valuation_message = get_latest_message_by_name(
        cleaned_messages_for_processing, "valuation_agent")
    risk_message = get_latest_message_by_name(
        cleaned_messages_for_processing, "risk_management_agent")
    tool_based_macro_message = get_latest_message_by_name(
        cleaned_messages_for_processing, "macro_analyst_agent")  # This is the main analysis path output
    # Add bull and bear researcher messages
    bull_researcher_message = get_latest_message_by_name(
        cleaned_messages_for_processing, "researcher_bull_agent")
    bear_researcher_message = get_latest_message_by_name(
        cleaned_messages_for_processing, "researcher_bear_agent")

    # Extract content, handling potential None if message not found by get_latest_message_by_name
    technical_content = technical_message.content if technical_message else json.dumps(
        {"signal": "error", "details": "Technical message missing"})
    fundamentals_content = fundamentals_message.content if fundamentals_message else json.dumps(
        {"signal": "error", "details": "Fundamentals message missing"})
    sentiment_content = sentiment_message.content if sentiment_message else json.dumps(
        {"signal": "error", "details": "Sentiment message missing"})
    valuation_content = valuation_message.content if valuation_message else json.dumps(
        {"signal": "error", "details": "Valuation message missing"})
    risk_content = risk_message.content if risk_message else json.dumps(
        {"signal": "error", "details": "Risk message missing"})
    tool_based_macro_content = tool_based_macro_message.content if tool_based_macro_message else json.dumps(
        {"signal": "error", "details": "Tool-based Macro message missing"})
    bull_researcher_content = bull_researcher_message.content if bull_researcher_message else json.dumps(
        {"signal": "error", "details": "Bull researcher message missing"})
    bear_researcher_content = bear_researcher_message.content if bear_researcher_message else json.dumps(
        {"signal": "error", "details": "Bear researcher message missing"})

    # Market-wide news summary from macro_news_agent (already correctly fetched from state["data"])
    market_wide_news_summary_content = state["data"].get(
        "macro_news_analysis_result", "大盘宏观新闻分析不可用或未提供。")
    # Optional: also try to get the message object for consistency in agent_signals, though data field is primary source
    macro_news_agent_message_obj = get_latest_message_by_name(
        cleaned_messages_for_processing, "macro_news_agent")

    system_message_content = """You are a portfolio manager making final trading decisions.
            Your job is to make a trading decision based on the team's analysis while considering
            risk management constraints as important guidance, not absolute rules.

            RISK MANAGEMENT GUIDANCE:
            - Consider the max_position_size specified by the risk manager as a guideline
            - The trading_action from risk management is valuable input, but not binding
            - You have the authority to override risk recommendations if other signals strongly justify it
            - However, be very cautious when overriding high risk warnings (risk_score >= 8)

            A股市场权重配置策略 (根据市场特色调整):
            1. 基本面分析 (35% weight) - A股基本面驱动更强
            2. 估值分析 (25% weight) - 估值回归重要性
            3. 技术分析 (20% weight) - 适应T+1交易和涨跌停
            4. 宏观分析 (15% weight) - 包含两个输入:
               a) 常规宏观环境 (来自宏观分析师)
               b) 大盘新闻摘要 (来自宏观新闻分析师)
               特别关注政策影响和资金流向
            5. 情绪分析 (5% weight) - A股情绪波动较大，权重降低

            A股决策流程优化:
            1. 综合评估所有投资信号，特别关注基本面变化
            2. 考虑风险管理建议，但优先考虑强投资逻辑
            3. A股特色风险控制:
               - 风险评分>=8且其他信号弱时显著减仓
               - 考虑T+1交易限制，避免日内频繁调整
               - 监控涨跌停板风险，预留安全边际
            4. 仓位管理原则:
               - 除非有重大基本面变化，避免清空仓位
               - 政策敏感期降低仓位上限
               - 市场极端情绪时采用逆向操作
            5. 将风险管理仓位建议作为指导而非硬性限制

            Provide the following in your output JSON:
            - "action": "buy" | "sell" | "hold",
            - "quantity": <positive integer>
            - "confidence": <float between 0 and 1>
            - "agent_signals": <list of agent signals including agent name, signal (bullish | bearish | neutral), and their confidence>.
              重要: 'agent_signals'列表必须包含以下条目:
                - "technical_analysis" (技术分析)
                - "fundamental_analysis" (基本面分析)
                - "sentiment_analysis" (情绪分析)
                - "valuation_analysis" (估值分析)
                - "risk_management" (风险管理)
                - "selected_stock_macro_analysis" (个股宏观分析)
                - "market_wide_news_summary(沪深300指数)" (大盘新闻摘要)
                - "ashare_policy_impact" (A股政策影响评估)
                - "liquidity_assessment" (流动性评估)
                - "bull_researcher" (多方研究分析)
                - "bear_researcher" (空方研究分析)
                每个信号需提供bullish/bearish/neutral标记和置信度
            - "reasoning": <决策解释，包括如何权衡所有信号、宏观输入、以及是否遵循或覆盖风险管理建议。特别说明A股市场特色因素的考虑>
            - "ashare_considerations": <A股特色考虑因素，如T+1限制、政策影响、流动性等>

            A股交易规则:
            - 将风险管理仓位限制作为指导原则
            - 只有在有可用资金时才买入
            - 只有在持有股份时才卖出
            - 卖出数量必须≤当前持仓
            - A股特色规则:
              * 考虑T+1交易制度，当日买入次日方可卖出
              * 监控涨跌停板，避免在极端价格执行
              * 政策敏感期采用保守仓位策略
              * 在仓位sizing上保守但不让风险管理完全压制强投资信号
              * 考虑A股波动性，设置合理的安全边际"""
    system_message = {
        "role": "system",
        "content": system_message_content
    }

    user_message_content = f"""Based on the team's analysis below, make your trading decision.

            Technical Analysis Signal: {technical_content}
            Fundamental Analysis Signal: {fundamentals_content}
            Sentiment Analysis Signal: {sentiment_content}
            Valuation Analysis Signal: {valuation_content}
            Risk Management Signal: {risk_content}
            General Macro Analysis (from Macro Analyst Agent): {tool_based_macro_content}
            Daily Market-Wide News Summary (from Macro News Agent):
            {market_wide_news_summary_content}
            
            Bull Researcher Analysis: {bull_researcher_content}
            Bear Researcher Analysis: {bear_researcher_content}

            当前投资组合状况:
            现金: {portfolio['cash']:.2f}
            当前持仓: {portfolio['stock']} 股
            
            A股市场状态考虑:
            - 当前是否处于政策敏感期
            - 市场流动性状况
            - 涨跌停板风险评估
            - T+1交易制约影响

            输出纯JSON格式。确保'agent_signals'包含系统提示中的所有必需代理。"""
    user_message = {
        "role": "user",
        "content": user_message_content
    }

    show_agent_reasoning(
        agent_name, f"Preparing LLM. User msg includes: TA, FA, Sent, Val, Risk, GeneralMacro, MarketNews.")

    llm_interaction_messages = [system_message, user_message]
    
    # 使用线程池添加超时控制
    def call_llm():
        return get_chat_completion(llm_interaction_messages)
    
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(call_llm)
            llm_response_content = future.result(timeout=90)  # 90秒超时
    except ConcurrentTimeoutError:
        logger.error(f"{agent_name}: LLM call timeout after 90 seconds")
        llm_response_content = None
    except Exception as e:
        logger.error(f"{agent_name}: LLM call failed: {e}")
        llm_response_content = None

    current_metadata = state["metadata"]
    current_metadata["current_agent_name"] = agent_name

    def get_llm_result_for_logging_wrapper():
        return llm_response_content
    log_llm_interaction(state)(get_llm_result_for_logging_wrapper)()

    if llm_response_content is None:
        show_agent_reasoning(
            agent_name, "LLM call failed. Using default conservative decision.")
        # Ensure the dummy response matches the expected structure for agent_signals
        llm_response_content = json.dumps({
            "action": "hold",
            "quantity": 0,
            "confidence": 0.7,
            "agent_signals": [
                {"agent_name": "technical_analysis",
                    "signal": "neutral", "confidence": 0.0},
                {"agent_name": "fundamental_analysis",
                    "signal": "neutral", "confidence": 0.0},
                {"agent_name": "sentiment_analysis",
                    "signal": "neutral", "confidence": 0.0},
                {"agent_name": "valuation_analysis",
                    "signal": "neutral", "confidence": 0.0},
                {"agent_name": "risk_management",
                    "signal": "hold", "confidence": 1.0},
                {"agent_name": "selected_stock_macro_analysis",
                    "signal": "neutral", "confidence": 0.0},
                {"agent_name": "market_wide_news_summary(沪深300指数)",
                    "signal": "unavailable_or_llm_error", "confidence": 0.0},
                {"agent_name": "ashare_policy_impact",
                    "signal": "neutral", "confidence": 0.0},
                {"agent_name": "liquidity_assessment",
                    "signal": "neutral", "confidence": 0.0},
                {"agent_name": "bull_researcher",
                    "signal": "neutral", "confidence": 0.0},
                {"agent_name": "bear_researcher",
                    "signal": "neutral", "confidence": 0.0}
            ],
            "reasoning": "LLM API error. Defaulting to conservative hold based on risk management."
        })

    final_decision_message = HumanMessage(
        content=llm_response_content,
        name=agent_name,
    )

    if show_reasoning_flag:
        show_agent_reasoning(
            agent_name, f"Final LLM decision JSON: {llm_response_content}")

    agent_decision_details_value = {}
    try:
        decision_json = json.loads(llm_response_content)
        
        # 后处理：为多空研究员添加详细信息
        if "agent_signals" in decision_json:
            # 解析多空研究员的原始内容
            bull_researcher_data = {}
            bear_researcher_data = {}
            
            # 调试：打印原始内容
            logger.info(f"Debug: bull_researcher_content = {bull_researcher_content[:200] if bull_researcher_content else 'None'}...")
            logger.info(f"Debug: bear_researcher_content = {bear_researcher_content[:200] if bear_researcher_content else 'None'}...")
            
            try:
                bull_researcher_data = json.loads(bull_researcher_content)
                logger.info(f"Debug: Successfully parsed bull_researcher_data with keys: {list(bull_researcher_data.keys())}")
            except Exception as e:
                logger.error(f"Debug: Failed to parse bull_researcher_content: {e}")
                
            try:
                bear_researcher_data = json.loads(bear_researcher_content)
                logger.info(f"Debug: Successfully parsed bear_researcher_data with keys: {list(bear_researcher_data.keys())}")
            except Exception as e:
                logger.error(f"Debug: Failed to parse bear_researcher_content: {e}")
            
            # 为agent_signals中的多空研究员添加详细信息
            for signal in decision_json["agent_signals"]:
                if signal.get("agent_name") == "bull_researcher" and bull_researcher_data:
                    signal.update({
                        "reasoning": bull_researcher_data.get("reasoning", ""),
                        "thesis_points": bull_researcher_data.get("thesis_points", []),
                        "perspective": bull_researcher_data.get("perspective", "bullish"),
                        "signal_weights": bull_researcher_data.get("signal_weights", {}),
                        "ashare_factors": bull_researcher_data.get("ashare_factors", {})
                    })
                elif signal.get("agent_name") == "bear_researcher" and bear_researcher_data:
                    signal.update({
                        "reasoning": bear_researcher_data.get("reasoning", ""),
                        "thesis_points": bear_researcher_data.get("thesis_points", []),
                        "perspective": bear_researcher_data.get("perspective", "bearish"),
                        "risk_factors": bear_researcher_data.get("risk_factors", []),
                        "ashare_risks": bear_researcher_data.get("ashare_risks", {})
                    })
            
            # 更新LLM响应内容
            llm_response_content = json.dumps(decision_json)
        
        agent_decision_details_value = {
            "action": decision_json.get("action"),
            "quantity": decision_json.get("quantity"),
            "confidence": decision_json.get("confidence"),
            "reasoning_snippet": decision_json.get("reasoning", "")[:150] + "..."
        }
    except json.JSONDecodeError:
        agent_decision_details_value = {
            "error": "Failed to parse LLM decision JSON from portfolio manager",
            "raw_response_snippet": llm_response_content[:200] + "..."
        }

    show_workflow_status(f"{agent_name}: --- Portfolio Manager Completed ---")

    # The portfolio_management_agent is a terminal or near-terminal node in terms of new message generation for the main state.
    # It should return its own decision, and an updated state["messages"] that includes its decision.
    # As it's a汇聚点, it should ideally start with a cleaned list of messages from its inputs.
    # The cleaned_messages_for_processing already did this. We append its new message to this cleaned list.

    # If we strictly want to follow the pattern of `state["messages"] + [new_message]` for all non-leaf nodes,
    # then the `cleaned_messages_for_processing` should become the new `state["messages"]` for this node's context.
    # However, for simplicity and robustness, let's assume its output `messages` should just be its own message added to the cleaned input it processed.

    final_messages_output = cleaned_messages_for_processing + [final_decision_message]
    # Alternative if we want to be super strict about adding to the raw incoming state["messages"]:
    # final_messages_output = state["messages"] + [final_decision_message]
    # But this ^ is prone to the duplication we are trying to solve if not careful.
    # The most robust is that portfolio_manager provides its clear output, and the graph handles accumulation if needed for further steps (none in this case as it's END).

    # logger.info(
    # f"--- DEBUG: {agent_name} RETURN messages: {[msg.name for msg in final_messages_output]} ---")

    return {
        "messages": final_messages_output,
        "data": state["data"],
        "metadata": {
            **state["metadata"],
            f"{agent_name}_decision_details": agent_decision_details_value,
            "agent_reasoning": llm_response_content
        }
    }


def format_decision(action: str, quantity: int, confidence: float, agent_signals: list, reasoning: str, market_wide_news_summary: str = "未提供") -> dict:
    """Format the trading decision into a standardized output format.
    Think in English but output analysis in Chinese."""

    # Get signals with safe fallbacks - all next() calls already have None as default
    fundamental_signal = next(
        (s for s in agent_signals if s["agent_name"] == "fundamental_analysis"), None)
    valuation_signal = next(
        (s for s in agent_signals if s["agent_name"] == "valuation_analysis"), None)
    technical_signal = next(
        (s for s in agent_signals if s["agent_name"] == "technical_analysis"), None)
    sentiment_signal = next(
        (s for s in agent_signals if s["agent_name"] == "sentiment_analysis"), None)
    risk_signal = next(
        (s for s in agent_signals if s["agent_name"] == "risk_management"), None)
    # Existing macro signal from macro_analyst_agent (tool-based)
    general_macro_signal = next(
        (s for s in agent_signals if s["agent_name"] == "macro_analyst_agent"), None)
    # New market-wide news summary signal from macro_news_agent
    market_wide_news_signal = next(
        (s for s in agent_signals if s["agent_name"] == "macro_news_agent"), None)

    def signal_to_chinese(signal_data):
        if not signal_data:
            return "无数据"
        if signal_data.get("signal") == "bullish":
            return "看多"
        if signal_data.get("signal") == "bearish":
            return "看空"
        return "中性"

    detailed_analysis = f"""
====================================
          投资分析报告
====================================

一、策略分析

1. 基本面分析 (权重30%):
   信号: {signal_to_chinese(fundamental_signal)}
   置信度: {fundamental_signal['confidence']*100:.0f if fundamental_signal else 0}%
   要点:
   - 盈利能力: {fundamental_signal.get('reasoning', {}).get('profitability_signal', {}).get('details', '无数据') if fundamental_signal else '无数据'}
   - 增长情况: {fundamental_signal.get('reasoning', {}).get('growth_signal', {}).get('details', '无数据') if fundamental_signal else '无数据'}
   - 财务健康: {fundamental_signal.get('reasoning', {}).get('financial_health_signal', {}).get('details', '无数据') if fundamental_signal else '无数据'}
   - 估值水平: {fundamental_signal.get('reasoning', {}).get('price_ratios_signal', {}).get('details', '无数据') if fundamental_signal else '无数据'}

2. 估值分析 (权重35%):
   信号: {signal_to_chinese(valuation_signal)}
   置信度: {valuation_signal['confidence']*100:.0f if valuation_signal else 0}%
   要点:
   - DCF估值: {valuation_signal.get('reasoning', {}).get('dcf_analysis', {}).get('details', '无数据') if valuation_signal else '无数据'}
   - 所有者收益法: {valuation_signal.get('reasoning', {}).get('owner_earnings_analysis', {}).get('details', '无数据') if valuation_signal else '无数据'}

3. 技术分析 (权重25%):
   信号: {signal_to_chinese(technical_signal)}
   置信度: {technical_signal['confidence']*100:.0f if technical_signal else 0}%
   要点:
   - 趋势跟踪: ADX={technical_signal.get('strategy_signals', {}).get('trend_following', {}).get('metrics', {}).get('adx', 0.0):.2f if technical_signal else 0.0:.2f}
   - 均值回归: RSI(14)={technical_signal.get('strategy_signals', {}).get('mean_reversion', {}).get('metrics', {}).get('rsi_14', 0.0):.2f if technical_signal else 0.0:.2f}
   - 动量指标:
     * 1月动量={technical_signal.get('strategy_signals', {}).get('momentum', {}).get('metrics', {}).get('momentum_1m', 0.0):.2% if technical_signal else 0.0:.2%}
     * 3月动量={technical_signal.get('strategy_signals', {}).get('momentum', {}).get('metrics', {}).get('momentum_3m', 0.0):.2% if technical_signal else 0.0:.2%}
     * 6月动量={technical_signal.get('strategy_signals', {}).get('momentum', {}).get('metrics', {}).get('momentum_6m', 0.0):.2% if technical_signal else 0.0:.2%}
   - 波动性: {technical_signal.get('strategy_signals', {}).get('volatility', {}).get('metrics', {}).get('historical_volatility', 0.0):.2% if technical_signal else 0.0:.2%}

4. 宏观分析 (综合权重15%):
   a) 常规宏观分析 (来自 Macro Analyst Agent):
      信号: {signal_to_chinese(general_macro_signal)}
      置信度: {general_macro_signal['confidence']*100:.0f if general_macro_signal else 0}%
      宏观环境: {general_macro_signal.get(
          'macro_environment', '无数据') if general_macro_signal else '无数据'}
      对股票影响: {general_macro_signal.get(
          'impact_on_stock', '无数据') if general_macro_signal else '无数据'}
      关键因素: {', '.join(general_macro_signal.get(
          'key_factors', ['无数据']) if general_macro_signal else ['无数据'])}

   b) 大盘宏观新闻分析 (来自 Macro News Agent):
      信号: {signal_to_chinese(market_wide_news_signal)}
      置信度: {market_wide_news_signal['confidence']*100:.0f if market_wide_news_signal else 0}%
      摘要或结论: {market_wide_news_signal.get(
          'reasoning', market_wide_news_summary) if market_wide_news_signal else market_wide_news_summary}

5. 情绪分析 (权重10%):
   信号: {signal_to_chinese(sentiment_signal)}
   置信度: {sentiment_signal['confidence']*100:.0f if sentiment_signal else 0}%
   分析: {sentiment_signal.get('reasoning', '无详细分析')
                             if sentiment_signal else '无详细分析'}

二、风险评估
风险评分: {risk_signal.get('risk_score', '无数据') if risk_signal else '无数据'}/10
主要指标:
- 波动率: {risk_signal.get('risk_metrics', {}).get('volatility', 0.0)*100:.1f if risk_signal else 0.0}%
- 最大回撤: {risk_signal.get('risk_metrics', {}).get('max_drawdown', 0.0)*100:.1f if risk_signal else 0.0}%
- VaR(95%): {risk_signal.get('risk_metrics', {}).get('value_at_risk_95', 0.0)*100:.1f if risk_signal else 0.0}%
- 市场风险: {risk_signal.get('risk_metrics', {}).get('market_risk_score', '无数据') if risk_signal else '无数据'}/10

三、投资建议
操作建议: {'买入' if action == 'buy' else '卖出' if action == 'sell' else '持有'}
交易数量: {quantity}股
决策置信度: {confidence*100:.0f}%

四、决策依据
{reasoning}

===================================="""

    return {
        "action": action,
        "quantity": quantity,
        "confidence": confidence,
        "agent_signals": agent_signals,
        "分析报告": detailed_analysis
    }
