from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load Quran verses once at startup
with open("quraan.txt", "r", encoding="utf8") as f:
    quran_lines = f.readlines()

def find_verses_with_root(root_letters, max_results=3):
    matches = []
    root_set = set(root_letters)
    count = 0

    for line in quran_lines:
        verse = line.strip()
        if not verse or "|" not in verse:
            continue

        sura_ayah, text = verse.split("|", maxsplit=1)
        match = True
        for letter in root_set:
            if letter not in text:
                match = False
                break
        if match:
            # Highlight root letters
            highlighted = ""
            for char in text:
                if char in root_set:
                    highlighted += f"<span class='root'>{char}</span>"
                else:
                    highlighted += char
            matches.append(f"<strong>{sura_ayah}</strong> {highlighted}")
            count += 1
            if len(matches) >= max_results:
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
أنت خبير في الصرف واللغة العربية وتحليل الكلمات في القرآن.

حلل الكلمة التالية: "{word}"

✅ أرجع النتيجة باستخدام تنسيقات HTML التالية:
- <span class='root'> للحروف الجذرية (لون أحمر)
- <span class='prefix'> للحروف الزائدة في البداية (لون أزرق)
- <span class='suffix'> للحروف الزائدة في النهاية (لون أخضر)
- <span class='extra'> لأي حروف زائدة أخرى (لون رمادي)

🔹 يجب أن تتضمن النتيجة:

1. الكلمة بعد التحليل والتلوين.
2. الجذر (بالعربية)، وترجمته للإنجليزية.
3. ترجمة الكلمة الكاملة للإنجليزية.
4. الوزن الصرفي (مثل: فَعَّال)، ونوعه (مثل: اسم مبالغة).
5. فقط أعد الجذر كحروف مفصولة حتى نستخدمها في البحث في القرآن مثل: ك-ت-ب

📌 أعد النتيجة بالعربية مع ترجمة إنجليزية حيث يُطلب.
"""
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        reply = response.choices[0].message.content

        # Extract root for searching Quran
        import re
        root_match = re.search(r"(?i)الجذر\s*[:：]?\s*<span class='root'>(.*?)</span>", reply)
        if not root_match:
            root_match = re.search(r"\b([أ-ي]-[أ-ي]-[أ-ي])\b", reply)
        if root_match:
            raw_root = root_match.group(1)
            root_letters = [r.strip() for r in re.split(r"[-–]", raw_root) if r.strip()]
            count, matched_verses = find_verses_with_root(root_letters)
        else:
            count = 0
            mat
