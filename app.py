from flask import Flask, request, jsonify
from googlesearch import search
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def get_wiki_style_descriptions(query, num=3):
    print(f"🔎 Результаты поиска по запросу '{query}':\n")
    titlelist = []
    try:
        urls = list(search(query, num_results=num, lang="ru"))
        for url in urls:
            try:
                response = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Заголовок
                title = soup.title.string if soup.title else "Нет заголовка"
                
                # Описание в стиле Википедии (ищем первый абзац или мета-описание)
                description = ""
                
                # Способ 1: Мета-описание
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc:
                    description = meta_desc["content"][:200]
                    if len(meta_desc["content"]) > 200:
                        description += "..."
                else:
                    # Способ 2: Первый абзац статьи (<p>)
                    first_p = soup.find("p")
                    if first_p:
                        description = first_p.get_text().strip()[:200] + "..."  # Ограничиваем длину
                titlelist.append([url, title, description])
                
            except Exception as e:
                titlelist.append(f"⚠️ Ошибка при обработке {url}: {str(e)[:50]}...\n")
                
    except Exception as e:
        titlelist.append(f"🚫 Ошибка поиска: {e}")
    return titlelist

@app.route('/test')
def search_test():
    test = get_wiki_style_descriptions("пельмени", num=5)
    return jsonify(test), 200

if __name__ == '__main__':    
    app.run(debug=True, host='0.0.0.0', port=5000)
