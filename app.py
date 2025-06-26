from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
from camel_tools.morphology.database import MorphologyDB
from camel_tools.morphology.analyzer import Analyzer

app = Flask(__name__)
CORS(app)

# Load your OpenAI key from env or config
openai.api_key = 'YOUR_OPENAI_API_KEY'  # Replace with your actual key or use env variable

# Load the CAMeL morphology database once at startup
db = MorphologyDB.builtin_db()
analyzer = Analyzer(db)

# Load your preprocessed Quran rooted JSON here:
import json
with open('quraan_rooted.json', 'r', encoding='utf-8') as f:
    quran_data = json.load(f)

def highlight_root(word, root_letters):
    # Highlights root letters in the word in red
    result = ''
    root_set = set(root_letters)
    for letter in word:
        if letter in root_set:
            result += f"<span class='root'>{letter}</span>"
        else:
            result += letter
    return result

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    word = data.get('word')
    if not word:
        return jsonify({'error': 'No word provided'}), 400

    # Use CAMeL analyzer to get morphological analyses
    analyses = analyzer.analyze(word)
    if not analyses:
        return jsonify({'error': 'Word not found in morphological database'}), 404

    # Take the first analysis as the best guess
    analysis = analyses[0]

    # Extract root and pattern (scale)
    root = analysis.get('root') or ''
    scale = analysis.get('pattern') or ''
    pos = analysis.get('pos') or ''

    # Extract root letters as list (remove hyphens etc.)
    root_letters = [l for l in root if l.isalpha()]

    # Highlight root letters in the word
    word_colored = highlight_root(word, root_letters)

    # Find occurrences in quran_data based on root
    occurrences = []
    root_occurrences_count = 0
    for verse_info in quran_data:
        verse_root = verse_info.get('root', '')
        if root and root == verse_root:
            root_occurrences_count += 1
            # Verse text with root letters highlighted red
            verse_text = verse_info.get('verse_highlighted', '')
            occurrences.append(f"{verse_info['sura']}|{verse_info['aya']}|{verse_text}")

    # Ask OpenAI for English translation of the word and root
    prompt = (
        f"Translate this Arabic word to English: {word}\n"
        f"Also translate this Arabic root: {root}\n"
        f"Provide a short clear translation for each."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        translations = response['choices'][0]['message']['content'].split('\n')
        word_en = translations[0] if len(translations) > 0 else ""
        root_en = translations[1] if len(translations) > 1 else ""
    except Exception as e:
        word_en = ""
        root_en = ""

    return jsonify({
        'word': word,
        'word_colored': word_colored,
        'root': root,
        'root_letters': root_letters,
        'root_en': root_en,
        'word_en': word_en,
        'scale': scale,
        'pos': pos,
        'root_occurrences': root_occurrences_count,
        'verses': occurrences
    })

if __name__ == '__main__':
    app.run(debug=True)
