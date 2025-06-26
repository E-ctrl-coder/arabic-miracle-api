from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from camel_tools.morphology.analyzer import Analyzer
from camel_tools.utils.charmap import CharMapper
import openai

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# OpenAI API key from environment
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Load preprocessed Qur'an data
with open("quraan_rooted.json", "r", encoding="utf-8") as f:
    quraan_data = json.load(f)

# Initialize CAMeL analyzer (default MLE)
analyzer = Analyzer.builtin_analyzer('calima-msa')

# Remove diacritics for better matching
strip_diacritics = CharMapper.builtin_mapper('arclean')

@app.route("/analyze", methods=["POST"])
def analyze_word():
    data = request.get_json()
    input_word = data.get("word", "").strip()

    if not input_word:
        return jsonify({"error": "No word provided"}), 400

    clean_word = strip_diacritics.map_string(input_word)

    # Analyze word with CAMeL
    analyses = analyzer.analyze(clean_word)
    if not analyses:
        return jsonify({"error": "No analysis found"}), 404

    # Pick first valid analysis
    analysis = analyses[0]
    root = analysis.get("root", "")
    pattern = analysis.get("pattern", "")
    pos = analysis.get("pos", "")
    stem = analysis.get("stem", "")

    # Use OpenAI to translate word and root
    try:
        messages = [
            {"role": "system", "content": "Translate Arabic words into English. Be concise."},
            {"role": "user", "content": f"What is the English meaning of the Arabic word '{input_word}' and its root '{root}'?"}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.2,
        )
        english_translation = response.choices[0].message.content.strip()
    except Exception as e:
        english_translation = f"Translation failed: {e}"

    # Search Qur'an data for root
    root_matches = quraan_data.get(root, [])

    # Highlight root letters inside words
    def highlight_root_letters(word, root_letters):
        highlight = ""
        root_set = set(root_letters)
        for letter in word:
            if letter in root_set:
                highlight += f"<span style='color:red;font-weight:bold'>{letter}</span>"
                root_set.remove(letter)  # remove once to avoid duplicate match
            else:
                highlight += f"<span style='color:gray'>{letter}</span>"
        return highlight

    highlighted_examples = []
    for match in root_matches:
        verse = match["verse"]
        word_in_verse = match["word"]
        highlighted_word = highlight_root_letters(word_in_verse, list(root))
        highlighted_examples.append({
            "verse": verse,
            "word": word_in_verse,
            "highlighted": highlighted_word
        })

    result = {
        "input_word": input_word,
        "cleaned_word": clean_word,
        "root": root,
        "stem": stem,
        "pattern": pattern,
        "pos": pos,
        "english_translation": english_translation,
        "quran_occurrences": len(root_matches),
        "quran_examples": highlighted_examples
    }

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
