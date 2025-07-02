import os

symbol = "000001"
news_dir = os.path.join(os.path.dirname(
        os.path.dirname(__file__)), "data", "stock_news")
if not os.path.exists(news_dir):
    os.makedirs(news_dir)
news_file = os.path.join(news_dir, f"{symbol}_news.json")
print(news_file)
