import json
from datetime import datetime
import os
import random
import json
import re

from openai import OpenAI
from utils import embedding_model
from vector_db import db
import agent_tool


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
你是一个资深的小红书爆款文案专家，擅长结合最新潮流和产品卖点，创作引人入胜、高互动、高转化的笔记文案。

你的任务是根据用户提供的产品和需求，生成包含标题、正文、相关标签和表情符号的完整小红书笔记。

请始终采用'Thought-Action-Observation'模式进行推理和行动。文案风格需活泼、真诚、富有感染力。当完成任务后，请以JSON格式直接输出最终文案，格式如下：
```json
{
  "title": "小红书标题",
  "body": "小红书正文",
  "hashtags": ["#标签1", "#标签2", "#标签3", "#标签4", "#标签5"],
  "emojis": ["✨", "🔥", "💖"]
}
```
在生成文案前，请务必先思考并收集足够的信息。
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

    def chat_with_deepseek(self, message: list):
        try:
            #print(f"lpppppppp: {self.messages}")
            # 调用 DeepSeek Chat API
            response = client.chat.completions.create(
                model="deepseek-chat",  # 或 DeepSeek 提供的其他模型名称
                messages=message,
                temperature=0.7,
                stream=False,
            )

            # 提取生成的 HTML 内容
            if response.choices and len(response.choices) > 0:
                response_message = response.choices[0].message
                self.messages.append(response.choices[0].message)
                return response_message
                # 保存到文件
            else:
                print("未收到有效响应")
                self.messages.pop()
                return
        except Exception as e:
            print(f"调用 API 出错: {e}")
            self.messages.pop()
            return
        
    def chat_with_deepseek_use_tool(self, message: list):
        try:
            #print(f"lpppppppp: {self.messages}")
            # 调用 DeepSeek Chat API
            response = client.chat.completions.create(
                model="deepseek-chat",  # 或 DeepSeek 提供的其他模型名称
                messages=message,
                temperature=0.7,
                stream=False,
                tools=agent_tool.TOOLS_DEFINITION, # 告知模型可用的工具
                tool_choice="auto" # 允许模型自动决定是否使用工具
            )

            # 提取生成的 HTML 内容
            if response.choices and len(response.choices) > 0:
                response_message = response.choices[0].message
                self.messages.append(response.choices[0].message)
                return response_message
                # 保存到文件
            else:
                print("未收到有效响应")
                self.messages.pop()
                return
        except Exception as e:
            print(f"调用 API 出错: {e}")
            self.messages.pop()
            return
        
    def extract_requirements(self, user_query: str) -> dict:
            """从用户提问中提取需求信息，包含产品名以及需要的风格"""

            extraction_prompt = """
                你是一个专业的营销需求分析助手。请从以下用户提问中提取关键信息，包含以下方面：
                1、需要营销的产品名
                2、需要的营销文案风格

                你以下面这种json的方式返回给我，
                {
                    "product_name": "产品名称",
                    "style": "风格要求（如：专业、幽默、活泼、科技感等）"
                }

                如果从用户的需求中没有识别到上述的关键信息，你必须以如下结果返回给我：
                {
                    "product_name": "",
                    "style": ""
                }
                
                请确保提取的信息准确且完整。
            """
            
            messages = [
                {"role": "system", "content": extraction_prompt},
                {"role": "user", "content": f"""用户提问：{user_query}"""}
            ]

            try:
                response = self.chat_with_deepseek(messages)
                print(f"deepseek 根据 {user_query} 提取了 {response.content}")
                # 解析DeepSeek的返回结果
                extracted_data = json.loads(response.content)
                return extracted_data
                
            except Exception as e:
                # 直接返回默认空值
                return {"product_name": "", "style": ""}
            
    #product_name: str, tone_style: str = "活泼甜美", max_iterations: int = 5
    def generate_rednote_by_single_chat(self, query, max_iterations: int = 5) -> str:
        """
        使用 DeepSeek Agent 生成小红书爆款文案。
        
        Args:
            product_name (str): 要生成文案的产品名称。
            tone_style (str): 文案的语气和风格，如"活泼甜美"、"知性"、"搞怪"等。
            max_iterations (int): Agent 最大迭代次数，防止无限循环。
            
        Returns:
            str: 生成的爆款文案（JSON 格式字符串）。
        """
        
        
        
        dic = self.extract_requirements(query)
        print(f"\n🚀 启动小红书文案生成助手，用户需求为：{query}\n, 成功提取到产品名为：{dic["product_name"]}, 需要的风格为: {dic["style"]}")

        # 存储对话历史，包括系统提示词和用户请求
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"请为产品「{dic["product_name"]}」生成一篇小红书爆款文案。要求：语气{dic["style"]}，包含标题、正文、至少5个相关标签和5个表情符号。请以完整的JSON格式输出，并确保JSON内容用markdown代码块包裹（例如：```json{{...}}```）。"}
        ]
        
        iteration_count = 0
        final_response = None
        
        while iteration_count < max_iterations:
            iteration_count += 1
            print(f"-- Iteration {iteration_count} --")
            
            try:
                response_message = self.chat_with_deepseek_use_tool(messages)
                
                # **ReAct模式：处理工具调用**
                if response_message.tool_calls: # 如果模型决定调用工具
                    print("Agent: 决定调用工具...")
                    messages.append(response_message) # 将工具调用信息添加到对话历史
                    
                    tool_outputs = []
                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        # 确保参数是合法的JSON字符串，即使工具不要求参数，也需要传递空字典
                        function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

                        print(f"Agent Action: 调用工具 '{function_name}'，参数：{function_args}")
                        
                        # 查找并执行对应的模拟工具函数
                        if function_name in agent_tool.available_tools:
                            tool_function = agent_tool.available_tools[function_name]
                            tool_result = tool_function(**function_args)
                            print(f"Observation: 工具返回结果：{tool_result}")
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "content": str(tool_result) # 工具结果作为字符串返回
                            })
                        else:
                            error_message = f"错误：未知的工具 '{function_name}'"
                            print(error_message)
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "content": error_message
                            })
                    messages.extend(tool_outputs) # 将工具执行结果作为 Observation 添加到对话历史
                    
                # **ReAct 模式：处理最终内容**
                elif response_message.content: # 如果模型直接返回内容（通常是最终答案）
                    print(f"[模型生成结果] {response_message.content}")
                    
                    # --- START: 添加 JSON 提取和解析逻辑 ---
                    json_string_match = re.search(r"```json\s*(\{.*\})\s*```", response_message.content, re.DOTALL)
                    
                    if json_string_match:
                        extracted_json_content = json_string_match.group(1)
                        try:
                            final_response = json.loads(extracted_json_content)
                            print("Agent: 任务完成，成功解析最终JSON文案。")
                            return self.format_rednote_for_markdown(json.dumps(final_response, ensure_ascii=False, indent=2))
                        except json.JSONDecodeError as e:
                            print(f"Agent: 提取到JSON块但解析失败: {e}")
                            print(f"尝试解析的字符串:\n{extracted_json_content}")
                            messages.append(response_message) # 解析失败，继续对话
                    else:
                        # 如果没有匹配到 ```json 块，尝试直接解析整个 content
                        try:
                            final_response = json.loads(response_message.content)
                            print("Agent: 任务完成，直接解析最终JSON文案。")
                            return self.format_rednote_for_markdown(json.dumps(final_response, ensure_ascii=False, indent=2))
                        except json.JSONDecodeError:
                            print("Agent: 生成了非JSON格式内容或非Markdown JSON块，可能还在思考或出错。")
                            messages.append(response_message) # 非JSON格式，继续对话
                    # --- END: 添加 JSON 提取和解析逻辑 ---
                else:
                    print("Agent: 未知响应，可能需要更多交互。")
                    break
                    
            except Exception as e:
                print(f"调用 DeepSeek API 时发生错误: {e}")
                break
        
        print("\n⚠️ Agent 达到最大迭代次数或未能生成最终文案。请检查Prompt或增加迭代次数。")
        return "未能成功生成文案。"
    
    def format_rednote_for_markdown(self, json_string: str) -> str:
        """
        将 JSON 格式的小红书文案转换为 Markdown 格式，以便于阅读和发布。

        Args:
            json_string (str): 包含小红书文案的 JSON 字符串。
                            预计格式为 {"title": "...", "body": "...", "hashtags": [...], "emojis": [...]}

        Returns:
            str: 格式化后的 Markdown 文本。
        """
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            return f"错误：无法解析 JSON 字符串 - {e}\n原始字符串：\n{json_string}"

        title = data.get("title", "无标题")
        body = data.get("body", "")
        hashtags = data.get("hashtags", [])
        # 表情符号通常已经融入标题和正文中，这里可以选择是否单独列出
        emojis = data.get("emojis", []) 

        # 构建 Markdown 文本
        markdown_output = f"## {title}\n\n" # 标题使用二级标题
        
        # 正文，保留换行符
        markdown_output += f"{body}\n\n"
        
        # Hashtags
        if hashtags:
            hashtag_string = " ".join(hashtags) # 小红书标签通常是空格分隔
            markdown_output += f"{hashtag_string}\n"
            
        # 如果需要，可以单独列出表情符号，但通常它们已经包含在标题和正文中
        if emojis:
            emoji_string = " ".join(emojis)
            markdown_output += f"\n使用的表情：{emoji_string}\n"
            
        return markdown_output.strip() # 去除末尾多余的空白