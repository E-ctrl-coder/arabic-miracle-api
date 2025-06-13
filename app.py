from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Dummy data for demonstration
ROOTS_DB = {
    "أكل": {
        "root": "أ ك ل",
        "translation": "to eat",
        "highlight": {
            "root": [0, 2],
            "prefix": [],
            "suffix": []
        },
        "examples": [
            {"ayah": "فَعَلَ اللَّهُ ذَٰلِكَ", "translation": "Allah did that"}
        ]
    },
    "كتب": {
        "root": "ك ت ب",
        "translation": "to write",
        "highlight": {
            "root": [0, 2],
            "prefix": [],
            "suffix": []
        },
        "examples": [
            {"ayah": "كُتِبَ عَلَيْكُمُ الصِّيَامُ", "translation": "Fasting is prescribed for you"}
        ]
    }
}

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    word = data.get("word", "").strip()

    if not word:
        return jsonify({"error": "No word provided."}), 400

    analysis = ROOTS_DB.get(word)

    if not analysis:
        return jsonify({
            "root": "",
            "translation": "Not found",
            "highlight": {},
            "examples": []
        })

    return jsonify(analysis)

if __name__ == "__main__":
    app.run(debug=True)
