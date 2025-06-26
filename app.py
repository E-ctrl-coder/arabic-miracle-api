from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from camel_tools.morphology.analyzer import Analyzer
from camel_tools.utils.charmap import CharMapper
from openai import OpenAI

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load OpenAI key
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Load Qur'an data (root-based)
with open("quraan_rooted.json", "r", encoding="utf-8") as f:
    quraan_data = json.load(f)

# Prepare analyzer
analyzer = Analyzer.builtin_analyzer('calima-msa')
strip_diacritics = CharMapper.builtin_mapper('arclean')

@app.route("/analyze", methods=["POST"])
def analyze_word():
    data = request.get_json()
    input_word = data.get("word", "").strip()

    if not input_word:
        return jsonify({"error": "No word provided"}), 400

    clean_word = strip_diacritics.map_string(input_word)
    analyses = analyzer.analyze(clean_word)
    if not analyses:
        return jsonify({"error": "No analysis found"}), 404

    analysis = analyses[0]
    root = analysis.get("root", "")
    pattern = analysis.get("pattern", "")
    pos = analysis.get("pos", "")
    stem = analysis.get("stem", "")

    # OpenAI for translation
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Translate Arabic words into English. Be concise."},
                {"role": "user", "content": f"What is the English meaning of the Arabic word '{input_word}' and its root '{root}'?"}
            ],
            temperature=0.2
        )
        english_translation = response.choices[0].message.content.strip()
    except Exception as e:
        english_translation = f"Translation failed: {str(e)}"

    # Search root in Qur'an data
    root_matches = quraan_data.get(root, [])

    def highlight_root(word, root_letters):
        result = ""
        used = set()
        for letter in word:
            if letter in root_letters and letter not in used:
                result += f"<span style='color:red;font-weight:bold'>{letter}</span>"
                used.add(letter)
            else:
                result += f"<span style='color:gray'>{letter}</span>"
        return result

    highlighted_examples = []
    for match in root_matches:
        verse = match["verse"]
        word_in_verse = match["word"]
        highlighted_word = highlight_root(word_in_verse, list(root))
        highlighted_examples.append({
            "verse": verse,
            "word": word_in_verse,
            "highlighted": highlighted_word
        })

    return jsonify({
        "input_word": input_word,
        "cleaned_word": clean_word,
        "root": root,
        "stem": stem,
        "pattern": pattern,
        "pos": pos,
        "english_translation": english_translation,
        "quran_occurrences": len(root_matches),
        "quran_examples": highlighted_examples
    })

if __name__ == "__main__":
    app.run(debug=True)
