import os
from dotenv import load_dotenv
from google import genai
import json

# 加载环境变量
env_path = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

# 获取配置
api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL")


def test_simple_prompt():
    """测试简单的提示词生成"""
    print(f"Using model: {model_name}")

    # 初始化客户端
    client = genai.Client(api_key=api_key)

    # 测试简单生成
    response = client.models.generate_content(
        model=model_name,
        contents='Write a story about a magic backpack.'
    )

    print("\nSimple prompt response:")
    print("Response type:", type(response))
    print("Response attributes:", dir(response))
    print("\nResponse text:", response.text)

    # 打印完整的响应对象结构
    print("\nFull response structure:")
    print(json.dumps(response.dict(), indent=2, ensure_ascii=False))


def test_chat_format():
    """测试聊天格式的提示词"""
    client = genai.Client(api_key=api_key)

    # 测试系统指令
    response = client.models.generate_content(
        model=model_name,
        contents='What is 1+1?',
        config={
            'system_instruction': 'You are a helpful math tutor.',
            'temperature': 0.3,
        }
    )

    print("\nChat format response:")
    print("Response type:", type(response))
    print("\nResponse text:", response.text)


if __name__ == "__main__":
    print("Testing Gemini API...")
    test_simple_prompt()
    print("\n" + "="*50 + "\n")
    test_chat_format()
