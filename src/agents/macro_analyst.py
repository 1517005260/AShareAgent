from langchain_core.messages import HumanMessage
from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from src.tools.news_crawler import get_stock_news
from src.utils.logging_config import setup_logger
from src.utils.api_utils import agent_endpoint, log_llm_interaction
import json
from datetime import datetime, timedelta
from src.tools.openrouter_config import get_chat_completion
from src.database.data_service import get_data_service

# 设置日志记录
logger = setup_logger('macro_analyst_agent')


@agent_endpoint("macro_analyst", "宏观分析师，分析宏观经济环境对目标股票的影响")
def macro_analyst_agent(state: AgentState):
    """Responsible for macro analysis"""
    show_workflow_status("Macro Analyst")
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]
    symbol = data["ticker"]
    logger.info(f"正在进行宏观分析: {symbol}")

    # 获取 end_date 并传递给 get_stock_news
    end_date = data.get("end_date")  # 从 run_hedge_fund 传递来的 end_date

    # 获取大量新闻数据（最多100条），传递正确的日期参数
    news_list = get_stock_news(symbol, max_news=100, date=end_date)

    # 过滤七天前的新闻（只对有publish_time字段的新闻进行过滤）
    cutoff_date = datetime.now() - timedelta(days=7)
    recent_news = []
    for news in news_list:
        if 'publish_time' in news:
            try:
                news_date = datetime.strptime(
                    news['publish_time'], '%Y-%m-%d %H:%M:%S')
                if news_date > cutoff_date:
                    recent_news.append(news)
            except ValueError:
                # 如果时间格式无法解析，默认包含这条新闻
                recent_news.append(news)
        else:
            # 如果没有publish_time字段，默认包含这条新闻
            recent_news.append(news)

    logger.info(f"获取到 {len(recent_news)} 条七天内的新闻")

    # 如果没有获取到新闻，返回默认结果
    if not recent_news:
        logger.warning(f"未获取到 {symbol} 的最近新闻，无法进行宏观分析")
        message_content = {
            "macro_environment": "neutral",
            "impact_on_stock": "neutral",
            "key_factors": [],
            "reasoning": "未获取到最近新闻，无法进行宏观分析"
        }
    else:
        # 获取宏观分析结果
        macro_analysis = get_macro_news_analysis(recent_news)
        message_content = macro_analysis

    # 如果需要显示推理过程
    if show_reasoning:
        show_agent_reasoning(message_content, "Macro Analysis Agent")
    
    # 始终保存推理信息到metadata供API使用
    state["metadata"]["agent_reasoning"] = message_content

    # 创建消息
    message = HumanMessage(
        content=json.dumps(message_content, ensure_ascii=False),
        name="macro_analyst_agent",
    )

    show_workflow_status("Macro Analyst", "completed")
    # logger.info(f"--- DEBUG: macro_analyst_agent COMPLETED ---")
    # logger.info(
    # f"--- DEBUG: macro_analyst_agent RETURN messages: {[msg.name for msg in (state['messages'] + [message])]} ---")
    return {
        "messages": state["messages"] + [message],
        "data": {
            **data,
            "macro_analysis": message_content
        },
        "metadata": state["metadata"],
    }


