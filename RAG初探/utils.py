import os
from pymilvus import model as milvus_model

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量")

print(api_key)
embedding_model = milvus_model.DefaultEmbeddingFunction()
# embedding_model = milvus_model.dense.OpenAIEmbeddingFunction(
#     model_name='text-embedding-3-large', # Specify the model name
#     api_key=api_key, # Provide your OpenAI API key
#     base_url='https://api.apiyi.com/v1',
#     dimensions=512
# )