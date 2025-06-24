from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # This will allow CORS for all domains by default
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI
import re

app = Flask(__name__)
CORS(app)

# Initialize OpenAI client with API key from Render environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load Qur'an once when the server starts
with open("quraan.txt", "r", encoding="utf-8") as f:
    quran_lines = f.readlines()


def highlight_root(word, root):
    highlighted = ""
    for char in word:
        if char in root:
            highlighted += f"<span class='root'>{char}</span>"
        else:
            highlighted += f"<span class='extra'>{char}</span>"
    return highlighted


def find_verses_with_root(root_letters):
    found_verses = []
    count = 0
    root_pattern = f"[{''.join(root_letters)}]"

    for line in quran_lines:
        if all(letter in line for letter in root_letters):
            count += 1
            # Highlight root letters
            highlighted_line = ""
            for char in line:
                if char in root_letters:
                    highlighted_line += f"<span class='root'>{char}</span>"
                else:
                    highlighted_line += char
            found_verses.append(highlighted_line.strip())
        if len(found_verses) >= 3:
            break

    return count, found_verses


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    word = data.get("word", "").strip()

    if not word:
        return jsonify({"error": "No word provided."}), 400

    try:
        # Step 1: Use OpenAI to analyze the word
        prompt = f"""
أنت خبير في الصرف العربي واللغويات. حلل الكلمة التالية: "{word}".

أعطني النتائج بصيغة JSON فقط (لا تشرح، فقط JSON)، ويجب أن تحتوي على:
- root_ar: الجذر العربي (مثلاً: ك ت ب)
- root_en: ترجمة الجذر (مثلاً: to write)
- word_en: معنى الكلمة بالإنجليزية
- scale: الوزن الصرفي (مثلاً: يَفْعَلُ)
- scale_type: نوع الوزن (مثلاً: فعل مجرد، صيغة مبالغة، اسم مكان)
- word_colored: الكلمة بعد تمييز الجذر باللون الأحمر داخل <span class='root'> والباقي في <span class='extra'>
        """

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        result_raw = response.choices[0].message.content.strip()
        import json
        result = json.loads(result_raw)

        # Step 2: Extract root letters
        root_letters = result.get("root_ar", "").replace(" ", "")
        root_letter_list = list(root_letters)

        # Step 3: Search quraan.txt for root occurrences
        occurrence_count, matched_verses = find_verses_with_root(root_letter_list)

        result["root_occurrences"] = occurrence_count
        result["verses"] = matched_verses

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
