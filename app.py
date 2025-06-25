from flask import Flask, request, jsonify
from flask_cors import CORS
from camel_tools.tokenizers.word import simple_word_tokenize
from camel_tools.morphology.analyzer import Analyzer
from openai import OpenAI
import json
import os

app = Flask(__name__)
CORS(app)

openai_client = OpenAI()
analyzer = Analyzer.builtin_analyzer()

# Load preprocessed Qur'an data
with open('quraan_rooted.json', encoding='utf-8') as f:
    quraan_data = json.load(f)

def analyze_word(word):
    analyses = analyzer.analyze(word)
    if not analyses:
        return {}

    best = analyses[0]
    root = best.get('root', '')
    pattern = best.get('pattern', '')
    pos = best.get('pos', '')
    return {
        'root': root,
        'scale': pattern,
        'scale_type': pos,
        'analysis': best
    }

def highlight_root(word, root):
    highlighted = ''
    root_letters = set(root)
    for char in word:
        if char in root_letters:
            highlighted += f"<span class='root'>{char}</span>"
        else:
            highlighted += f"<span class='extra'>{char}</span>"
    return highlighted

def find_verses_with_root(root):
    matches = []
    for verse in quraan_data:
        for word, w_root in verse['roots']:
            if root and w_root and root == w_root:
                text = verse['text']
                for char in root:
                    text = text.replace(char, f"<span class='root'>{char}</span>")
                matches.append(f"{verse['surah']}|{verse['ayah']}|{text}")
                break
    return matches

def get_english_translation(word):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": f"Translate the Arabic word '{word}' to English and explain briefly."}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Translation unavailable."

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    word = data.get('word', '')
    if not word:
        return jsonify({'error': 'No word provided'}), 400

    result = analyze_word(word)
    if not result.get('root'):
        return jsonify({'error': 'No root found'}), 404

    root = result['root']
    verses = find_verses_with_root(root)
    translation = get_english_translation(word)
    root_translation = get_english_translation(root)

    return jsonify({
        'root_ar': ' '.join(root),
        'root_en': root_translation,
        'root_occurrences': len(verses),
        'scale': result['scale'],
        'scale_type': result['scale_type'],
        'verses': verses,
        'word_colored': highlight_root(word, root),
        'word_en': translation
    })

if __name__ == '__main__':
    app.run(debug=True)
