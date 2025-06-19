from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")  # Make sure your key is set in the environment

@app.route('/analyze', methods=['POST'])
def analyze():
    user_text = request.json.get('text', '')

    prompt = f"""
    Analyze the following Arabic sentence or word: "{user_text}"

    Return:
    1. The root letters (in Arabic).
    2. The English meaning of the root.
    3. Full sentence/context-aware English translation.
    4. Quranic occurrences: How many times the root appears, and a few sample verses.
    5. The morphological weight or pattern (وزن صرفي).
    Highlight root letters in the word using <span class='highlight'></span>.
    """

    completion = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    content = completion['choices'][0]['message']['content']

    return jsonify({
        'analysis': content
    })
