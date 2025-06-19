from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load Quran text at startup
try:
    with open("quraan.txt", "r", encoding="utf-8") as f:
        quran_text = f.read()
except Exception as e:
    quran_text = ""
    print("Error loading quraan.txt:", e)


def count_root_occurrences(root_letters, quran_text):
    count = 0
    root_chars = set(root_letters)
    words = quran_text.split()

    for word in words:
        if root_chars.issubset(set(word)):
            count += 1

    return count


def find_verses_with_root(root_letters, quran_text, limit=3):
    root_chars = set(root_letters)
    verses = quran_text.split("۞")  # assuming ۞ is used to separate verses

    matched = []
    for verse in verses:
        if root_chars.issubset(set(verse)):
            matched.append(verse.strip())
            if len(matched) >= limit:
                break

    return matched


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    word = data.get("word", "").strip()

    if not word:
        return jsonify({"error": "No word provided."}), 400

    try:
        # Ask OpenAI for analysis and root extraction
        prompt = f"""
أنت خبير لغوي في اللغة العربية وتحليل الصرف القرآني.

حلل الكلمة: "{word}"

✅ حدد جذر الكلمة فقط كأحرف مفصولة بفواصل بدون شرح:
مثال: ك، ت، ب

أجب فقط بالجذر بشكل مباشر.
"""

        root_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        root_letters = root_response.choices[0].message.content.strip().replace(",", "").replace(" ", "")
        root_letters_list = list(root_letters)

        # Find root occurrences and sample verses
        root_count = count_root_occurrences(root_letters_list, quran_text)
        root_verses = find_verses_with_root(root_letters_list, quran_text)

        # Generate final detailed prompt for linguistic styling
        full_prompt = f"""
أنت خبير صرف عربي وقرآني.

الكلمة: "{word}"

جذرها: {"، ".join(root_letters_list)}

هذا النص المقتطع من القرآن لاستخدامك:
-----
{quran_text[:4000]}...
-----

✅ حلل الكلمة باستخدام:
- <span class='root'> لجذر الكلمة
- <span class='prefix'> للبداية
- <span class='suffix'> للنهاية
- <span class='extra'> لأي شيء زائد

✅ ثم:
1. بيّن الجذر بالعربية والحروف الجذرية مضللة بـ <span class='root'>
2. ترجمة الجذر بالإنجليزية
3. معنى الكلمة بالإنجليزية
4. عدد مرات الجذر: {root_count}
5. الآيات التالية تحتوي على الجذر (اظهر الجذر مضللًا):

{chr(10).join(root_verses)}

6. الوزن الصرفي ونوعه

أجب بصيغة HTML.
"""

        result_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.3
        )

        return jsonify({"result": result_response.choices[0].message.content})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
