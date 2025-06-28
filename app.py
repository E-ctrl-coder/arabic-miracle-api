import os
import re
import json
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

# --- Configuration ---
# Path to the Alkhaleel CLI executable (make sure this name matches your uploaded binary)
ALKHALEEL_CMD = os.path.join(os.path.dirname(__file__), "alkhalil")

# Load Quran data once at startup
BASE = os.path.dirname(__file__)
with open(os.path.join(BASE, 'quraan_rooted.json'), 'r', encoding='utf-8') as f:
    quraan_data = json.load(f)
with open(os.path.join(BASE, 'quraan.txt'), 'r', encoding='utf-8') as f:
    quraan_lines = f.readlines()

# OpenAI config
openai.api_key = os.getenv("OPENAI_API_KEY")


# --- Utility Functions ---
def normalize_arabic(text):
    text = re.sub(r'[ًٌٍَُِّْـ]', '', text)
    text = re.sub(r'[إأآ]', 'ا', text)
    text = re.sub(r'[ؤئ]', 'ء', text)
    text = re.sub(r'ة', 'ه', text)
    return text

def analyze_with_cli(word):
    """
    Calls the Alkhaleel CLI binary and parses its output.
    Raises FileNotFoundError if the binary is missing,
           subprocess.CalledProcessError if the CLI returns non-zero.
    """
    proc = subprocess.run(
        [ALKHALEEL_CMD, word],
        capture_output=True, text=True, check=True
    )
    lines = proc.stdout.strip().splitlines()
    analyses = []
    for line in lines:
        parts = line.split()
        if len(parts) < 3:
            continue
        analyses.append({
            "root": parts[0],
            "pattern": parts[1],
            "pos": parts[2],
            "raw": line
        })
    return analyses

def highlight_root(verse, root):
    result, letters = '', list(root)
    for ch in verse:
        if ch in letters:
            result += f'<span style="color:red;font-weight:bold;">{ch}</span>'
            letters.remove(ch)
        else:
            result += ch
    return result


# --- Routes ---
@app.route('/analyze', methods=['POST'])
def analyze_word():
    data = request.get_json() or {}
    word = data.get('word', '').strip()
    if not word:
        return jsonify({'error': 'No word provided'}), 400

    normalized = normalize_arabic(word)

    # 1) Run CLI analysis, catch binary/mis-named errors
    try:
        results = analyze_with_cli(normalized)
    except FileNotFoundError:
        return jsonify({'error': f'Alkhaleel CLI not found at {ALKHALEEL_CMD}'}), 500
    except subprocess.CalledProcessError as e:
        return jsonify({
            'error': 'Alkhaleel analysis failed',
            'details': e.stderr.strip() or str(e)
        }), 500

    if not results:
        return jsonify({'error': 'Could not parse the word with Alkhaleel'}), 400

    best = results[0]
    root, pattern, pos = best['root'], best['pattern'], best['pos']

    # 2) Translate with OpenAI
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a translator of Arabic to English."},
                {"role": "user",
                 "content": f"What is the English meaning of the Arabic word '{word}' and its root '{root}'?"}
            ]
        )
        translation = resp.choices[0].message.content.strip()
    except Exception as e:
        translation = f"Translation error: {e}"

    # 3) Gather Quran occurrences
    occs = quraan_data.get(root, [])
    formatted = [
        {
            'surah': o['surah'],
            'ayah': o['ayah'],
            'text': highlight_root(o['text'], root)
        }
        for o in occs
    ]

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


# --- Global JSON Error Handler ---
@app.errorhandler(Exception)
def handle_all_errors(e):
    # Logs full traceback into your Render logs
    app.logger.error("Unhandled Exception", exc_info=e)
    return jsonify({
        'error': f'{e.__class__.__name__}: {e}'
    }), 500


@app.route('/')
def home():
    return "Arabic Miracle backend is running."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
