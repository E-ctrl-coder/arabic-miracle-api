from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

# Make sure you set your OpenAI API key in an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    word = data.get("word", "").strip()

    if not word:
        return jsonify({"error": "No word provided."}), 400

    try:
        prompt = f"""
You are an expert Arabic linguist and Qur'an scholar. Given the Arabic word "{word}", return a JSON object with the following fields:
- root: the triliteral root of the word
- meaning_ar: short Arabic meaning
- meaning_en: short English meaning
- quran_count: number of times this root appears in the Qur'an
- highlight: object with prefix [start, end], root [start, end], suffix [start, end] — all based on character positions in the word
- examples: array of max 2 Qur'anic ayahs that contain the word or its root, each with `ayah` and `translation`
- word: return the input word

Output ONLY valid JSON.
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful Arabic language analysis assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

        content = response.choices[0].message["content"]
        return jsonify(eval(content))  # NOTE: Safe only if content is guaranteed to be JSON

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
