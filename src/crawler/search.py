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


async def google_search(
    query: str,
    options: Optional[SearchOptions] = None,
    existing_browser: Optional[Browser] = None
) -> SearchResponse:
    """
    执行 Google 搜索并返回结构化结果

    Args:
        query: 搜索查询字符串
        options: 搜索选项
        existing_browser: 可选的现有浏览器实例

    Returns:
        搜索响应对象
    """
    if options is None:
        options = SearchOptions()

    # 设置默认值
    limit = options.limit or 10
    timeout = options.timeout or 60000
    state_file = options.state_file or "./browser-state.json"
    no_save_state = options.no_save_state or False
    locale = options.locale or "zh-CN"

    logger.info(f"正在初始化浏览器搜索: {query}")

    # 检查状态文件
    storage_state = None
    saved_state = SavedState()

    # 指纹配置文件路径
    fingerprint_file = state_file.replace(".json", "-fingerprint.json")

    if os.path.exists(state_file):
        logger.info(f"发现浏览器状态文件: {state_file}")
        storage_state = state_file

        # 尝试加载保存的指纹配置
        if os.path.exists(fingerprint_file):
            try:
                with open(fingerprint_file, 'r', encoding='utf-8') as f:
                    fingerprint_data = json.load(f)
                    if fingerprint_data.get('fingerprint'):
                        fp = fingerprint_data['fingerprint']
                        saved_state.fingerprint = FingerprintConfig(**fp)
                    saved_state.google_domain = fingerprint_data.get(
                        'google_domain')
                logger.info("已加载保存的浏览器指纹配置")
            except Exception as e:
                logger.warning(f"无法加载指纹配置文件: {e}")
    else:
        logger.info(f"未找到浏览器状态文件: {state_file}")

    # Google 域名列表
    google_domains = [
        "https://www.google.com",
        "https://www.google.co.uk",
        "https://www.google.ca",
        "https://www.google.com.au"
    ]

    # 设备配置映射（简化版）
    device_configs = {
        "Desktop Chrome": {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
        "Desktop Firefox": {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
        }
    }

    async def perform_search(headless: bool = True) -> SearchResponse:
        """执行实际的搜索操作"""
        browser_was_provided = existing_browser is not None
        browser = existing_browser

        if not browser_was_provided:
            # 启动新的浏览器
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
                        "--no-first-run",
                        "--disable-gpu",
                        "--hide-scrollbars",
                        "--mute-audio"
                    ]
                )
                return await _perform_search_with_browser(browser, browser_was_provided, headless)
        else:
            return await _perform_search_with_browser(browser, browser_was_provided, headless)

    async def _perform_search_with_browser(browser: Browser, browser_was_provided: bool, headless: bool = True) -> SearchResponse:
        """使用给定浏览器执行搜索"""
        try:
            # 获取设备配置
            if saved_state.fingerprint:
                device_name = saved_state.fingerprint.device_name
            else:
                device_name = "Desktop Chrome"

            device_config = device_configs.get(
                device_name, device_configs["Desktop Chrome"])

            # 创建浏览器上下文
            context_options = {
                "viewport": device_config["viewport"],
                "user_agent": device_config["user_agent"],
                "locale": locale,
                "timezone_id": "Asia/Shanghai"
            }

            if storage_state and os.path.exists(storage_state):
                context_options["storage_state"] = storage_state

            context = await browser.new_context(**context_options)

            # 添加反检测脚本
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => false});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en', 'zh-CN']});
                window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}, app: {}};
            """)

            page = await context.new_page()

            # 选择 Google 域名
            if saved_state.google_domain:
                selected_domain = saved_state.google_domain
            else:
                import random
                selected_domain = random.choice(google_domains)
                saved_state.google_domain = selected_domain

            logger.info(f"访问 Google 搜索页面: {selected_domain}")

            # 访问 Google
            await page.goto(selected_domain, timeout=timeout)

            # 检查是否遇到人机验证
            current_url = page.url
            sorry_patterns = ["google.com/sorry",
                              "recaptcha", "captcha", "unusual traffic"]
            is_blocked = any(
                pattern in current_url for pattern in sorry_patterns)

            if is_blocked and headless:
                logger.warning("检测到人机验证，切换到有头模式")
                await context.close()
                if not browser_was_provided:
                    await browser.close()
                return await perform_search(headless=False)
            elif is_blocked:
                logger.warning("检测到人机验证，请手动完成")
                await page.wait_for_navigation(timeout=timeout * 2)

            # 查找搜索框
            search_selectors = [
                "textarea[name='q']",
                "input[name='q']",
                "textarea[title='Search']",
                "input[title='Search']"
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await page.wait_for_selector(selector, timeout=5000)
                    if search_input:
                        logger.info(f"找到搜索框: {selector}")
                        break
                except:
                    continue

            if not search_input:
                raise Exception("无法找到搜索框")

            # 输入搜索查询
            await search_input.click()
            await page.keyboard.type(query, delay=50)
            await page.keyboard.press("Enter")

            # 等待搜索结果
            await page.wait_for_load_state("networkidle", timeout=timeout)

            # 等待搜索结果元素
            result_selectors = ["#search", "#rso",
                                ".g", "[data-sokoban-container]"]
            results_found = False

            for selector in result_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=10000)
                    results_found = True
                    logger.info(f"找到搜索结果: {selector}")
                    break
                except:
                    continue

            if not results_found:
                logger.warning("未找到搜索结果元素")

            # 提取搜索结果
            results = await page.evaluate(f"""
                () => {{
                    const results = [];
                    const maxResults = {limit};
                    const seenUrls = new Set();
                    
                    // 定义选择器组合
                    const selectorSets = [
                        {{ container: '#search div[data-hveid]', title: 'h3', snippet: '.VwiC3b' }},
                        {{ container: '#rso div[data-hveid]', title: 'h3', snippet: '[data-sncf="1"]' }},
                        {{ container: '.g', title: 'h3', snippet: 'div[style*="webkit-line-clamp"]' }},
                        {{ container: 'div[jscontroller][data-hveid]', title: 'h3', snippet: 'div[role="text"]' }}
                    ];
                    
                    // 备用摘要选择器
                    const alternativeSnippetSelectors = [
                        '.VwiC3b', '[data-sncf="1"]', 'div[style*="webkit-line-clamp"]', 'div[role="text"]'
                    ];
                    
                    // 尝试每组选择器
                    for (const selectors of selectorSets) {{
                        if (results.length >= maxResults) break;
                        
                        const containers = document.querySelectorAll(selectors.container);
                        
                        for (const container of containers) {{
                            if (results.length >= maxResults) break;
                            
                            const titleElement = container.querySelector(selectors.title);
                            if (!titleElement) continue;
                            
                            const title = (titleElement.textContent || "").trim();
                            
                            // 查找链接
                            let link = '';
                            const linkInTitle = titleElement.querySelector('a');
                            if (linkInTitle) {{
                                link = linkInTitle.href;
                            }} else {{
                                let current = titleElement;
                                while (current && current.tagName !== 'A') {{
                                    current = current.parentElement;
                                }}
                                if (current && current instanceof HTMLAnchorElement) {{
                                    link = current.href;
                                }} else {{
                                    const containerLink = container.querySelector('a');
                                    if (containerLink) {{
                                        link = containerLink.href;
                                    }}
                                }}
                            }}
                            
                            // 过滤无效链接
                            if (!link || !link.startsWith('http') || seenUrls.has(link)) continue;
                            
                            // 查找摘要
                            let snippet = '';
                            const snippetElement = container.querySelector(selectors.snippet);
                            if (snippetElement) {{
                                snippet = (snippetElement.textContent || "").trim();
                            }} else {{
                                for (const altSelector of alternativeSnippetSelectors) {{
                                    const element = container.querySelector(altSelector);
                                    if (element) {{
                                        snippet = (element.textContent || "").trim();
                                        break;
                                    }}
                                }}
                                
                                if (!snippet) {{
                                    const textNodes = Array.from(container.querySelectorAll('div')).filter(el =>
                                        !el.querySelector('h3') && (el.textContent || "").trim().length > 20
                                    );
                                    if (textNodes.length > 0) {{
                                        snippet = (textNodes[0].textContent || "").trim();
                                    }}
                                }}
                            }}
                            
                            if (title && link) {{
                                results.push({{ title, link, snippet }});
                                seenUrls.add(link);
                            }}
                        }}
                    }}
                    
                    return results.slice(0, maxResults);
                }}
            """)

            logger.info(f"成功获取到 {len(results)} 条搜索结果")

            # 保存浏览器状态
            if not no_save_state:
                try:
                    os.makedirs(os.path.dirname(state_file), exist_ok=True)
                    await context.storage_state(path=state_file)

                    # 保存指纹配置
                    if not saved_state.fingerprint:
                        saved_state.fingerprint = get_host_machine_config(
                            locale)

                    fingerprint_data = {
                        'fingerprint': {
                            'device_name': saved_state.fingerprint.device_name,
                            'locale': saved_state.fingerprint.locale,
                            'timezone_id': saved_state.fingerprint.timezone_id,
                            'color_scheme': saved_state.fingerprint.color_scheme,
                            'reduced_motion': saved_state.fingerprint.reduced_motion,
                            'forced_colors': saved_state.fingerprint.forced_colors
                        },
                        'google_domain': saved_state.google_domain
                    }

                    with open(fingerprint_file, 'w', encoding='utf-8') as f:
                        json.dump(fingerprint_data, f,
                                  ensure_ascii=False, indent=2)

                    logger.info("浏览器状态保存成功")
                except Exception as e:
                    logger.error(f"保存浏览器状态时出错: {e}")

            await context.close()
            if not browser_was_provided:
                await browser.close()

            # 转换结果格式
            search_results = [
                SearchResult(title=r['title'],
                             link=r['link'], snippet=r['snippet'])
                for r in results
            ]

            return SearchResponse(query=query, results=search_results)

        except Exception as e:
            logger.error(f"搜索过程中发生错误: {e}")

            # 尝试保存状态即使出错
            try:
                if not no_save_state:
                    await context.storage_state(path=state_file)
            except:
                pass

            # 清理资源
            try:
                await context.close()
                if not browser_was_provided:
                    await browser.close()
            except:
                pass

            # 返回错误结果
            return SearchResponse(
                query=query,
                results=[SearchResult(
                    title="搜索失败",
                    link="",
                    snippet=f"无法完成搜索，错误信息: {str(e)}"
                )]
            )

    # 首先尝试无头模式
    return await perform_search(headless=True)

# 同步包装函数


def google_search_sync(
    query: str,
    options: Optional[SearchOptions] = None
) -> SearchResponse:
    """
    同步版本的 Google 搜索函数
    """
    return asyncio.run(google_search(query, options))
