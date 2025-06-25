from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from camel_tools.morphology.analyzer import Analyzer
from camel_tools.tokenizers.word import simple_word_tokenize
from openai import OpenAI
import os

app = Flask(__name__)
CORS(app)

# Load Qur'an data preprocessed with roots
with open('quraan_rooted.json', 'r', encoding='utf-8') as f:
    quraan_data = json.load(f)

# Initialize CAMeL Analyzer
analyzer = Analyzer.builtin_analyzer()

# Set your OpenAI API key
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_morphology(word):
    analyses = analyzer.analyze(word)
    for entry in analyses:
        if 'root' in entry and 'pattern' in entry:
            return {
                'root_ar': entry['root'],
                'scale': entry['pattern'],
                'scale_type': entry['diac'],
            }
    return {
        'root_ar': '',
        'scale': '',
        'scale_type': ''
    }

def get_openai_translation(word, root):
    prompt = f"Translate this Arabic word and its root to English:\nWord: {word}\nRoot: {root}\nReturn JSON like {{'word_en': '', 'root_en': ''}}"
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        return {"word_en": "", "root_en": ""}

def search_root_in_quraan(root_letters):
    matched_verses = []
    root_occurrences = 0

    for entry in quraan_data:
        verse_text = entry['text']
        verse_root = entry.get('root')
        if verse_root == root_letters:
            root_occurrences += 1
            highlighted = ""
            for letter in verse_text:
                if letter in root_letters:
                    highlighted += f"<span class='root'>{letter}</span>"
                else:
                    highlighted += letter
            matched_verses.append(f"{entry['surah']}|{entry['ayah']}|{highlighted}")

    return matched_verses, root_occurrences

@app.route('/analyze', methods=['POST'])
def analyze_word():
    data = request.get_json()
    word = data.get('word', '').strip()

    if not word:
        return jsonify({"error": "No word provided"}), 400

    morphology = get_morphology(word)
    root_ar = morphology['root_ar']
    scale = morphology['scale']
    scale_type = morphology['scale_type']

    if not root_ar:
        return jsonify({"error": "Root could not be determined"}), 200

    translation = get_openai_translation(word, root_ar)
    word_en = translation.get('word_en', '')
    root_en = translation.get('root_en', '')

    # Highlight root letters in the input word
    root_letters_set = set(root_ar)
    word_colored = ""
    for ch in word:
        if ch in root_letters_set:
            word_colored += f"<span class='root'>{ch}</span>"
        else:
            word_colored += f"<span class='extra'>{ch}</span>"

    verses, root_occurrences = search_root_in_quraan(root_ar)

    return jsonify({
        "root_ar": " ".join(root_ar),
        "root_en": root_en,
        "root_occurrences": root_occurrences,
        "scale": scale,
        "scale_type": scale_type,
        "verses": verses,
        "word_colored": word_colored,
        "word_en": word_en
    })

if __name__ == '__main__':
    app.run(debug=True)
