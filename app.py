import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load word_roots.json from the same directory as this script
here = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(here, "word_roots.json")
print(f"▶️ Loading JSON from {json_path}")
with open(json_path, encoding="utf-8") as f:
    root_lookup = json.load(f)
print(f"✅ Loaded {len(root_lookup)} entries")

@app.route("/debug/keys", methods=["GET"])
def debug_keys():
    # Return the first 20 keys so you can inspect what's in your JSON
    sample = list(root_lookup.keys())[:20]
    return jsonify({"sample_keys": sample})

@app.route("/", methods=["GET"])
def index():
    # Health-check
    return jsonify({
        "status": "up",
        "entries_loaded": len(root_lookup),
        "hint": "Use GET /analyze?word=… or POST /analyze"
    })

@app.route("/analyze", methods=["GET"])
def analyze_get():
    word = request.args.get("word", "").strip()
    if not word:
        return jsonify({"error": "No word provided"}), 400
    entry = root_lookup.get(word)
    if not entry:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"word": word, "data": entry})

@app.route("/analyze", methods=["POST"])
def analyze_post():
    data = request.get_json(silent=True) or {}
    word = data.get("word", "").strip()
    if not word:
        return jsonify({"error": "No word provided"}), 400
    entry = root_lookup.get(word)
    if not entry:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"word": word, "data": entry})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
