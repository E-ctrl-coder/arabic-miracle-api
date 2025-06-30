from flask import Flask, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# Load the preprocessed root data
with open("word_roots.json", "r", encoding="utf-8") as f:
    root_lookup = json.load(f)

@app.route("/")
def index():
    return "✅ Arabic Miracle API is running."

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    word = data.get("word")
    if not word:
        return jsonify({"error": "Missing 'word' in request."}), 400

    result = root_lookup.get(word)
    if result:
        return jsonify({
            "word": word,
            "root": result.get("root"),
            "pattern": result.get("pattern"),
            "lemma": result.get("lemma"),
            "prefix": result.get("prefix"),
            "suffix": result.get("suffix")
        })
    else:
        return jsonify({"error": f"'{word}' not found in dataset."}), 404
