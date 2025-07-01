import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load word_roots.json from the same directory as this script
here = os.path.dirname(__file__)
json_path = os.path.join(here, "word_roots.json")
with open(json_path, encoding="utf-8") as f:
    root_lookup = json.load(f)

@app.route("/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(silent=True, force=True) or {}
    word = payload.get("word", "").strip()
    if not word:
        return jsonify({"error": "No word provided"}), 400

    entry = root_lookup.get(word)
    if not entry:
        return jsonify({"error": "Word not found"}), 404

    return jsonify({
        "word": word,
        "data": entry
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
