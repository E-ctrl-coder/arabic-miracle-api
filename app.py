import os
import re
import json
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

# 1) Path to the Alkhaleel CLI executable (you must upload this binary)
ALKHALEEL_CMD = os.path.join(os.path.dirname(__file__), "alkhalil")

# 2) Arabic normalization function (strips diacritics, normalizes letters)
def normalize_arabic(text):
    text = re.sub(r'[ًٌٍَُِّْـ]', '', text)
    text = re.sub(r'[إأآ]', 'ا', text)
    text = re.sub(r'[ؤئ]', 'ء', text)
    text = re.sub(r'ة', 'ه', text)
    return text

# 3) Wrapper to call the CLI and parse its output
def analyze_with_cli(word):
    try:
        proc = subprocess.run(
            [ALKHALEEL_CMD, word],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError:
        return []
    lines = proc.stdout.strip().splitlines()
    analyses = []
    for line in lines:
        parts = line.split()
        if len(parts) < 3:
            continue
        root, pattern, pos = parts[0], parts[1], parts[2]
        analyses.append({
            "root": root,
            "pattern": pattern,
            "pos": pos,
            "raw": line
        })
    return analyses

# 4) Load Quran data
with open(os.path.join(os.path.dirname(__file__), 'quraan_rooted.json'), 'r', encoding='utf-8') as f:
    quraan_data = json.load(f)

with open(os.path.join(os.path.dirname(__file__), 'quraan.txt'), 'r', encoding='utf-8') as f:
    quraan_lines = f.readlines()

# 5) OpenAI config
openai.api_key = os.getenv("OPENAI_API_KEY")

# 6) Highlight root letters in red for display
def highlight_root(verse, root):
    result, letters = '', list(root)
    for ch in verse:
        if ch in letters:
            result += f'<span style="color:red;font-weight:bold;">{ch}</span>'
            letters.remove(ch)
        else:
            result += ch
    return result

# 7) Analyze endpoint
@app.route('/analyze', methods=['POST'])
def analyze_word():
    data = request.get_json() or {}
    word = data.get('word', '').strip()
    if not word:
        return jsonify({'error': 'No word provided'}), 400

    normalized = normalize_arabic(word)
    results = analyze_with_cli(normalized)
    if not results:
        return jsonify({'error': 'Could not analyze word'}), 400

    best = results[0]
    root, pattern, pos = best['root'], best['pattern'], best['pos']

    # Translate using OpenAI
    messages = [
        {"role": "system", "content": "You are a translator of Arabic to English."},
        {"role": "user", "content": f"What is the English meaning of the Arabic word '{word}' and its root '{root}'?"}
    ]
    try:
        resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        translation = resp.choices[0].message.content.strip()
    except:
        translation = "Translation not available."

    # Quranic occurrences
    occs = quraan_data.get(root, [])
    formatted = []
    for occ in occs:
        formatted.append({
            'surah': occ['surah'],
            'ayah': occ['ayah'],
            'text': highlight_root(occ['text'], root)
        })

    return jsonify({
        'word': word,
        'normalized': normalized,
        'root': root,
        'pattern': pattern,
        'pos': pos,
        'translation': translation,
        'quran_occurrences': formatted,
        'occurrence_count': len(occs)
    })

@app.route('/')
def home():
    return "Arabic Miracle backend is running."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
