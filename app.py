from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from camel_tools.morphology.analyzer import Analyzer
from openai import OpenAI

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Load CAMeL Analyzer
analyzer = Analyzer.builtin_analyzer('calima-msa')

# Load Qur'an root-based data
with open('quraan_rooted.json', 'r', encoding='utf-8') as f:
    quraan_data = json.load(f)

# OpenAI setup
client = OpenAI()
openai_model = "gpt-4"  # You can change this to "gpt-3.5-turbo" if needed

def get_analysis(word):
    analyses = analyzer.analyze(word)
    if not analyses:
        return None

    # Pick the first valid analysis
    first = analyses[0]
    root = first.get('root', '')
    pattern = first.get('pattern', '')
    pos = first.get('pos', '')
    return {
        'root': root,
        'pattern': pattern,
        'pos': pos
    }

def highlight_root(word, root):
    highlighted = ""
    used = [False] * len(word)
    for r in root:
        for i, c in enumerate(word):
            if not used[i] and c == r:
                highlighted += f"<span style='color:red;font-weight:bold'>{c}</span>"
                used[i] = True
                break
        else:
            highlighted += f"<span style='color:gray'>{r}</span>"
    return highlighted

def search_quran_by_root(root):
    if root in quraan_data:
        matches = quraan_data[root]
        count = len(matches)
        verses = []
        for entry in matches:
            surah = entry['surah']
            ayah = entry['ayah']
            text = entry['text']
            for letter in root:
                text = text.replace(letter, f"<span style='color:red;font-weight:bold'>{letter}</span>")
            verses.append({
                "surah": surah,
                "ayah": ayah,
                "text": text
            })
        return {
            "count": count,
            "verses": verses
        }
    else:
        return {
            "count": 0,
            "verses": []
        }

def translate_word(word, root):
    prompt = f"Translate the Arabic word '{word}' and its root '{root}' into English. Give short, clear meanings."
    response = client.chat.completions.create(
        model=openai_model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

@app.route('/analyze', methods=['POST'])
def analyze_word():
    data = request.get_json()
    word = data.get('word', '').strip()

    if not word:
        return jsonify({"error": "No word provided"}), 400

    analysis = get_analysis(word)
    if not analysis:
        return jsonify({"error": "Word analysis failed"}), 404

    root = analysis['root']
    pattern = analysis['pattern']
    pos = analysis['pos']

    quran_result = search_quran_by_root(root)
    translation = translate_word(word, root)
    root_highlighted = highlight_root(word, root)

    return jsonify({
        "word": word,
        "root": root,
        "pattern": pattern,
        "pos": pos,
        "translation": translation,
        "highlighted_word": root_highlighted,
        "quran_matches": quran_result
    })

# For health check
@app.route('/')
def home():
    return "Arabic Word Analyzer API is running."

