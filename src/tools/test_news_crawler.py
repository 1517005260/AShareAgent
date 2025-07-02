from src.tools.news_crawler import get_stock_news
import os
import sys
import json
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)


def test_news_crawler():
    """测试新闻爬取和保存功能"""
    # 测试参数
    test_symbols = ["600519", "300750", "000001"]  # 测试不同的股票代码
    test_news_counts = [5, 10, 20]  # 测试不同的新闻数量

    print("\n=== 开始测试新闻爬取功能 ===")
    print(f"项目根目录: {project_root}")

    # 检查数据目录
    news_dir = os.path.join(project_root, "src", "data", "stock_news")
    print(f"新闻存储目录: {news_dir}")

    if not os.path.exists(news_dir):
        print(f"创建新闻存储目录: {news_dir}")
        os.makedirs(news_dir, exist_ok=True)

    for symbol in test_symbols:
        print(f"\n测试股票代码: {symbol}")
        for news_count in test_news_counts:
            print(f"\n  请求新闻数量: {news_count}")

            try:
                # 爬取新闻
                news_list = get_stock_news(symbol, max_news=news_count)

                # 检查新闻列表
                if news_list:
                    print(f"  成功获取新闻数量: {len(news_list)}")

                    # 检查新闻文件路径
                    news_file = os.path.join(news_dir, f"{symbol}_news.json")

                    # 保存新闻数据
                    try:
                        save_data = {
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "news": news_list
                        }
                        with open(news_file, 'w', encoding='utf-8') as f:
                            json.dump(save_data, f,
                                      ensure_ascii=False, indent=2)
                        print(f"  新闻文件已保存: {news_file}")

                        # 验证文件内容
                        with open(news_file, 'r', encoding='utf-8') as f:
                            saved_data = json.load(f)
                            saved_news = saved_data.get("news", [])
                            print(f"  文件中的新闻数量: {len(saved_news)}")
                            print(f"  保存日期: {saved_data.get('date')}")

                            # 检查文件格式
                            if saved_news and isinstance(saved_news[0], dict):
                                print("  新闻格式正确")
                                print(f"  示例新闻标题: {saved_news[0]['title']}")
                            else:
                                print("  警告: 新闻格式可能不正确")
                    except Exception as e:
                        print(f"  保存或验证文件时出错: {e}")
                else:
                    print("  错误: 未获取到新闻")

            except Exception as e:
                print(f"  测试过程中出错: {e}")

            print("\n  等待5秒后继续下一个测试...")
            import time
            time.sleep(5)  # 避免请求过于频繁


if __name__ == "__main__":
    test_news_crawler()
