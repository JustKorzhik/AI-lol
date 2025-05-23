from flask import Flask, request, jsonify, Response
import aiohttp
import asyncio
from functools import wraps
import json

app = Flask(__name__)

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

async def get_chute_response(prompt):
    config = {
        "api_url": "https://llm.chutes.ai/v1/chat/completions",
        "api_token": "cpk_87c1ab80f98d4d4a9d019ece666385a9.a6d88321b7935a319035a323a1ae2a18.FX6HxQeeUOGEJqRicmakDXPvO4X1vy7a",
        "model": "deepseek-ai/DeepSeek-V3-0324",
        "temperature": 0.8,
        "max_tokens": 1024,
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {config['api_token']}",
        "Content-Type": "application/json",
        "Accept": "application/json"
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

@app.route('/ai', methods=['POST'])
@async_route
async def ai():
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"error": "Prompt is required in JSON body"}), 400

        response = await get_chute_response(data['prompt'])

        if isinstance(response, dict) and 'error' in response:
            return jsonify(response), 500

        nickname = data.get('nickname', '')
        if nickname:
            response = f"{response}\n\n— {nickname}"

        return Response(
            response,
            content_type='text/plain; charset=utf-8',
            status=200
        )

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
