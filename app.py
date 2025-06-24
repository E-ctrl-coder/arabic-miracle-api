from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI
import re

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load Quran once at startup
with open("quraan.txt", "r", encoding="utf-8") as f:
    quraan_lines = [line.strip() for line in f if line.strip()]

def highlight_root(word, root_letters):
    highlighted = ""
    for char in word:
        if char in root_letters:
            highlighted += f"<span class='root'>{char}</span>"
        else:
            highlighted += char
    return highlighted

def find_quran_references(root_letters):
    matches = []
    count = 0
    root_set = set(root_letters)

    for verse in quraan_lines:
        if root_set & set(verse):  # basic filter
            root_hits = [c for c in verse if c in root_set]
            if len(root_hits) >= len(root_set):  # basic root match
                count += 1
                highlighted = highlight_root(verse, root_set)
                matches.append(highlighted)
                if len(matches) >= 3:
                    break

    return count, matches

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    word = data.get("word", "").strip()

    if not word:
        return jsonify({"error": "No word provided."}), 400

    try:
        prompt = f"""
أنت خبير في اللغويات العربية والصرف القرآني.

حلل الكلمة العربية: "{word}"

🔹 أعد فقط:
1. الجذر العربي للكلمة، مثال: ك-ت-ب
2. الترجمة الإنجليزية للجذر
3. الترجمة الإنجليزية للكلمة الكاملة
4. الوزن الصرفي (الميزان) ونوعه

✅ استخدم هذا الشكل بدقة:
جذر الكلمة: ...
ترجمة الجذر: ...
معنى الكلمة: ...
الوزن الصرفي: ... (النوع: ...)

❌ لا تذكر الآيات أو عدد مرات الظهور، سأقوم بذلك بنفسي.
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        reply = response.choices[0].message.content.strip()

        # Extract results using regex
        root_match = re.search(r"جذر الكلمة:\s*([أ-ي\-]+)", reply)
        root_arabic = root_match.group(1).replace("-", "") if root_match else ""

        meaning_root = re.search(r"ترجمة الجذر:\s*(.+)", reply)
        meaning_word = re.search(r"معنى الكلمة:\s*(.+)", reply)
        scale_info = re.search(r"الوزن الصرفي:\s*(.+?)\(النوع:\s*(.+?)\)", reply)

        # Lookup Quran references from local file
        count, verses = find_quran_references(root_arabic)

        return jsonify({
            "word": word,
            "root": root_arabic,
            "translation_root": meaning_root.group(1) if meaning_root else "",
            "translation_word": meaning_word.group(1) if meaning_word else "",
            "scale": scale_info.group(1).strip() if scale_info else "",
            "scale_type": scale_info.group(2).strip() if scale_info else "",
            "quran_count": count,
            "quran_verses": verses
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
