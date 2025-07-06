import os
import zipfile
import xml.etree.ElementTree as ET
import re
from collections import Counter
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def load_dataset(zip_path='data/Nemlar_dataset.zip'):
    words_index = {}
    app.logger.info(f"Loading Nemlar XML from {zip_path}")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if not name.lower().endswith('.xml'):
                    continue
                try:
                    tree = ET.fromstring(zf.read(name))
                except ET.ParseError:
                    app.logger.warning(f"Malformed XML, skipping: {name}")
                    continue

                for al in tree.findall('.//ArabicLexical'):
                    w = al.attrib.get('word','').strip()
                    if not w:
                        continue
                    if w not in words_index:
                        words_index[w] = {
                            'prefix':    al.attrib.get('prefix','').strip(),
                            'root':      al.attrib.get('root','').strip(),
                            'suffix':    al.attrib.get('suffix','').strip(),
                            'pattern':   al.attrib.get('pattern','').strip(),
                            'word_occurrences': 0,
                            'quran_occurrences': 0
                        }
                    words_index[w]['word_occurrences'] += 1
    except Exception as e:
        app.logger.error(f"Failed loading dataset: {e}")
    app.logger.info(f"Dataset loaded: {len(words_index)} unique words")
    return words_index

def load_and_tokenize_quran(quran_path='data/quraan.txt'):
    app.logger.info(f"Loading Quran text from {quran_path}")
    try:
        text = open(quran_path, 'r', encoding='utf-8').read()
    except Exception as e:
        app.logger.error(f"Failed to read Quran text: {e}")
        return []

    # Split on anything that isn't an Arabic letter
    tokens = re.findall(r'[\u0600-\u06FF]+', text)
    app.logger.info(f"Quran tokenized into {len(tokens)} words")
    return tokens

# Startup: load data
words_index = load_dataset()
quran_tokens = load_and_tokenize_quran()
# Precompute root counts
root_counter = Counter()
for entry in words_index.values():
    root = entry['root']
    if root:
        root_counter[root] += 0  # ensure key exists

for token in quran_tokens:
    if token in root_counter:
        root_counter[token] += 1

# Assign quran_occurrences back into words_index
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
        w = payload.get('word','').strip()
    except Exception:
        return jsonify(error="Invalid JSON payload"), 400

    app.logger.info(f"Analyze request for word: {w}")

    if not w:
        return jsonify(error="No word provided"), 400

    entry = words_index.get(w)
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

# Global error handlers to ensure JSON output
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