def get_macro_news_analysis(news_list: list) -> dict:
    """分析宏观经济新闻对股票的影响

    Args:
        news_list (list): 新闻列表

    Returns:
        dict: 宏观分析结果，包含环境评估、对股票的影响、关键因素和详细推理
    """
    if not news_list:
        return {
            "macro_environment": "neutral",
            "impact_on_stock": "neutral",
            "key_factors": [],
            "reasoning": "没有足够的新闻数据进行宏观分析"
        }

    # 获取数据服务
    data_service = get_data_service()
    
    # 生成新闻内容的唯一标识
    news_key = "|".join([
        f"{news['title']}|{news.get('publish_time', '')}"
        for news in news_list[:20]  # 使用前20条新闻作为标识
    ])

    # 检查数据库缓存
    cached_analysis = data_service.get_macro_analysis_from_cache(news_key)
    if cached_analysis:
        logger.info("使用数据库中的宏观分析结果")
        return cached_analysis

    # 准备系统消息
    system_message = {
        "role": "system",
        "content": """你是一位专业的宏观经济分析师，专注于分析宏观经济环境对A股个股的影响。
        请分析提供的新闻，从宏观角度评估当前经济环境，并分析这些宏观因素对目标股票的潜在影响。
        
        请关注以下宏观因素：
        1. 货币政策：利率、准备金率、公开市场操作等
        2. 财政政策：政府支出、税收政策、补贴等
        3. 产业政策：行业规划、监管政策、环保要求等
        4. 国际环境：全球经济形势、贸易关系、地缘政治等
        5. 市场情绪：投资者信心、市场流动性、风险偏好等
        
        你的分析应该包括：
        1. 宏观环境评估：积极(positive)、中性(neutral)或消极(negative)
        2. 对目标股票的影响：利好(positive)、中性(neutral)或利空(negative)
        3. 关键影响因素：列出3-5个最重要的宏观因素
        4. 详细推理：解释为什么这些因素会影响目标股票
        
        请确保你的分析：
        1. 基于事实和数据，而非猜测
        2. 考虑行业特性和公司特点
        3. 关注中长期影响，而非短期波动
        4. 提供具体、可操作的见解"""
    }

    # 准备新闻内容
    news_content = "\n\n".join([
        f"标题：{news['title']}\n"
        f"来源：{news['source']}\n"
        f"时间：{news['publish_time']}\n"
        f"内容：{news['content']}"
        # 使用前50条新闻进行分析，注意这里不是100，因为可能超过上下文限制，可根据自己的LLM来自行设置
        for news in news_list[:50]
    ])

    user_message = {
        "role": "user",
        "content": f"请分析以下新闻，评估当前宏观经济环境及其对相关A股上市公司的影响：\n\n{news_content}\n\n请以JSON格式返回结果，包含以下字段：macro_environment（宏观环境：positive/neutral/negative）、impact_on_stock（对股票影响：positive/neutral/negative）、key_factors（关键因素数组）、reasoning（详细推理）。"
    }

    try:
        # 获取LLM分析结果
        logger.info("正在调用LLM进行宏观分析...")
        result = get_chat_completion([system_message, user_message])
        if result is None:
            logger.error("LLM分析失败，无法获取宏观分析结果")
            return {
                "macro_environment": "neutral",
                "impact_on_stock": "neutral",
                "key_factors": [],
                "reasoning": "LLM分析失败，无法获取宏观分析结果"
            }

        # 解析JSON结果
        try:
            # 尝试直接解析
            analysis_result = json.loads(result.strip())
            logger.info("成功解析LLM返回的JSON结果")
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取JSON部分
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', result, re.DOTALL)
            if json_match:
                try:
                    analysis_result = json.loads(json_match.group(1).strip())
                    logger.info("成功从代码块中提取并解析JSON结果")
                except:
                    # 如果仍然失败，返回默认结果
                    logger.error("无法解析代码块中的JSON结果")
                    return {
                        "macro_environment": "neutral",
                        "impact_on_stock": "neutral",
                        "key_factors": [],
                        "reasoning": "无法解析LLM返回的JSON结果"
                    }
            else:
                # 如果没有找到JSON，返回默认结果
                logger.error("LLM未返回有效的JSON格式结果")
                return {
                    "macro_environment": "neutral",
                    "impact_on_stock": "neutral",
                    "key_factors": [],
                    "reasoning": "LLM未返回有效的JSON格式结果"
                }

        # 缓存结果到数据库
        try:
            current_date = datetime.now().strftime('%Y-%m-%d')
            data_service.save_macro_analysis_to_cache(
                analysis_key=news_key,
                date=current_date,
                analysis_type='news',
                macro_environment=analysis_result.get('macro_environment'),
                impact_on_stock=analysis_result.get('impact_on_stock'),
                key_factors=analysis_result.get('key_factors', []),
                reasoning=analysis_result.get('reasoning'),
                content=json.dumps(analysis_result, ensure_ascii=False),
                news_count=len(news_list)
            )
            logger.info("宏观分析结果已缓存到数据库")
        except Exception as cache_error:
            logger.warning(f"缓存宏观分析结果时出错: {cache_error}")

        return analysis_result

    except Exception as e:
        logger.error(f"宏观分析出错: {e}")
        return {
            "macro_environment": "neutral",
            "impact_on_stock": "neutral",
            "key_factors": [],
            "reasoning": f"分析过程中出错: {str(e)}"
        }
