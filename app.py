import os
import zipfile
import xml.etree.ElementTree as ET
import re
from collections import defaultdict, Counter
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DIACRITICS_PATTERN = re.compile(
    r'[\u0610-\u061A\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]'
)

def normalize_arabic(text: str) -> str:
    # strip tashkeel, normalize hamza variants, tā’ marbūṭa, etc.
    if not text: return ''
    normal_map = str.maketrans({'آ':'ا','أ':'ا','إ':'ا','ة':'ه','ى':'ي','ـ':''})
    text = text.translate(normal_map)
    return DIACRITICS_PATTERN.sub('', text)

def load_dataset(zip_path='data/Nemlar_dataset.zip'):
    idx = {}
    with zipfile.ZipFile(zip_path) as zf:
        for fn in zf.namelist():
            if not fn.lower().endswith('.xml'): continue
            try:
                root = ET.fromstring(zf.read(fn))
            except ET.ParseError:
                continue
            for al in root.findall('.//ArabicLexical'):
                w  = normalize_arabic(al.attrib.get('word','').strip())
                p  = normalize_arabic(al.attrib.get('prefix','').strip())
                r  = normalize_arabic(al.attrib.get('root','').strip())
                s  = normalize_arabic(al.attrib.get('suffix','').strip())
                pat= normalize_arabic(al.attrib.get('pattern','').strip())
                if not w or not r: continue
                if w not in idx:
                    segs = []
                    if p: segs.append({'text':p,'type':'prefix'})
                    if r: segs.append({'text':r,'type':'root'})
                    if s: segs.append({'text':s,'type':'suffix'})
                    idx[w] = {'segments':segs,'pattern':pat,'root':r}
    return idx

def load_quran(q_path='data/quraan.txt'):
    verses=[]
    with open(q_path,encoding='utf-8') as f:
        for i,line in enumerate(f,1):
            t=normalize_arabic(line.strip())
            if t: verses.append({'verseNumber':i,'text':t})
    return verses

# startup
words_index   = load_dataset()
verses        = load_quran()
root_set      = {e['root'] for e in words_index.values()}
root_counts   = Counter()
root_examples = defaultdict(list)

for v in verses:
    toks = set(re.findall(r'[\u0600-\u06FF]+', v['text']))
    hits = toks & root_set
    for r in hits:
        root_counts[r] += 1
        if len(root_examples[r])<3:
            root_examples[r].append(v)
@app.route('/debug/<raw_word>', methods=['GET'])
def debug_word(raw_word):
    # apply the same normalization used in analyze()
    w = normalize_arabic(raw_word)
    # capture every Unicode code point in the raw input
    codes = [ord(ch) for ch in raw_word]
    return jsonify({
        "original":   raw_word,
        "codes":      codes,
        "normalized": w,
        "in_index":   w in words_index
    }), 200
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json(silent=True) or {}
    raw  = data.get('word','').strip()
    w    = normalize_arabic(raw)
    if not w:
        return jsonify(error="Invalid JSON payload"), 400

    entry = words_index.get(w)

    # ── FALLBACK: bare-root lookup ──
    if not entry and w in root_set:
        entry = {
            'segments':    [{'text': w, 'type':'root'}],
            'pattern':     'فعل',
            'root':        w
        }

    if not entry:
        return jsonify(error="Word not found"), 404

    r    = entry['root']
    cnt  = root_counts.get(r, 0)
    exs  = root_examples.get(r, [])

    return jsonify({
        'segments':         entry['segments'],
        'pattern':          entry['pattern'],
        'root_occurrences': cnt,
        'example_verses':   exs
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT',10000))
    app.run(host='0.0.0.0', port=port)
