import os
import zipfile
import xml.etree.ElementTree as ET
import re
from collections import defaultdict, Counter
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# regex to strip Arabic diacritics (تشكيل)
DIACRITICS_PATTERN = re.compile(
    r'[\u0610-\u061A\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]'
)

def strip_diacritics(text: str) -> str:
    return DIACRITICS_PATTERN.sub('', text or '')

def load_dataset(zip_path='data/Nemlar_dataset.zip'):
    words_index = {}
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for fname in zf.namelist():
            if not fname.lower().endswith('.xml'):
                continue
            try:
                root = ET.fromstring(zf.read(fname))
            except ET.ParseError:
                continue
            for al in root.findall('.//ArabicLexical'):
                raw_word   = al.attrib.get('word','').strip()
                raw_pref   = al.attrib.get('prefix','').strip()
                raw_root   = al.attrib.get('root','').strip()
                raw_suff   = al.attrib.get('suffix','').strip()
                raw_pat    = al.attrib.get('pattern','').strip()
                if not raw_word or not raw_root:
                    continue

                # strip diacritics
                word   = strip_diacritics(raw_word)
                pref   = strip_diacritics(raw_pref)
                root_s = strip_diacritics(raw_root)
                suff   = strip_diacritics(raw_suff)
                pat    = strip_diacritics(raw_pat)

                if word not in words_index:
                    # prepare letter-level segments
                    segments = []
                    if pref:   segments.append({'text': pref,   'type':'prefix'})
                    if root_s: segments.append({'text': root_s, 'type':'root'})
                    if suff:   segments.append({'text': suff,   'type':'suffix'})

                    words_index[word] = {
                        'segments': segments,
                        'pattern':  pat,
                        'root':     root_s
                    }
    return words_index

def load_quran_verses(quran_path='data/quraan.txt'):
    verses = []
    with open(quran_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, start=1):
            text = strip_diacritics(line.strip())
            if text:
                verses.append({'verseNumber': i, 'text': text})
    return verses

# Startup: load data
words_index   = load_dataset()
verses       = load_quran_verses()

# Precompute root → [example verses] and root counts
root_set     = {e['root'] for e in words_index.values()}
root_examples= defaultdict(list)
root_counts  = Counter()

for v in verses:
    tokens = set(re.findall(r'[\u0600-\u06FF]+', v['text']))
    hits   = tokens & root_set
    for r in hits:
        root_counts[r] += 1
        if len(root_examples[r]) < 3:
            root_examples[r].append(v)

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

    w       = strip_diacritics(data['word'].strip())
    entry   = words_index.get(w)
    if not entry:
        return jsonify(error="Word not found"), 404

    r       = entry['root']
    count   = root_counts.get(r, 0)
    examples= root_examples.get(r, [])

    return jsonify({
        'segments':         entry['segments'],
        'pattern':          entry['pattern'],
        'root_occurrences': count,
        'example_verses':   examples
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
