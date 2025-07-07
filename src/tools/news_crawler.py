import os
import sys
from datetime import datetime, timedelta
import time
import pandas as pd
from urllib.parse import urlparse
import hashlib
from src.tools.openrouter_config import get_chat_completion, logger as api_logger
from src.database.data_service import get_data_service

# 导入 Bing 搜索模块
try:
    from src.crawler.search import (
        bing_search_sync, 
        SearchOptions
    )
except ImportError:
    print("警告: 无法导入 Bing 搜索模块，将回退到 akshare")
    bing_search_sync = None
    SearchOptions = None

# 保留 akshare 作为备用
try:
    import akshare as ak
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("警告: akshare 不可用")
    ak = None


def build_search_query(symbol: str, date: str = None) -> str:
    """
    构建针对股票新闻的 Google 搜索查询

    Args:
        symbol: 股票代码，如 "300059"
        date: 截止日期，格式 "YYYY-MM-DD"

    Returns:
        构建好的搜索查询字符串
    """
    # 基础查询：股票代码 + 新闻关键词
    base_query = f"{symbol} 股票 新闻 财经"

    # 添加时间限制（搜索指定日期之前的新闻）
    if date:
        try:
            # 解析日期并计算一周前的日期作为开始时间
            end_date = datetime.strptime(date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=7)  # 搜索过去一周的新闻

            # Google 搜索时间语法：after:YYYY-MM-DD before:YYYY-MM-DD
            base_query += f" after:{start_date.strftime('%Y-%m-%d')} before:{date}"
        except ValueError:
            print(f"日期格式错误: {date}，忽略时间限制")

    # 限制新闻网站 - 只选择主要的财经网站
    news_sites = [
        "site:sina.com.cn",
        "site:163.com",
        "site:eastmoney.com",
        "site:cnstock.com",
        "site:hexun.com"
    ]

    # 添加网站限制
    query = f"{base_query} ({' OR '.join(news_sites)})"

    return query


def extract_domain(url: str) -> str:
    """从 URL 提取域名作为新闻来源"""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return "未知来源"


def try_bing_search(search_query: str, search_options, symbol: str) -> tuple:
    """
    使用 Bing 搜索获取财经新闻
    
    Args:
        search_query: 搜索查询字符串
        search_options: 搜索选项
        symbol: 股票代码
    
    Returns:
        tuple: (新闻列表, 使用的搜索引擎名称)
    """
    if bing_search_sync is None:
        print("Bing 搜索功能不可用")
        return [], "none"
            
    try:
        print("使用 Bing 搜索获取财经新闻...")
        search_response = bing_search_sync(search_query, search_options)
        
        if search_response.results:
            # 过滤掉搜索失败的结果
            valid_results = [
                result for result in search_response.results 
                if (result.title not in ["Bing搜索失败", "搜索失败"] and 
                    "无法完成搜索" not in result.snippet and
                    "搜索失败" not in result.snippet)
            ]
            
            if valid_results:
                # 转换搜索结果为新闻格式
                news_list = convert_search_results_to_news_format(valid_results, symbol)
                if news_list:
                    print(f"通过 Bing 搜索成功获取到 {len(news_list)} 条新闻")
                    return news_list, "bing"
                else:
                    print("Bing 搜索结果转换后为空")
            else:
                print("Bing 搜索返回的都是失败结果")
        else:
            print("Bing 搜索未返回有效结果")
            
    except Exception as e:
        print(f"Bing 搜索出错: {e}")
    
    print("Bing 搜索失败，将回退到 akshare")
    return [], "none"


