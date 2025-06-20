from flask import Flask, request, jsonify
import openai
import os
import re

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")  # Make sure this is set in your environment

def extract_root_line(response_text):
    """
    Finds the line that includes root letters.
    """
    for line in response_text.splitlines():
        if "root letter" in line.lower() or "Root letters" in line:
            match = re.search(r'[:：]\s*(.+)', line)
            if match:
                return match.group(1).strip()
    return None

def highlight_root_letters(letters):
    """
    Wrap each Arabic root letter in a span with highlight class.
    """
    clean = letters.replace(" ", "")
    return ''.join(f"<span class='highlight'>{char}</span>" for char in clean)

@app.route('/analyze', methods=['POST'])
def analyze():
    user_input = request.json.get("text", "").strip()

    prompt = f"""
    Analyze the Arabic input: "{user_input}"

    Return:
    1. Root letters (in Arabic).
    2. The English meaning of the root.
    3. The full sentence/contextual English translation.
    4. Quranic usage: number of times the root appears and 1–2 examples.
    5. Morphological pattern (وزن صرفي).

    DO NOT include HTML. Format using plain numbered lines.
    """

    try:
        reply = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        response_text = reply.choices[0].message.content

        # Highlight root letters
        root_text = extract_root_line(response_text)
        if root_text:
            highlighted = highlight_root_letters(root_text)
            response_text = response_text.replace(root_text, highlighted)

        return jsonify({
            "analysis": response_text.replace("\n", "<br>")
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
