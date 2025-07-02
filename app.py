import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)   # allow all origins—your React UI can call this

# 1) Load word_roots.json
here = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(here, "word_roots.json")
print(f"▶️ Loading JSON from {json_path}")
try:
    with open(json_path, encoding="utf-8") as f:
        root_lookup = json.load(f)
    print(f"✅ Loaded {len(root_lookup)} entries")
except Exception as e:
    print(f"❌ Failed to load JSON: {e}")
    root_lookup = {}

# 2) Index route for health check
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "up",
        "entries_loaded": len(root_lookup),
        "message": "POST to /analyze with JSON {word:…} or GET /analyze?word=…"
    })

# 3) POST /analyze — your main lookup
@app.route("/analyze", methods=["POST"])
def analyze_post():
    data = request.get_json(silent=True)
    word = (data or {}).get("word", "").strip()
    if not word:
        return jsonify({"error": "No word provided"}), 400

    entry = root_lookup.get(word)
    if not entry:
        return jsonify({"error": "Not found"}), 404

    return jsonify({"word": word, "data": entry})

# 4) GET /analyze — for quick browser tests
@app.route("/analyze", methods=["GET"])
def analyze_get():
    word = request.args.get("word", "").strip()
    if not word:
        return jsonify({"message":"Use ?word=… or POST JSON body"}), 200

    entry = root_lookup.get(word)
    if not entry:
        return jsonify({"error":"Not found"}), 404

    return jsonify({"word": word, "data": entry})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
