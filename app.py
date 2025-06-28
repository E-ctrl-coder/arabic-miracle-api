from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import re
import openai
from alkhaleel import Analyzer

app = Flask(__name__)
CORS(app)

# Load Qur'an rooted dataset
with open('quraan_rooted.json', 'r', encoding='utf-8') as f:
    quraan_data = json.load(f)

# Load raw Qur’an text
with open('quraan.txt', 'r', encoding='utf-8') as f:
    quraan_lines = f.readlines()

# Set your OpenAI key (already stored in Render)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Alkhaleel analyzer
analyzer = Analyzer()

# Arabic normalization function
def normalize_arabic(text):
    text = re.sub(r'[ًٌٍَُِّْـ]', '', text)  # Remove diacritics
    text = re.sub(r'[إأآ]', 'ا', text)       # Normalize alef
    text = re.sub(r'[ؤئ]', 'ء', text)
    text = re.sub(r'ة', 'ه', text)
    return text

# Highlight root letters in red
def highlight_root(word, root):
    result = ''
    root_letters = list(root)
    for char in word:
        if char in root_letters:
            result += f'<span style="color:red;font-weight:bold;">{char}</span>'
            root_letters.remove(char)
        else:
            result += char
    return result

@app.route('/analyze', methods=['POST'])
def analyze_word():
    data = request.get_json()
    word = data.get('word', '').strip()

    if not word:
        return jsonify({'error': 'No word provided'}), 400

    normalized_word = normalize_arabic(word)

    # Use Alkhaleel to analyze the word
    analysis_results = analyzer.analyze(word)
    if not analysis_results:
        return jsonify({'error': 'Could not analyze word'}), 400

    best_result = analysis_results[0]
    root = best_result.get('root')
    pattern = best_result.get('pattern')
    pos = best_result.get('pos')

    # Translate word and root using OpenAI
    messages = [
        {"role": "system", "content": "You are a translator of Arabic to English."},
        {"role": "user", "content": f"What is the English meaning of the Arabic word '{word}' and its root '{root}'?"}
    ]

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        translation = completion.choices[0].message.content.strip()
    except Exception as e:
        translation = "Translation not available."

    # Look up root in quraan_rooted.json
    root_occurrences = quraan_data.get(root, [])
    formatted_occurrences = []
    for occ in root_occurrences:
        verse = occ['text']
        highlighted = highlight_root(verse, root)
        formatted_occurrences.append({
            'surah': occ['surah'],
            'ayah': occ['ayah'],
            'text': highlighted
        })

    return jsonify({
        'word': word,
        'normalized': normalized_word,
        'root': root,
        'pattern': pattern,
        'pos': pos,
        'translation': translation,
        'quran_occurrences': formatted_occurrences,
        'occurrence_count': len(root_occurrences)
    })

@app.route('/')
def home():
    return "Arabic Miracle backend is running."

if __name__ == '__main__':
    app.run(debug=True)
