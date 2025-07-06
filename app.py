import os
import zipfile
import xml.etree.ElementTree as ET
import re
from collections import Counter
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Regex to match Arabic diacritics (Tashkeel)
DIACRITICS_PATTERN = re.compile(
    r'[\u0610-\u061A\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]'
)

def strip_diacritics(text: str) -> str:
    """Remove all Arabic diacritics from the input string."""
    return DIACRITICS_PATTERN.sub('', text or '')

def load_dataset(zip_path='data/Nemlar_dataset.zip'):
    words_index = {}
    app.logger.info(f"Loading Nemlar XML from {zip_path}")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for name in zf.namelist():
            if not name.lower().endswith('.xml'):
                continue
            try:
                root_ele = ET.fromstring(zf.read(name))
            except ET.ParseError:
                app.logger.warning(f"Skipping malformed XML: {name}")
                continue

            for al in root_ele.findall('.//ArabicLexical'):
                raw_word   = al.attrib.get('word','').strip()
                raw_root   = al.attrib.get('root','').strip()
                if not raw_word or not raw_root:
                    continue

                # strip diacritics from word and root
                word = strip_diacritics(raw_word)
                root = strip_diacritics(raw_root)

                if word not in words_index:
                    words_index[word] = {
                        'prefix':    strip_diacritics(al.attrib.get('prefix','').strip()),
                        'root':      root,
                        'suffix':    strip_diacritics(al.attrib.get('suffix','').strip()),
                        'pattern':   strip_diacritics(al.attrib.get('pattern','').strip()),
                        'word_occurrences':  0,
                        'quran_occurrences': 0
                    }
                words_index[word]['word_occurrences'] += 1

    app.logger.info(f"Parsed {len(words_index)} unique words (diacritics stripped)")
    return words_index

def load_quran_tokens(quran_path='data/quraan.txt'):
    app.logger.info(f"Loading Quran text from {quran_path}")
    text = open(quran_path, 'r', encoding='utf-8').read()
    text = strip_diacritics(text)   # remove tashkeel from Quran
    # tokenize on Arabic letters only
    tokens = re.findall(r'[\u0600-\u06FF]+', text)
    app.logger.info(f"Tokenized Quran into {len(tokens)} words (diacr. stripped)")
    return tokens

# Load data at startup
words_index = load_dataset()
quran_tokens = load_quran_tokens()

# Precompute root occurrence counts
root_counter = Counter()
# initialize keys
for entry in words_index.values():
    root = entry['root']
    if root:
        root_counter[root] = 0

# count occurrences in Quran tokens
for token in quran_tokens:
    if token in root_counter:
        root_counter[token] += 1

# assign back to words_index
for entry in words_index.values():
    entry['quran_occurrences'] = root_counter.get(entry['root'], 0)

@app.route('/', methods=['GET'])
def home():
    return jsonify(message="Arabic Miracle API is running"), 200

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify(status="ok", words_loaded=len(words_index)), 200

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        payload = request.get_json(force=True)
        raw = payload.get('word','').strip()
    except Exception:
        return jsonify(error="Invalid JSON payload"), 400

    # strip diacritics from incoming word
    word = strip_diacritics(raw)
    if not word:
        return jsonify(error="No word provided"), 400

    entry = words_index.get(word)
    if not entry:
        return jsonify(error="Word not found"), 404

    return jsonify({
        'prefix':            entry['prefix'],
        'root':              entry['root'],
        'suffix':            entry['suffix'],
        'pattern':           entry['pattern'],
        'word_occurrences':  entry['word_occurrences'],
        'quran_occurrences': entry['quran_occurrences']
    }), 200

# Ensure all errors return JSON
@app.errorhandler(404)
def not_found(e):
    return jsonify(error="Not found"), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify(error="Method not allowed"), 405

@app.errorhandler(Exception)
def internal_error(e):
    app.logger.exception(e)
    return jsonify(error="Internal server error"), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