def convert_search_results_to_news_format(search_results, symbol: str) -> list:
    """
    将 Bing 搜索结果转换为新闻格式，针对财经网站优化

    Args:
        search_results: Bing 搜索结果
        symbol: 股票代码

    Returns:
        符合现有格式的新闻列表
    """
    news_list = []

    for result in search_results:
        # 过滤掉明显不相关的结果
        if any(keyword in result.title.lower() for keyword in ['招聘', '求职', '广告', '登录', '注册', '404', 'error']):
            continue
            
        # 优先处理财经网站的结果
        source_domain = extract_domain(result.link)
        
        # 检查是否是主要财经网站
        financial_sites = {
            'finance.sina.com.cn': '新浪财经',
            'quote.eastmoney.com': '东方财富网',
            'stock.eastmoney.com': '东方财富网', 
            'data.eastmoney.com': '东方财富网',
            'guba.eastmoney.com': '东方财富股吧',
            'money.163.com': '网易财经',
            'finance.163.com': '网易财经',
            'cnstock.com': '中国证券网',
            'cs.com.cn': '中证网',
            'hexun.com': '和讯网',
            'stock.hexun.com': '和讯股票',
            'caijing.com.cn': '财经网',
            'yicai.com': '第一财经',
            'cls.cn': '财联社',
            'wallstreetcn.com': '华尔街见闻'
        }
        
        # 确定新闻来源
        news_source = financial_sites.get(source_domain, source_domain)
        
        # 清理标题（移除网站URL等无用信息）
        clean_title = result.title
        
        # 移除常见的URL前缀
        url_patterns = [
            r'^https?://[^\s]+\s*[-·›»]\s*',
            r'^[^\s]+\.com[^\s]*\s*[-·›»]\s*',
            r'^[^\s]+\.cn[^\s]*\s*[-·›»]\s*',
        ]
        
        for pattern in url_patterns:
            import re
            clean_title = re.sub(pattern, '', clean_title, flags=re.IGNORECASE)
        
        # 如果标题还是包含URL，尝试从snippet中提取更好的标题
        if any(x in clean_title.lower() for x in ['http', 'www.', '.com', '.cn']):
            if result.snippet and len(result.snippet) > 20:
                # 从snippet的第一句话提取标题
                import re
                sentences = re.split(r'[。！？\.\!\?]', result.snippet)
                if sentences and len(sentences[0]) > 10:
                    clean_title = sentences[0].strip()

        # 尝试从snippet中提取时间信息
        publish_time = None
        if result.snippet:
            import re
            time_patterns = [
                r'(\d{4}年\d{1,2}月\d{1,2}日)',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{1,2}天前)',
                r'(\d{1,2}小时前)',
                r'(\d{2}-\d{2})',
                r'(昨天|今天|前天)'
            ]

            for pattern in time_patterns:
                match = re.search(pattern, result.snippet)
                if match:
                    time_str = match.group(1)
                    try:
                        from datetime import datetime, timedelta
                        
                        # 处理相对时间
                        if '天前' in time_str:
                            days = int(time_str.replace('天前', ''))
                            publish_date = datetime.now() - timedelta(days=days)
                            publish_time = publish_date.strftime('%Y-%m-%d %H:%M:%S')
                        elif '小时前' in time_str:
                            hours = int(time_str.replace('小时前', ''))
                            publish_date = datetime.now() - timedelta(hours=hours)
                            publish_time = publish_date.strftime('%Y-%m-%d %H:%M:%S')
                        elif time_str == '今天':
                            publish_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        elif time_str == '昨天':
                            publish_date = datetime.now() - timedelta(days=1)
                            publish_time = publish_date.strftime('%Y-%m-%d %H:%M:%S')
                        elif time_str == '前天':
                            publish_date = datetime.now() - timedelta(days=2)
                            publish_time = publish_date.strftime('%Y-%m-%d %H:%M:%S')
                        elif '-' in time_str and len(time_str) == 10:
                            publish_time = f"{time_str} 00:00:00"
                        elif '年' in time_str and '月' in time_str and '日' in time_str:
                            # 转换 "2025年7月3日" 格式
                            date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', time_str)
                            if date_match:
                                year, month, day = date_match.groups()
                                publish_time = f"{year}-{month.zfill(2)}-{day.zfill(2)} 00:00:00"
                        break
                    except:
                        continue

        # 增强内容信息
        content = result.snippet or clean_title
        if len(content) < 50 and result.snippet:
            content = result.snippet
            
        news_item = {
            "title": clean_title,
            "content": content,
            "source": news_source,
            "url": result.link,
            "keyword": symbol,
            "search_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "search_engine": "bing"  # 标记搜索引擎
        }

        # 只有当能提取到发布时间时才添加
        if publish_time:
            news_item["publish_time"] = publish_time

        news_list.append(news_item)

    return news_list


