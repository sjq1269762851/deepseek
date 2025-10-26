import random # 用于模拟生成表情
import time # 用于模拟网络延迟
from vector_db import db
TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "query_product_information",
            "description": "查询内部产品数据库，获取指定产品的详细卖点、成分、适用人群、使用方法等信息。同时可以获取到最近网上的一些风评以及话题看点等",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "要查询的产品名称，例如'深海蓝藻保湿面膜'"
                    }
                },
                "required": ["product_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_emoji",
            "description": "根据提供的文本内容，生成一组适合小红书风格的表情符号。",
            "parameters": {
                "type": "object",
                "properties": {
                    "context": {
                        "type": "string",
                        "description": "文案的关键内容或情感，例如'惊喜效果'、'补水保湿'"
                    }
                },
                "required": ["context"]
            }
        }
    }
]

def mock_query_product_database(product_name: str) -> str:
    """模拟查询产品数据库，返回预设的产品信息。"""
    print(f"[Tool Call] 模拟查询产品数据库：{product_name}")
    dic = db.search("product_information", product_name, "IP", 1)

    content = [line_with_distance[0] for line_with_distance in dic]

    if not content=="":
        return content
    else:
        return f"产品数据库中未找到关于 '{product_name}' 的详细信息。"

def mock_generate_emoji(context: str) -> list:
    """模拟生成表情符号，根据上下文提供常用表情。"""
    print(f"[Tool Call] 模拟生成表情符号，上下文：{context}")
    dic = db.search("emotion2emoji", context)

    content = [line_with_distance[0] for line_with_distance in dic]

    if not content=="":
        return content
    else:
        print("未能从向量数据内找到正确符合的表情")
    

    if "补水" in context or "水润" in context or "保湿" in context:
        return ["💦", "💧", "🌊", "✨"]
    elif "惊喜" in context or "哇塞" in context or "爱了" in context:
        return ["💖", "😍", "🤩", "💯"]
    elif "熬夜" in context or "疲惫" in context:
        return ["😭", "😮‍💨", "😴", "💡", ""]
    elif "好物" in context or "推荐" in context:
        return ["✅", "👍", "⭐", "🛍️"]
    else:
        return random.sample(["✨", "🔥", "💖", "💯", "🎉", "👍", "🤩", "💧", "🌿"], k=min(5, len(context.split())))

# 将模拟工具函数映射到一个字典，方便通过名称调用
available_tools = {
    "query_product_information": mock_query_product_database,
    "generate_emoji": mock_generate_emoji,
}