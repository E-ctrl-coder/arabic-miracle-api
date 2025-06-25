from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from openai import OpenAI
import os
import re

app = Flask(__name__)
CORS(app)

with open('quraan_rooted.json', 'r', encoding='utf-8') as f:
    quraan_data = json.load(f)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def highlight_root_letters(text, root_letters):
    highlighted = ""
    root_set = set(root_letters)
    for ch in text:
        if ch in root_set:
            highlighted += f"<span class='root'>{ch}</span>"
        else:
            highlighted += ch
    return highlighted

@app.route('/analyze', methods=['POST'])
def analyze_word():
    data = request.get_json()
    word = data.get('word', '').strip()

    if not word:
        return jsonify({"error": "No word provided"}), 400

    # Ask OpenAI for root, scale, and translation
    prompt = (
        f"Given this Arabic word: {word}\n"
        "Please provide JSON with the root letters, morphological scale, and English translations "
        "in this format:\n"
        '{"root_ar": "root letters", "scale": "scale pattern", "scale_type": "type", '
        '"word_en": "word translation", "root_en": "root translation"}'
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        ai_response = response.choices[0].message.content
        analysis = json.loads(ai_response)
    except Exception as e:
        return jsonify({"error": "OpenAI request failed", "details": str(e)}), 500

    root_ar = analysis.get("root_ar", "").replace(" ", "")
    scale = analysis.get("scale", "")
    scale_type = analysis.get("scale_type", "")
    word_en = analysis.get("word_en", "")
    root_en = analysis.get("root_en", "")

    if not root_ar:
        return jsonify({"error": "Root not found in OpenAI response"}), 200

    # Search in quraan data for verses with this root
    verses = []
    root_occurrences = 0
    for entry in quraan_data:
        if entry.get("root", "") == root_ar:
            root_occurrences += 1
            verse_text = highlight_root_letters(entry['text'], root_ar)
            verses.append(f"{entry['surah']}|{entry['ayah']}|{verse_text}")

    # Highlight root letters in the input word
    word_colored = highlight_root_letters(word, root_ar)

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

if __name__ == "__main__":
    app.run(debug=True)
