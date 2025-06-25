from flask import Flask, request, jsonify
from flask_cors import CORS
from camel_tools.morphology.analyzer import Analyzer
import openai
import json
import os

app = Flask(__name__)
CORS(app)

# Load the preprocessed Qur'an dataset
with open('quraan_rooted.json', 'r', encoding='utf-8') as f:
    quraan_data = json.load(f)

# Load OpenAI key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize CAMeL analyzer
analyzer = Analyzer.pretrained()

def analyze_word(word):
    # Analyze Arabic word with CAMeL
    analyses = analyzer.analyze(word)
    if not analyses:
        return None

    best = analyses[0]
    root = best.get('root')
    if not root:
        return None

    root_letters = list(root)
    prefix = best.get('prefix', '')
    stem = best.get('stem', '')
    suffix = best.get('suffix', '')

    scale = best.get('pattern')
    scale_type = best.get('bw') or 'Unknown'

    # Build highlighted word
    word_colored = ""
    for letter in word:
        if letter in root_letters:
            word_colored += f"<span class='root'>{letter}</span>"
            root_letters.remove(letter)
        else:
            word_colored += f"<span class='extra'>{letter}</span>"

    return {
        "root_ar": " ".join(list(root)),
        "scale": scale or "Unknown",
        "scale_type": scale_type,
        "word_colored": word_colored,
        "raw_root": root
    }

def translate_with_openai(text):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Translate the Arabic word or root into English."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Translation error: {str(e)}"

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    word = data.get('word', '').strip()

    if not word:
        return jsonify({"error": "No word provided"}), 400

    camel_result = analyze_word(word)
    if not camel_result:
        return jsonify({"error": "Word analysis failed"}), 400

    raw_root = camel_result["raw_root"]

    # Find verses containing the exact root (not individual letters)
    verses = []
    for entry in quraan_data:
        if entry['root'] == raw_root:
            highlighted = entry['highlighted']
            verses.append(f"{entry['surah']}|{entry['ayah']}|{highlighted}")

    # Translate word and root
    word_en = translate_with_openai(word)
    root_en = translate_with_openai(raw_root)

    response = {
        "root_ar": camel_result["root_ar"],
        "root_en": root_en,
        "root_occurrences": len(verses),
        "scale": camel_result["scale"],
        "scale_type": camel_result["scale_type"],
        "verses": verses,
        "word_colored": camel_result["word_colored"],
        "word_en": word_en
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
