from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
from openai import OpenAI

app = Flask(__name__)
CORS(app)  # You can restrict origins here if you want later

# Initialize OpenAI client with your API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Utility to highlight root letters in text with <span> and CSS classes for color
def highlight_text(text, root_letters):
    def replacer(match):
        char = match.group(0)
        if char in root_letters:
            return f"<span class='root'>{char}</span>"
        return char
    # We use regex to replace all letters in root_letters with highlighted spans
    pattern = f"[{''.join(root_letters)}]"
    return re.sub(pattern, replacer, text)

# Load Quran text once on startup for fast lookup
with open("quraan.txt", encoding="utf8") as f:
    quran_lines = [line.strip() for line in f if line.strip()]

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    word = data.get("word", "").strip()
    if not word:
        return jsonify({"error": "No word provided."}), 400

    try:
        # Ask OpenAI to analyze the word: extract root, translation, scale, type, word translation, and color-coded HTML
        prompt = f"""
أنت خبير في اللغويات العربية والصرف القرآني.

حلل الكلمة العربية: "{word}"

أعطني:

1. جذر الكلمة (الحروف فقط) مع الترجمة الإنجليزية.
2. ترجمة الكلمة كاملة إلى الإنجليزية.
3. الوزن الصرفي (الميزان) للكلمة ونوعه.
4. أعطني الكلمة ملونة HTML بحيث يكون الجذر داخل <span class='root'>، والبادئة <span class='prefix'>، واللاحقة <span class='suffix'>، وأي زوائد <span class='extra'>.

أعطني الرد بصيغة JSON بهذا الشكل:
{{
  "root_ar": "ك ت ب",
  "root_en": "to write",
  "word_en": "they wrote",
  "scale": "فَعَّال",
  "scale_type": "فعل ماضٍ",
  "word_colored": "<span class='root'>ك</span><span class='root'>ت</span><span class='root'>ب</span><span class='extra'>وا</span>"
}}
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        ai_result = response.choices[0].message.content

        # Parse the AI response JSON safely
        import json
        try:
            ai_data = json.loads(ai_result)
        except json.JSONDecodeError:
            return jsonify({"error": "Failed to parse AI response JSON.", "ai_response": ai_result}), 500

        root_letters = ai_data["root_ar"].replace(" ", "")

        # Find verses in quraan.txt that contain any of the root letters
        matching_verses = []
        root_count = 0
        for line in quran_lines:
            # Check if line contains at least one root letter
            if any(letter in line for letter in root_letters):
                # Highlight root letters in verse
                highlighted_verse = highlight_text(line, root_letters)
                matching_verses.append(highlighted_verse)
                # Count occurrences of root letters in this verse
                root_count += sum(line.count(l) for l in root_letters)
            if len(matching_verses) >= 5:
                break

        result = {
            "root_ar": ai_data["root_ar"],
            "root_en": ai_data["root_en"],
            "word_en": ai_data["word_en"],
            "scale": ai_data["scale"],
            "scale_type": ai_data["scale_type"],
            "word_colored": ai_data["word_colored"],
            "root_occurrences": root_count,
            "verses": matching_verses,
        }
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # For local testing only, in production Render will handle hosting
    app.run(host="0.0.0.0", port=10000)
