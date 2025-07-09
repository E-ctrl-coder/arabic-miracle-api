import os
import zipfile
import xml.etree.ElementTree as ET
import re
from collections import defaultdict, Counter
from flask import Flask, jsonify, request, current_app
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Toggle our new hybrid Alkhalil analyzer on/off
app.config['USE_HYBRID_ALKHALIL'] = True

# Import the fresh helper you created
from aratools_alkhalil.helper import analyze_word_with_alkhalil

# remove diacritics
DIACRITICS_PATTERN = re.compile(
    r'[\u0610-\u061A\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]'
)

# strip invisible chars (BOM, zero-width, non-breaking space)
HIDDEN_CHARS = re.compile(r'[\uFEFF\u200B\u00A0]')

# normalize letter variants
NORMALIZE_MAP = str.maketrans({
    'آ': 'ا', 'أ': 'ا', 'إ': 'ا',
    'ة': 'ه', 'ى': 'ي', 'ـ': ''
})

# common Arabic prefixes and particles
PREFIXES = [
    'ال', 'و', 'ف', 'ب', 'ك', 'ل', 'س',
    'است'
]

# common pronoun/plural/dual suffixes
SUFFIXES = [
    'ه', 'ها', 'هم', 'هن', 'كما', 'نا', 'ني', 'ي',
    'وا', 'ان', 'ين', 'ون', 'ات', 'ة', 'ك'
]

def normalize_arabic(text: str) -> str:
    """Remove hidden chars, strip tashkeel, normalize alef/ta-marbuta/tatweel."""
    if not text:
        return ''
    text = HIDDEN_CHARS.sub('', text)
    text = text.translate(NORMALIZE_MAP)
    return DIACRITICS_PATTERN.sub('', text)

def try_strip_affixes(word: str):
    """
    Yield (prefix, core, suffix) for each affix-stripping possibility.
    Skip the no-affix case in analyze().
    """
    # prefix only
    for pre in PREFIXES:
        if word.startswith(pre) and len(word) > len(pre):
            yield pre, word[len(pre):], None

    # suffix only
    for suf in SUFFIXES:
        if word.endswith(suf) and len(word) > len(suf):
            yield None, word[:-len(suf)], suf

    # prefix+suffix
    for pre in PREFIXES:
        if word.startswith(pre) and len(word) > len(pre):
            mid = word[len(pre):]
            for suf in SUFFIXES:
                if mid.endswith(suf) and len(mid) > len(suf):
                    yield pre, mid[:-len(suf)], suf

def load_dataset(zip_path='data/Nemlar_dataset.zip'):
    idx = {}
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for fn in zf.namelist():
            if not fn.lower().endswith('.xml'):
                continue
            try:
                root_elem = ET.fromstring(zf.read(fn))
            except ET.ParseError:
                continue
            for al in root_elem.findall('.//ArabicLexical'):
                raw_w    = al.attrib.get('word','').strip()
                raw_pref = al.attrib.get('prefix','').strip()
                raw_root = al.attrib.get('root','').strip()
                raw_suff = al.attrib.get('suffix','').strip()
                raw_pat  = al.attrib.get('pattern','').strip()

                w    = normalize_arabic(raw_w)
                pref = normalize_arabic(raw_pref)
                root = normalize_arabic(raw_root)
                suff = normalize_arabic(raw_suff)
                pat  = normalize_arabic(raw_pat)

                if not w or not root:
                    continue

                if w not in idx:
                    segs = []
                    if pref: segs.append({'text':pref,'type':'prefix'})
                    if root: segs.append({'text':root,'type':'root'})
                    if suff: segs.append({'text':suff,'type':'suffix'})
                    idx[w] = {'segments':segs,'pattern':pat,'root':root}
    return idx

def load_quran(q_path='data/quraan.txt'):
    verses = []
    with open(q_path, encoding='utf-8') as f:
        for i, line in enumerate(f, start=1):
            txt = normalize_arabic(line.strip())
            if txt:
                verses.append({'verseNumber':i,'text':txt})
    return verses

# ─── Startup Indexing ───
words_index   = load_dataset()
verses        = load_quran()
root_set      = {e['root'] for e in words_index.values()}
root_counts   = Counter()
root_examples = defaultdict(list)

for v in verses:
    tokens = set(re.findall(r'[\u0600-\u06FF]+', v['text']))
    hits   = tokens & root_set
    for r in hits:
        root_counts[r] += 1
        if len(root_examples[r]) < 3:
            root_examples[r].append(v)

# ─── Debug Endpoint ───
@app.route('/debug/<raw_word>', methods=['GET'])
def debug_word(raw_word):
    w     = normalize_arabic(raw_word)
    codes = [ord(ch) for ch in raw_word]
    return jsonify({
        'original':   raw_word,
        'codes':      codes,
        'normalized': w,
        'in_index':   w in words_index
    }), 200

# ─── Analyze Endpoint (amended) ───
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json(silent=True) or {}
    raw  = data.get('word','').strip()
    w    = normalize_arabic(raw)
    if not w:
        return jsonify(error="Invalid JSON payload"), 400

    results = []

    # 1) dataset lookup + fallbacks
    entry = words_index.get(w)
    if not entry:
        for hamza in ('أ','إ','آ'):
            if w.startswith(hamza):
                cand = words_index.get(w[1:])
                if cand:
                    entry = {
                        'segments': [{'text':hamza,'type':'prefix'}] + cand['segments'],
                        'pattern':  cand['pattern'],
                        'root':     cand['root']
                    }
                    break

    if not entry:
        for pre, core, suf in try_strip_affixes(w):
            cand = words_index.get(core)
            if cand:
                segs = []
                if pre: segs.append({'text':pre,'type':'prefix'})
                segs.extend(cand['segments'])
                if suf: segs.append({'text':suf,'type':'suffix'})
                entry = {'segments': segs, 'pattern': cand['pattern'], 'root': cand['root']}
                break

    if not entry and w in root_set:
        entry = {
            'segments': [{'text':w,'type':'root'}],
            'pattern':  'فعل',
            'root':     w
        }

    if not entry:
        return jsonify(error="Word not found"), 404

    # assemble and tag base result
    r   = entry['root']
    cnt = root_counts.get(r, 0)
    exs = root_examples.get(r, [])
    base = {
        'segments':         entry['segments'],
        'pattern':          entry['pattern'],
        'root_occurrences': cnt,
        'example_verses':   exs
    }
    results.append({'source': 'dataset', **base})

    # 2) Hybrid Alkhalil (Aratools-style)
    if app.config['USE_HYBRID_ALKHALIL']:
        alk = analyze_word_with_alkhalil(w)
        for a in alk:
            a['source'] = 'hybrid_alkhalil'
        results.extend(alk)

    return jsonify(results), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