def get_stock_news_via_akshare(symbol: str, max_news: int = 10) -> list:
    """使用 akshare 获取股票新闻的原始方法"""
    if ak is None:
        return []

    try:
        # 获取新闻列表
        news_df = ak.stock_news_em(symbol=symbol)
        if news_df is None or news_df.empty:
            print(f"未获取到{symbol}的新闻数据")
            return []

        print(f"成功获取到{len(news_df)}条新闻")

        # 实际可获取的新闻数量
        available_news_count = len(news_df)
        if available_news_count < max_news:
            print(f"警告：实际可获取的新闻数量({available_news_count})少于请求的数量({max_news})")
            max_news = available_news_count

        # 获取指定条数的新闻（考虑到可能有些新闻内容为空，多获取50%）
        news_list = []
        for _, row in news_df.head(int(max_news * 1.5)).iterrows():
            try:
                # 获取新闻内容
                content = row["新闻内容"] if "新闻内容" in row and not pd.isna(
                    row["新闻内容"]) else ""
                if not content:
                    content = row["新闻标题"]

                # 只去除首尾空白字符
                content = content.strip()
                if len(content) < 10:  # 内容太短的跳过
                    continue

                # 获取关键词
                keyword = row["关键词"] if "关键词" in row and not pd.isna(
                    row["关键词"]) else ""

                # 添加新闻
                news_item = {
                    "title": row["新闻标题"].strip(),
                    "content": content,
                    "publish_time": row["发布时间"],
                    "source": row["文章来源"].strip(),
                    "url": row["新闻链接"].strip(),
                    "keyword": keyword.strip()
                }
                news_list.append(news_item)
                print(f"成功添加新闻: {news_item['title']}")

            except Exception as e:
                print(f"处理单条新闻时出错: {e}")
                continue

        # 按发布时间排序
        news_list.sort(key=lambda x: x["publish_time"], reverse=True)

        # 只保留指定条数的有效新闻
        return news_list[:max_news]

    except Exception as e:
        print(f"akshare 获取新闻数据时出错: {e}")
        return []


def get_stock_news(symbol: str, max_news: int = 10, date: str = None) -> list:
    """获取并处理个股新闻

    Args:
        symbol (str): 股票代码，如 "300059"
        max_news (int, optional): 获取的新闻条数，默认为10条。最大支持100条。
        date (str, optional): 截止日期，格式 "YYYY-MM-DD"，用于限制获取新闻的时间范围，
                             获取该日期及之前的新闻。如果不指定，则使用当前日期。

    Returns:
        list: 新闻列表，每条新闻包含标题、内容、发布时间等信息。
              新闻来源通过智能搜索引擎获取，包含各大财经网站的相关报道。
    """

    # 限制最大新闻条数
    max_news = min(max_news, 100)

    # 获取当前日期或使用指定日期
    cache_date = date if date else datetime.now().strftime("%Y-%m-%d")
    
    # 获取数据服务
    data_service = get_data_service()
    
    print(f'开始获取{symbol}的新闻数据...')
    
    # 首先使用智能查询检查数据库中是否已有足够的新闻数据，避免重复API调用
    existing_news = data_service.get_stock_news_smart(symbol, cache_date, max_news)
    if len(existing_news) >= max_news:
        print(f"数据库中已有足够的新闻数据，跳过API调用: {symbol} {cache_date} (数据库数量: {len(existing_news)})")
        return existing_news[:max_news]
    
    # 检查是否有部分数据
    if existing_news:
        print(f"数据库中的新闻数量({len(existing_news)})不足，需要获取更多新闻({max_news}条)")
    else:
        print(f"数据库中无{symbol} {cache_date}的新闻数据，开始获取...")

    # 计算需要获取的新闻数量
    cached_news = existing_news or []
    need_more_news = max_news - len(cached_news)
    fetch_count = max(need_more_news, max_news)  # 至少获取请求的数量

    # 优先尝试使用 Bing 搜索
    new_news_list = []
    used_engine = "unknown"
    if SearchOptions and bing_search_sync:
        try:
            print("使用 Bing 搜索获取财经新闻...")

            # 构建搜索查询
            search_query = build_search_query(symbol, date)
            print(f"搜索查询: {search_query}")

            # 执行 Bing 搜索
            search_options = SearchOptions(
                limit=fetch_count * 2,  # 获取更多结果以便过滤
                timeout=30000,
                locale="zh-CN"
            )

            new_news_list, used_engine = try_bing_search(search_query, search_options, symbol)

        except Exception as e:
            print(f"Bing 搜索获取新闻时出错: {e}，回退到 akshare")
            new_news_list, used_engine = [], "none"

    # 如果 Bing 搜索失败，回退到 akshare
    if not new_news_list:
        print("使用 akshare 获取新闻...")
        new_news_list = get_stock_news_via_akshare(symbol, fetch_count)
        used_engine = "akshare"

    # 保存新获取的新闻到数据库
    saved_count = 0
    if new_news_list:
        try:
            # 使用实际使用的搜索引擎名称
            method = used_engine
            saved_count = data_service.save_stock_news(
                ticker=symbol,
                date=cache_date,
                method=method,
                query=f"股票 {symbol} 新闻",
                news_data=new_news_list
            )
            print(f"成功保存{saved_count}条新闻到数据库 (使用{method})")
        except Exception as e:
            print(f"保存新闻到数据库失败: {e}")
            saved_count = 0

    # 重新获取最新的新闻数据
    final_news = data_service.get_stock_news(symbol, cache_date)
    
    # 按发布时间排序（如果有发布时间信息）
    try:
        final_news.sort(key=lambda x: x.get("publish_time", ""), reverse=True)
    except:
        pass  # 如果排序失败，保持原顺序

    # 只保留指定条数的新闻
    return final_news[:max_news]


