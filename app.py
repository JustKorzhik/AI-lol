from flask import Flask, request, jsonify, Response
import aiohttp
import asyncio
from functools import wraps
import json
import time
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
executor = ThreadPoolExecutor()

def async_route(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(f(*args, **kwargs))
            return result
        finally:
            loop.close()
    return wrapper

async def get_chute_response_async(prompt):
    config = {
        "api_url": "https://llm.chutes.ai/v1/chat/completions",
        "api_token": "cpk_87c1ab80f98d4d4a9d019ece666385a9.a6d88321b7935a319035a323a1ae2a18.FX6HxQeeUOGEJqRicmakDXPvO4X1vy7a",
        "model": "deepseek-ai/DeepSeek-V3-0324",
        "temperature": 0.8,
        "max_tokens": 10240,
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {config['api_token']}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "model": config["model"],
        "messages": [{"role": "user", "content": prompt}, {"role": "system", "content": "используй форматирование майнкрафта со знаком &"}],
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"],
        "stream": config["stream"]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                config["api_url"],
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                response_data = await response.read()
                data = json.loads(response_data.decode('utf-8'))
                
                if response.status != 200:
                    error_msg = data.get("error", {}).get("message", "Unknown error")
                    return {"error": f"API error: {response.status} - {error_msg}"}

                content = data.get("choices", [{}])[0].get("message", {}).get("content", "No response")
                return content

    except asyncio.TimeoutError:
        return {"error": "API request timed out"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def get_chute_response(prompt):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_chute_response_async(prompt))
    finally:
        loop.close()

@app.route('/ai', methods=['POST'])
def ai():
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"error": "Prompt is required in JSON body"}), 400

        # Запускаем запрос в отдельном потоке
        future = executor.submit(get_chute_response, data['prompt'])
        
        # Ждем до 2 секунд для быстрого ответа
        start_time = time.time()
        try:
            response = future.result(timeout=2)
            # Если ответ получен быстро, возвращаем его сразу
            nickname = data.get('nickname', '')
            if nickname and isinstance(response, str):
                response = f"{response}\n\n— {nickname}"
            return Response(response, content_type='text/plain; charset=utf-8', status=200)
        except TimeoutError:
            # Если ответ не получен за 2 секунды, возвращаем 200 и продолжаем обработку
            def generate():
                # Ждем завершения запроса
                response = future.result()
                if isinstance(response, dict) and 'error' in response:
                    yield json.dumps(response)
                else:
                    nickname = data.get('nickname', '')
                    if nickname and isinstance(response, str):
                        response = f"{response}\n\n— {nickname}"
                    yield response

            return Response(
                generate(),
                content_type='text/plain; charset=utf-8',
                status=200
            )

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
