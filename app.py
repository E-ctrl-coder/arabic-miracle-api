import os
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 1) Load the raw JSON lookup
here = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(here, "word_roots.json")
print(f"▶️ Loading JSON from {json_path}")
with open(json_path, encoding="utf-8") as f:
    raw_lookup = json.load(f)
print(f"✅ Loaded {len(raw_lookup)} entries")

# 2) Build a normalized (diacritic‐free) lookup
def normalize(text: str) -> str:
    # remove Arabic diacritics (tashkeel)
    text = re.sub(r"[ًٌٍَُِّْ]", "", text)
    # optionally unify alef forms etc. (uncomment if needed)
    # text = re.sub(r"[إأآا]", "ا", text)
    # text = text.replace("ؤ", "و").replace("ئ", "ي")
    return text

norm_lookup = {}
for key, data in raw_lookup.items():
    nk = normalize(key)
    # keep the first entry for each normalized form
    if nk not in norm_lookup:
        norm_lookup[nk] = data
print(f"✅ Built normalized lookup with {len(norm_lookup)} keys")

# 3) Debug endpoint to inspect raw keys
@app.route("/debug/keys", methods=["GET"])
def debug_keys():
    sample = list(raw_lookup.keys())[:20]
    return jsonify({"sample_keys": sample})

# 4) Health check
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "up",
        "raw_entries": len(raw_lookup),
        "normalized_entries": len(norm_lookup),
        "hint": "GET /analyze?word=… or POST /analyze"
    })

# 5) Lookup logic for GET
@app.route("/analyze", methods=["GET"])
def analyze_get():
    word = request.args.get("word", "").strip()
    if not word:
        return jsonify({"error": "No word provided"}), 400

    # try raw first, then normalized
    entry = raw_lookup.get(word) or norm_lookup.get(normalize(word))
    if not entry:
        return jsonify({"error": "Not found"}), 404

    return jsonify({"word": word, "data": entry})

# 6) Same for POST
@app.route("/analyze", methods=["POST"])
def analyze_post():
    data = request.get_json(silent=True) or {}
    word = (data.get("word") or "").strip()
    if not word:
        return jsonify({"error": "No word provided"}), 400

    entry = raw_lookup.get(word) or norm_lookup.get(normalize(word))
    if not entry:
        return jsonify({"error": "Not found"}), 404

    return jsonify({"word": word, "data": entry})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
