from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests (for Netlify frontend)

@app.route('/', methods=['GET'])
def index():
    return "Hello World"

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    word = data.get('word', '')

    # MOCK analysis result (replace with real logic later)
    response = {
        "word": word,
        "root": "ف ع ل",
        "meaning_ar": "عمل",
        "meaning_en": "to do / act",
        "quran_count": 45,
        "examples": [
            {"ayah": "فَعَلَ اللَّهُ ذَٰلِكَ", "translation": "Allah did that"},
        ],
        "highlight": {
            "root": [0, 3],
            "prefix": [0, 0],
            "suffix": [3, 3]
        }
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)  # Required for Render
