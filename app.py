from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import json

# Load preprocessed Qur'an data
with open('quraan_rooted.json', 'r', encoding='utf-8') as f:
    quran_data = json.load(f)

app = Flask(__name__)
CORS(app)

# Set OpenAI API key from environment
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    word = data.get("word", "").strip()

    if not word:
        return jsonify({"error": "No word provided"}), 400

    # Ask OpenAI for root, scale, type, and translation
    prompt = (
    f"Analyze the Arabic word: {word}\n"
    f"Return the following:\n"
    f"- Root (in Arabic)\n"
    f"- Scale/Pattern (الوزن)\n"
    f"- Type (e.g. noun, verb)\n"
    f"- English translation of the word\n"
    f"- English translation of the root"
)


    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        reply = response.choices[0].message.content.strip()

        # Extract data from OpenAI reply
        lines = reply.splitlines()
        extracted = {
            "word": word,
            "root": "",
            "scale": "",
            "type": "",
            "word_translation": "",
            "root_translation": ""
        }

        for line in lines:
            if "Root" in line:
                extracted["root"] = line.split(":")[-1].strip()
            elif "Scale" in line or "Pattern" in line or "الوزن" in line:
                extracted["scale"] = line.split(":")[-1].strip()
            elif "Type" in line:
                extracted["type"] = line.split(":")[-1].strip()
            elif "translation of the word" in line.lower():
                extracted["word_translation"] = line.split(":")[-1].strip()
            elif "translation of the root" in line.lower():
                extracted["root_translation"] = line.split(":")[-1].strip()

        root = extracted["root"]

        # Find matches in the Qur'an
        matches = [
            verse for verse in quran_data if root and root in verse.get("roots", [])
        ]

        extracted["matches"] = matches
        extracted["count"] = len(matches)

        return jsonify(extracted)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
