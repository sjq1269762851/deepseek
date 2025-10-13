import json
from datetime import datetime
import os
import random
from openai import OpenAI
from utils import embedding_model
from vector_db import db

# 从环境变量获取 DeepSeek API Key
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量")

# 初始化 OpenAI 客户端（假设 DeepSeek 的 API 兼容 OpenAI 格式）
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com/v1",  # DeepSeek API 的基地址
)

SYSTEM_PROMPT = """
Human: 你是一个 AI 助手。你能够从提供的上下文段落片段中找到问题的答案。
"""

class ConversationEngine:
    messages : list = [{"role": "system", "content": SYSTEM_PROMPT}]
    """
    多轮对话引擎类
    
    功能：
    - 支持多轮对话上下文管理
    - 提供简单的规则匹配回复
    - 可扩展集成大型语言模型
    - 对话日志记录
    
    使用方法：
    1. 初始化引擎: engine = ConversationEngine()
    2. 处理用户消息: response = engine.chat(user_message)
    3. 获取对话历史: history = engine.get_history()
    4. 保存对话日志: engine.save_logs()
    """
    
    def __init__(self, log_file):
        """
        初始化对话引擎
        
        参数:
        log_file: 对话日志保存
        """
        self.log_file = log_file
        self.conversation_history = []

    
    def chat_with_deepseek(self, question) -> str:
        dic = db.search("my_mfd_collection", question)
        context = "\n".join(
                                [line_with_distance[0] for line_with_distance in dic]
                            )
        USER_PROMPT = f"""
                        请使用以下用 <context> 标签括起来的信息片段来回答用 <question> 标签括起来的问题。最后追加原始回答的中文翻译，并用 <translated>和</translated> 标签标注。
                                    <context>
                                    {context}
                                    </context>
                                    <question>
                                    {question}
                                    </question>
                                    <translated>
                                    </translated>
                                    """
        print(USER_PROMPT)
        self.messages.append({"role": "user", "content": USER_PROMPT})
        try:
            #print(f"lpppppppp: {self.messages}")
            # 调用 DeepSeek Chat API
            response = client.chat.completions.create(
                model="deepseek-chat",  # 或 DeepSeek 提供的其他模型名称
                messages=self.messages,
                temperature=0.7,
                stream=False
            )

            # 提取生成的 HTML 内容
            if response.choices and len(response.choices) > 0:
                html_content = response.choices[0].message.content
                self.messages.append(response.choices[0].message)
                print(f"问题：{question}，响应: {html_content}")
                with open(self.log_file, "w", encoding="utf-8") as f:
                    f.write(f"Question: {question}\n")
                    f.write(f"Answer: {html_content}\n")
                return html_content
                # 保存到文件
                
                
            else:
                print("未收到有效响应")
                self.messages.pop()
                return ""
        except Exception as e:
            print(f"调用 API 出错: {e}")
            self.messages.pop()
            return ""