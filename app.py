from flask import Flask, request, jsonify
from aiohttp import ClientSession
import asyncio

app = Flask(__name__)

# Конфигурация API Chutes
CHUTES_API_URL = "https://llm.chutes.ai/v1/chat/completions"
CHUTES_API_TOKEN = "cpk_87c1ab80f98d4d4a9d019ece666385a9.a6d88321b7935a319035a323a1ae2a18.FX6HxQeeUOGEJqRicmakDXPvO4X1vy7a"
MODEL_NAME = "deepseek-ai/DeepSeek-V3-0324"

async def make_chutes_request(messages, nickname):
    headers = {
        "Authorization": f"Bearer {CHUTES_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Добавляем nickname в контекст
    system_message = {
        "role": "system",
        "content": f"Пользователь известен как {nickname}. Учитывай это в ответах."
    }
    processed_messages = [system_message] + messages
    
    payload = {
        "model": MODEL_NAME,
        "messages": processed_messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    async with ClientSession() as session:
        async with session.post(CHUTES_API_URL, json=payload, headers=headers) as response:
            return await response.json()

@app.route('/ai', methods=['POST'])
async def ai_chat():
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        nickname = data.get('nickname', 'Друг')
        
        if not messages:
            return jsonify({"error": "Сообщения не предоставлены"}), 400
        
        # Асинхронный запрос к API
        response_data = await make_chutes_request(messages, nickname)
        
        if 'error' in response_data:
            return jsonify({"error": "Ошибка нейросети", "details": response_data}), 500
            
        return jsonify({
            "response": response_data,
            "nickname": nickname
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    from hypercorn.asyncio import serve
    from hypercorn.config import Config
    
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    
    asyncio.run(serve(app, config))
