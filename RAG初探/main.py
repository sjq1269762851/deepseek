
from flask import Flask, request, jsonify
from conversation import ConversationEngine
from glob import glob
from vector_db import LocalMilvusDB
from tqdm import tqdm
from utils import embedding_model
from vector_db import db

app = Flask(__name__)
engine = ConversationEngine("conversation.log")

"""
从民法典md中读取文本
"""
def fetch_content_from_mfd() -> list[str]:
    text_lines = []
    with open("./doc/mfd.md", "r") as file:
        file_text = file.read()
        text_lines += file_text.split("# ")
    return text_lines

"""
从milvus向量数据faq md中读取文本
"""
def fetch_milvus_faq_from_dir() -> list[str]:
    text_lines = []
    for file_path in glob("milvus_docs/en/faq/*.md", recursive=True):
        with open(file_path, "r") as file:
            file_text = file.read()
            text_lines += file_text.split("# ")
    
    return text_lines

"""
初始化民法典向量数据库
"""
def init_mfd_vector_db():
    contents = fetch_content_from_mfd()
    #print(contents)
    #print("\n")
    data = []
    collection_name = "my_mfd_collection"

    doc_embeddings = embedding_model.encode_documents(contents)
    embedding_dim = len(doc_embeddings[0])
    print(f"第一个元素的维度是 {embedding_dim}\n")

    for i, line in enumerate(tqdm(contents, desc="Creating embeddings")):
        data.append({"id": i, "vector": doc_embeddings[i], "text": line})

    if not db.create_collection(collection_name, embedding_dim, "IP") :
        print("初始化数据库失败")
        exit(1)   

    if not db.insert(collection_name, data):
        print("插入到向量数据库失败")
        exit(1)
    
    print("初始化数据库成功")



@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    data = request.json
    user_message = data.get('message', '')
    print(f"lppppp:{user_message}")
    # 处理用户消息
    response = engine.chat_with_deepseek(user_message)
    
    return jsonify({
        'response': response,
        #'history': engine.get_history()
    })

# @app.route('/clear', methods=['POST'])
# def clear_history():
#     engine.clear_history()
#     return jsonify({'status': 'success'})

if __name__ == '__main__':
    init_mfd_vector_db()
    app.run(debug=True, port=5000, use_reloader=False)