def get_news_sentiment(news_list: list, num_of_news: int = 5) -> float:
    """分析新闻情感得分

    Args:
        news_list (list): 新闻列表
        num_of_news (int): 用于分析的新闻数量，默认为5条

    Returns:
        float: 情感得分，范围[-1, 1]，-1最消极，1最积极
    """
    if not news_list:
        return 0.0

    # 获取数据服务
    data_service = get_data_service()

    # 生成新闻内容的唯一标识
    news_key = "|".join([
        f"{news['title']}|{news['content'][:100]}|{news.get('publish_time', '')}"
        for news in news_list[:num_of_news]
    ])

    # 检查数据库缓存
    cached_sentiment_result = data_service.get_sentiment_from_cache(news_key)
    if cached_sentiment_result is not None:
        print("使用数据库中的情感分析结果")
        return cached_sentiment_result.get('sentiment_score', 0.0)
    
    print("未找到匹配的情感分析缓存，开始分析...")

    # 准备系统消息
    system_message = {
        "role": "system",
        "content": """你是一个专业的A股市场分析师，擅长解读新闻对股票走势的影响。你需要分析一组新闻的情感倾向，并给出一个介于-1到1之间的分数：
        - 1表示极其积极（例如：重大利好消息、超预期业绩、行业政策支持）
        - 0.5到0.9表示积极（例如：业绩增长、新项目落地、获得订单）
        - 0.1到0.4表示轻微积极（例如：小额合同签订、日常经营正常）
        - 0表示中性（例如：日常公告、人事变动、无重大影响的新闻）
        - -0.1到-0.4表示轻微消极（例如：小额诉讼、非核心业务亏损）
        - -0.5到-0.9表示消极（例如：业绩下滑、重要客户流失、行业政策收紧）
        - -1表示极其消极（例如：重大违规、核心业务严重亏损、被监管处罚）

        分析时重点关注：
        1. 业绩相关：财报、业绩预告、营收利润等
        2. 政策影响：行业政策、监管政策、地方政策等
        3. 市场表现：市场份额、竞争态势、商业模式等
        4. 资本运作：并购重组、股权激励、定增配股等
        5. 风险事件：诉讼仲裁、处罚、债务等
        6. 行业地位：技术创新、专利、市占率等
        7. 舆论环境：媒体评价、社会影响等

        请确保分析：
        1. 新闻的真实性和可靠性
        2. 新闻的时效性和影响范围
        3. 对公司基本面的实际影响
        4. A股市场的特殊反应规律"""
    }

    # 准备新闻内容
    news_content = "\n\n".join([
        f"标题：{news['title']}\n"
        f"来源：{news['source']}\n"
        f"时间：{news['publish_time']}\n"
        f"内容：{news['content']}"
        for news in news_list[:num_of_news]  # 使用指定数量的新闻
    ])

    user_message = {
        "role": "user",
        "content": f"请分析以下A股上市公司相关新闻的情感倾向：\n\n{news_content}\n\n请直接返回一个数字，范围是-1到1，无需解释。"
    }

    try:
        # 获取LLM分析结果
        result = get_chat_completion([system_message, user_message])
        if result is None:
            print("Error: PI error occurred, LLM returned None")
            return 0.0

        # 提取数字结果
        try:
            sentiment_score = float(result.strip())
        except ValueError as e:
            print(f"Error parsing sentiment score: {e}")
            print(f"Raw result: {result}")
            return 0.0

        # 确保分数在-1到1之间
        sentiment_score = max(-1.0, min(1.0, sentiment_score))

        # 确定情感标签
        if sentiment_score > 0.1:
            sentiment_label = 'positive'
        elif sentiment_score < -0.1:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'

        # 缓存结果到数据库
        data_service.save_sentiment_to_cache(news_key, sentiment_score, sentiment_label)
        print(f"情感分析结果已保存到数据库: {sentiment_score} ({sentiment_label})")

        return sentiment_score

    except Exception as e:
        print(f"Error analyzing news sentiment: {e}")
        return 0.0  # 出错时返回中性分数
