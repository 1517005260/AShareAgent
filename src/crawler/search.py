import asyncio
import json
import os
import tempfile
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import logging

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
except ImportError:
    raise ImportError(
        "请安装 playwright: pip install playwright && playwright install chromium")

# 设置日志
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    link: str
    snippet: str


@dataclass
class SearchResponse:
    """搜索响应"""
    query: str
    results: List[SearchResult]


@dataclass
class SearchOptions:
    """搜索选项"""
    limit: Optional[int] = 10
    timeout: Optional[int] = 60000
    state_file: Optional[str] = "./browser-state.json"
    no_save_state: Optional[bool] = False
    locale: Optional[str] = "zh-CN"


@dataclass
class FingerprintConfig:
    """浏览器指纹配置"""
    device_name: str
    locale: str
    timezone_id: str
    color_scheme: str  # "dark" or "light"
    reduced_motion: str  # "reduce" or "no-preference"
    forced_colors: str  # "active" or "none"


@dataclass
class SavedState:
    """保存的状态"""
    fingerprint: Optional[FingerprintConfig] = None
    google_domain: Optional[str] = None


def get_host_machine_config(user_locale: Optional[str] = None) -> FingerprintConfig:
    """获取宿主机器的实际配置"""
    import time

    # 获取系统区域设置
    system_locale = user_locale or os.environ.get('LANG', 'zh-CN')

    # 根据时区推断合适的时区ID
    timezone_offset = time.timezone
    timezone_id = "Asia/Shanghai"  # 默认使用上海时区

    # 根据时间推断颜色方案
    import datetime
    hour = datetime.datetime.now().hour
    color_scheme = "dark" if (hour >= 19 or hour < 7) else "light"

    # 其他设置使用合理默认值
    reduced_motion = "no-preference"
    forced_colors = "none"
    device_name = "Desktop Chrome"

    return FingerprintConfig(
        device_name=device_name,
        locale=system_locale,
        timezone_id=timezone_id,
        color_scheme=color_scheme,
        reduced_motion=reduced_motion,
        forced_colors=forced_colors
    )


# Google 搜索已移除，只保留 Bing 搜索


async def bing_search(
    query: str,
    options: Optional[SearchOptions] = None,
    existing_browser: Optional[Browser] = None
) -> SearchResponse:
    """
    执行 Bing 搜索并返回结构化结果
    """
    if options is None:
        options = SearchOptions()

    limit = options.limit or 10
    timeout = options.timeout or 60000
    state_file = options.state_file or "./browser-state.json"
    no_save_state = options.no_save_state or False
    locale = options.locale or "zh-CN"

    logger.info(f"正在执行 Bing 搜索: {query}")

    async def perform_bing_search(headless: bool = True) -> SearchResponse:
        browser_was_provided = existing_browser is not None
        browser = existing_browser

        if not browser_was_provided:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-features=IsolateOrigins,site-per-process",
                        "--disable-web-security",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--no-first-run"
                    ]
                )
                return await _perform_bing_search_with_browser(browser, browser_was_provided, headless)
        else:
            return await _perform_bing_search_with_browser(browser, browser_was_provided, headless)

    async def _perform_bing_search_with_browser(browser: Browser, browser_was_provided: bool, headless: bool = True) -> SearchResponse:
        try:
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "locale": locale,
                "timezone_id": "Asia/Shanghai"
            }

            context = await browser.new_context(**context_options)
            page = await context.new_page()

            # 访问 Bing
            bing_url = "https://www.bing.com"
            await page.goto(bing_url, timeout=timeout)

            # 查找搜索框
            search_selectors = [
                "input[name='q']",
                "#sb_form_q",
                "input[type='search']"
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await page.wait_for_selector(selector, timeout=5000)
                    if search_input:
                        logger.info(f"找到 Bing 搜索框: {selector}")
                        break
                except:
                    continue

            if not search_input:
                raise Exception("无法找到 Bing 搜索框")

            # 输入搜索查询
            await search_input.click()
            await page.keyboard.type(query, delay=50)
            await page.keyboard.press("Enter")

            # 等待搜索结果
            await page.wait_for_load_state("networkidle", timeout=timeout)

            # 提取搜索结果
            results = await page.evaluate(f"""
                () => {{
                    const results = [];
                    const maxResults = {limit};
                    const seenUrls = new Set();
                    
                    // Bing 搜索结果选择器
                    const resultItems = document.querySelectorAll('.b_algo, .b_ans');
                    
                    for (const item of resultItems) {{
                        if (results.length >= maxResults) break;
                        
                        const titleElement = item.querySelector('h2 a, h3 a, a[href]');
                        if (!titleElement) continue;
                        
                        const title = (titleElement.textContent || "").trim();
                        const link = titleElement.href;
                        
                        if (!link || !link.startsWith('http') || seenUrls.has(link)) continue;
                        
                        // 查找摘要
                        let snippet = '';
                        const snippetSelectors = ['.b_caption p', '.b_descript', '.b_snippet'];
                        for (const selector of snippetSelectors) {{
                            const snippetElement = item.querySelector(selector);
                            if (snippetElement) {{
                                snippet = (snippetElement.textContent || "").trim();
                                break;
                            }}
                        }}
                        
                        if (title && link) {{
                            results.push({{ title, link, snippet }});
                            seenUrls.add(link);
                        }}
                    }}
                    
                    return results;
                }}
            """)

            logger.info(f"Bing 搜索成功获取到 {len(results)} 条结果")

            await context.close()
            if not browser_was_provided:
                await browser.close()

            search_results = [
                SearchResult(title=r['title'], link=r['link'], snippet=r['snippet'])
                for r in results
            ]

            return SearchResponse(query=query, results=search_results)

        except Exception as e:
            logger.error(f"Bing 搜索过程中发生错误: {e}")
            
            try:
                await context.close()
                if not browser_was_provided:
                    await browser.close()
            except:
                pass

            return SearchResponse(
                query=query,
                results=[SearchResult(
                    title="Bing搜索失败",
                    link="",
                    snippet=f"Bing搜索失败，错误信息: {str(e)}"
                )]
            )

    return await perform_bing_search(headless=True)


def bing_search_sync(
    query: str,
    options: Optional[SearchOptions] = None
) -> SearchResponse:
    """
    同步版本的 Bing 搜索函数
    """
    return asyncio.run(bing_search(query, options))


# DuckDuckGo 搜索已移除，只保留 Bing 搜索
