from flask import Flask, request, jsonify, Response
import aiohttp
import asyncio
import json

app = Flask(__name__)

@app.route('/')
def home():
    return "Сервер работает. Используйте POST /ai с JSON {'prompt':'ваш запрос'}"

async def get_chute_response(prompt):
    config = {
        "api_url": "https://llm.chutes.ai/v1/chat/completions",
        "api_token": "ваш_токен",  # замените на реальный токен
        "model": "deepseek-ai/DeepSeek-V3-0324",
        "temperature": 0.8,
        "max_tokens": 1024,
        "stream": False  # сначала сделаем без потокового вывода
    }

    headers = {
        "Authorization": f"Bearer {config['api_token']}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": config["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"],
        "stream": config["stream"]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(config["api_url"], headers=headers, json=payload) as response:
                if response.status != 200:
                    error_msg = await response.text()
                    return {"error": f"API error: {response.status} - {error_msg}"}

                data = await response.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "No response")

    except Exception as e:
        return {"error": str(e)}

@app.route('/ai', methods=['POST'])
async def ai():
    try:
        # Проверяем Content-Type
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()

        # Проверяем наличие prompt
        if not data or 'prompt' not in data:
            return jsonify({"error": "Prompt is required in JSON body"}), 400

        # Получаем ответ от API
        response = await get_chute_response(data['prompt'])

        # Обрабатываем ошибки
        if isinstance(response, dict) and 'error' in response:
            return jsonify(response), 500

        return jsonify({"response": response})

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
