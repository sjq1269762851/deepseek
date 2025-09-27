from flask import Flask, request, jsonify
from conversation import ConversationEngine

app = Flask(__name__)
engine = ConversationEngine("conversation.log")

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
    app.run(debug=True, port=5000)