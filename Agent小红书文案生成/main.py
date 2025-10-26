
from flask import Flask, request, jsonify
from conversation import ConversationEngine
from glob import glob
from vector_db import LocalMilvusDB
from tqdm import tqdm
from utils import embedding_model, emoji_mapping
from vector_db import db

import product_chunker  

app = Flask(__name__)
engine = ConversationEngine("conversation.log")

def chunk_product_information(): 
    chunker = product_chunker.ProductChunker("./doc/product_information.json", "./doc/chunked_product_information.json")
     # 执行chunking
    chunks = chunker.chunk_by_product()
    
    if not chunks:
        print("❌ chunking失败，请检查输入文件")
        return

    chunker.print_chunks_as_json(chunks)

    # 保存chunks到文件
    if chunker.save_chunks_to_file(chunks):
        print("分块信息成功保存至: ./doc/chunked_product_information.json")
    else:
        print("分块信息保存失败！")

    return chunks        


def init_product_vector_db():
    print("即将从json文件内处理文本分块嵌入")
    chunks = chunk_product_information()

    text_chunks = [chunk["product_name"] for chunk in chunks]
    content_chunks = [chunk["content"] for chunk in chunks]
    print(f"准备为 {len(text_chunks)} 个文本块生成向量嵌入。内容是：{text_chunks}")
    #print(contents)
    #print("\n")
    data = []
    collection_name = "product_information"

    doc_embeddings = embedding_model.encode_documents(text_chunks)
    embedding_dim = len(doc_embeddings[0])
    print(f"第一个元素的维度是 {embedding_dim}\n")
    print(f"向量编码模型的默认维度是 {embedding_model.dim}\n")

    for i, line in enumerate(tqdm(text_chunks, desc="Creating embeddings")):
        data.append({"id": i, "vector": doc_embeddings[i], "text": content_chunks[i]})

    if not db.create_collection(collection_name, embedding_dim) :
        print("初始化数据库失败")
        exit(1)   

    if not db.insert(collection_name, data):
        print("插入产品信息到向量数据库失败")
        exit(1)
    
    emotion_list = [key for key in emoji_mapping.keys()]
    emoji_list = [value for value in emoji_mapping.values()]
    print(f"emotion: {emotion_list}, emoji: {emoji_list}")

    emotion_enbed = embedding_model.encode_documents(emotion_list)
    embedding_dim = len(emotion_enbed[0])
    print(f"第一个情绪元素的维度是 {embedding_dim}\n")
    print(f"向量编码模型的默认维度是 {embedding_model.dim}\n")

    emoji_data = []
    emoji_collection_name = "emotion2emoji"    
    for i, line in enumerate(tqdm(emotion_list, desc="Creating embeddings")):
        emoji_data.append({"id": i, "vector": emotion_enbed[i], "text": emoji_list[i]})

    if not db.create_collection(emoji_collection_name, embedding_dim) :
        print("初始化数据库失败")
        exit(1)   

    if not db.insert(emoji_collection_name, emoji_data):
        print("插入产品信息到向量数据库失败")
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
    response = engine.generate_rednote_by_single_chat(user_message)
    
    return jsonify({
        'response': response,
        #'history': engine.get_history()
    })

# @app.route('/clear', methods=['POST'])
# def clear_history():
#     engine.clear_history()
#     return jsonify({'status': 'success'})

if __name__ == '__main__':
    init_product_vector_db()
    app.run(debug=True, port=5000, use_reloader=False)