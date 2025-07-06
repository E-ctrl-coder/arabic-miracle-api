import os
import zipfile
import xml.etree.ElementTree as ET
import re
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def load_dataset(zip_path='data/Nemlar_dataset.zip'):
    words_index = {}
    print(f"🔎 Loading XML dataset from {zip_path} (exists? {os.path.exists(zip_path)})")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for name in zf.namelist():
            if not name.lower().endswith('.xml'):
                continue
            xml_bytes = zf.read(name)
            try:
                root = ET.fromstring(xml_bytes)
            except ET.ParseError:
                print(f"❌ Skipping malformed XML file: {name}")
                continue

            for al in root.findall('.//ArabicLexical'):
                w = al.attrib.get('word','').strip()
                if not w:
                    continue

                # initialize entry
                if w not in words_index:
                    words_index[w] = {
                        'prefix':     al.attrib.get('prefix','').strip(),
                        'root':       al.attrib.get('root','').strip(),
                        'suffix':     al.attrib.get('suffix','').strip(),
                        'pattern':    al.attrib.get('pattern','').strip(),
                        'word_occurrences': 0,
                        'quran_occurrences': 0
                    }

                # count this exact word instance
                words_index[w]['word_occurrences'] += 1

    print(f"✅ Parsed {len(words_index)} unique words")
    return words_index

def load_quran_text(quran_path='data/quraan.txt'):
    print(f"🔎 Loading Quran text from {quran_path} (exists? {os.path.exists(quran_path)})")
    with open(quran_path, 'r', encoding='utf-8') as f:
        text = f.read()
    return text

# 1) Load up front
words_index = load_dataset()
quran_text = load_quran_text()

# 2) Precompute root-occurrence counts (whole-word matches)
print("🔢 Counting root occurrences in Quran text…")
root_counts = {}
for entry in words_index.values():
    root_str = entry['root']
    if not root_str or root_str in root_counts:
        continue

    # Use Unicode word-boundary regex to match whole root
    pattern = re.compile(rf'\b{re.escape(root_str)}\b', flags=re.UNICODE)
    count = len(pattern.findall(quran_text))
    root_counts[root_str] = count

# 3) Assign each entry its Quran count
for entry in words_index.values():
    entry['quran_occurrences'] = root_counts.get(entry['root'], 0)

print("✅ Quran root counts computed.")

@app.route('/', methods=['GET'])
def home():
    return jsonify(message="Arabic Miracle API is running"), 200

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify(status="ok", words_loaded=len(words_index)), 200

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json(silent=True)
    if not data or 'word' not in data:
        return jsonify(error="Invalid JSON payload"), 400

    w = data['word'].strip()
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
