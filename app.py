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

# mapping for letter-level normalization
NORMALIZE_MAP = str.maketrans({
    'آ': 'ا',
    'أ': 'ا',
    'إ': 'ا',
    'ة': 'ه',
    'ى': 'ي',
    'ـ': ''
})

def normalize_arabic(text: str) -> str:
    """Strip tashkeel, normalize alef variants, tā’ marbūṭa, tatwīl, alif maqṣūra."""
    if not text:
        return ''
    # remove tatwīl/alef variants/tā’ marbūṭa/alif maqṣūra
    text = text.translate(NORMALIZE_MAP)
    # remove diacritics
    return DIACRITICS_PATTERN.sub('', text)

def load_dataset(zip_path='data/Nemlar_dataset.zip'):
    words_index = {}
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for fname in zf.namelist():
            if not fname.lower().endswith('.xml'):
                continue
            try:
                root_elem = ET.fromstring(zf.read(fname))
            except ET.ParseError:
                continue
            for al in root_elem.findall('.//ArabicLexical'):
                raw_word = normalize_arabic(al.attrib.get('word','').strip())
                raw_pref = normalize_arabic(al.attrib.get('prefix','').strip())
                raw_root = normalize_arabic(al.attrib.get('root','').strip())
                raw_suff = normalize_arabic(al.attrib.get('suffix','').strip())
                raw_pat  = normalize_arabic(al.attrib.get('pattern','').strip())
                if not raw_word or not raw_root:
                    continue

                if raw_word not in words_index:
                    segments = []
                    if raw_pref:   segments.append({'text': raw_pref,   'type':'prefix'})
                    if raw_root:   segments.append({'text': raw_root,   'type':'root'})
                    if raw_suff:   segments.append({'text': raw_suff,   'type':'suffix'})
                    words_index[raw_word] = {
                        'segments': segments,
                        'pattern':  raw_pat,
                        'root':     raw_root
                    }
    return words_index

def load_quran_verses(quran_path='data/quraan.txt'):
    verses = []
    with open(quran_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, start=1):
            text = normalize_arabic(line.strip())
            if text:
                verses.append({'verseNumber': i, 'text': text})
    return verses

# Startup: build indexes
words_index   = load_dataset()
verses        = load_quran_verses()
root_set      = {e['root'] for e in words_index.values()}
root_examples = defaultdict(list)
root_counts   = Counter()

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
    data = request.get_json(silent=True) or {}
    raw  = data.get('word','').strip()
    w    = normalize_arabic(raw)
    if not w:
        return jsonify(error="Invalid JSON payload"), 400

    # exact lookup
    entry = words_index.get(w)

    # fallback: strip initial hamza/alif variants
    if not entry:
        for hamza in ('ا','أ','إ','آ'):
            if w.startswith(hamza):
                stripped = w[len(hamza):]
                cand = words_index.get(stripped)
                if cand:
                    entry = {
                        'segments': [{'text': hamza, 'type':'prefix'}] + cand['segments'],
                        'pattern':  cand['pattern'],
                        'root':     cand['root']
                    }
                    break

    if not entry:
        return jsonify(error="Word not found"), 404

    root_val = entry['root']
    count    = root_counts.get(root_val, 0)
    examples = root_examples.get(root_val, [])

    return jsonify({
        'segments':         entry['segments'],
        'pattern':          entry['pattern'],
        'root_occurrences': count,
        'example_verses':   examples
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
