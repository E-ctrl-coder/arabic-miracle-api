from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load Quran content once at startup
try:
    with open("quraan.txt", "r", encoding="utf-8") as f:
        quran_text = f.read()
except Exception as e:
    quran_text = ""
    print("Error loading quraan.txt:", e)

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

هذا هو النص الكامل للقرآن الكريم لتستخدمه عند الحاجة:
-----
{quran_text[:4000]}...
-----
(⚠️ ملاحظة: هذا مقتطف فقط من النص الكامل لتوفير مساحة في النموذج.)

✅ ارجع النتيجة بصيغة HTML باستخدام:
- <span class='root'> للحروف الجذرية
- <span class='prefix'> للحروف الزائدة كبادئة
- <span class='suffix'> للحروف الزائدة كلاحقة
- <span class='extra'> لأي حروف زائدة أخرى

🔹 يجب أن تتضمن النتيجة:

1. **الكلمة مع التلوين** باستخدام العلامات أعلاه.

2. **جذر الكلمة (بالعربية)**:
   - بالحروف المفردة داخل <span class='root'>
   - مع ترجمة الجذر بالإنجليزية

3. **معنى الكلمة الكاملة بالإنجليزية**

4. **الاستعمال القرآني**:
   - عدد مرات ظهور الجذر (وليس الكلمة فقط)
   - آيتان أو ثلاث تحتويان على الجذر
   - الحروف الجذرية مظللة بـ <span class='root'>

5. **الوزن الصرفي (الميزان)**:
   - مثال: فَعَّال، يَفْتَعِل
   - نوع الوزن: مثل صيغة مبالغة، اسم مكان، إلخ

كل الردود يجب أن تكون بالعربية، مع ترجمة إنجليزية فقط حيث يُطلب. لا تستخدم المعنى الإنجليزي للبحث.
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        reply = response.choices[0].message.content
        return jsonify({"result": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
