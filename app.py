from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

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

يجب أن تُرجع النتيجة بصيغة HTML باستخدام:
- <span class='root'> للحروف الجذرية
- <span class='prefix'> للحروف الزائدة كبادئة
- <span class='suffix'> للحروف الزائدة كلاحقة
- <span class='extra'> لأي حروف زائدة أخرى

🔹 يجب أن تتضمن النتيجة:

1. **الكلمة مع التلوين**:
   - حدد الجذر داخل الكلمة باستخدام <span class='root'>
   - الحروف الزائدة بـ <span class='prefix'> أو <span class='suffix'> أو <span class='extra'>

2. **جذر الكلمة (بالعربية)**:
   - اكتب الجذر بالحروف المفردة داخل <span class='root'>
   - ترجم الجذر للإنجليزية (مثلاً: ك-ت-ب → to write)

3. **معنى الكلمة الكاملة بالإنجليزية**

4. **الاستعمال القرآني**:
   - استخدم **الجذر العربي فقط** (وليس الترجمة) للبحث
   - عدد مرات ظهور الجذر في القرآن الكريم
   - أعرض آيتين أو ثلاث تحتوي على الجذر
   - ظلل الحروف الجذرية في الآية باستخدام <span class='root'>

5. **الوزن الصرفي (الميزان)**:
   - اذكر الوزن الصرفي للكلمة (مثل: فَعَّال، يَفْتَعِل)
   - ما نوع هذا الوزن؟ (مثل: صيغة مبالغة، اسم مكان، فعل مجرد...)

✅ يجب أن تكون كل الإجابات بالعربية، مع الترجمة الإنجليزية حيث يُطلب فقط. لا تستخدم الترجمة الإنجليزية للبحث عن الجذر في القرآن. نظّم التنسيق بوضوح باستخدام HTML.
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        reply = response.choices[0].message.content
        return jsonify({"result": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
