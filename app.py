import os
import zipfile
import xml.etree.ElementTree as ET
import re
from collections import defaultdict, Counter
from flask import Flask, jsonify, request, current_app
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Toggle our hybrid analyzer on/off
app.config['USE_HYBRID_ALKHALIL'] = True

# Import the HTTP-based Alkhalil helper
from aratools_alkhalil.helper import analyze_with_alkhalil

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
    for pre in PREFIXES:
        if word.startswith(pre) and len(word) > len(pre):
            yield pre, word[len(pre):], None

    for suf in SUFFIXES:
        if word.endswith(suf) and len(word) > len(suf):
            yield None, word[:-len(suf)], suf

    for pre in PREFIXES:
        if word.startswith(pre) and len(word) > len(pre):
            mid = word[len(pre):]
            for suf in SUFFIXES:
                if mid.endswith(suf) and len(mid) > len(suf):
                    yield pre, mid[:-len(suf)], suf

def load_dataset(zip_path='data/Nemlar_dataset.zip'):
    idx = {}
    with zipfile.ZipFile(zip_path) as zf:
        for fn in zf.namelist():
            if not fn.lower().endswith('.xml'):
                continue
            try:
                xml_data = zf.read(fn)
                root = ET.fromstring(xml_data)
            except:
                continue
            for al in root.findall('.//ArabicLexical'):
                raw_w    = al.attrib.get('word','').strip()
                raw_pref = al.attrib.get('prefix','').strip()
                raw_root = al.attrib.get('root','').strip()
                raw_suff = al.attrib.get('suffix','').strip()
                raw_pat  = al.attrib.get('pattern','').strip()

                w    = normalize_arabic(raw_w)
                pref = normalize_arabic(raw_pref)
                rt   = normalize_arabic(raw_root)
                suff = normalize_arabic(raw_suff)
                pat  = normalize_arabic(raw_pat)
                if not w or not rt:
                    continue

                if w not in idx:
                    segs = []
                    if pref:
                        segs.append({'text':pref,'type':'prefix'})
                    if rt:
                        segs.append({'text':rt,'type':'root'})
                    if suff:
                        segs.append({'text':suff,'type':'suffix'})
                    idx[w] = {'segments':segs,'pattern':pat,'root':rt}
    return idx

def load_quran(q_path='data/quraan.txt'):
    vs = []
    with open(q_path, encoding='utf-8') as f:
        for i, line in enumerate(f,1):
            txt = normalize_arabic(line.strip())
            if txt:
                vs.append({'verseNumber':i,'text':txt})
    return vs

# Build indexes
words_index   = load_dataset()
verses        = load_quran()
root_set      = {e['root'] for e in words_index.values()}
root_counts   = Counter()
root_examples = defaultdict(list)

for v in verses:
    tokens = set(re.findall(r'[\u0600-\u06FF]+', v['text']))
    for r in tokens & root_set:
        root_counts[r] += 1
        if len(root_examples[r]) < 3:
            root_examples[r].append(v)

@app.route('/debug/<raw_word>', methods=['GET'])
def debug_word(raw_word):
    w = normalize_arabic(raw_word)
    return jsonify({
        'original': raw_word,
        'normalized': w,
        'in_index': w in words_index,
        'codes': [ord(ch) for ch in raw_word]
    }), 200

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    # support browser GET for quick testing
    if request.method == 'GET':
        raw = request.args.get('word', '').strip()
    else:
        data = request.get_json(silent=True) or {}
        raw  = data.get('word','').strip()

    w = normalize_arabic(raw)
    if not w:
        return jsonify(error="Invalid payload"), 400

    results = []

    # 1) dataset lookup + affix fallbacks
    entry = words_index.get(w)
    if not entry:
        # hamza-drop fallback
        for hamza in ('أ','إ','آ'):
            if w.startswith(hamza) and (cand := words_index.get(w[1:])):
                entry = {
                    'segments': [{'text':hamza,'type':'prefix'}] + cand['segments'],
                    'pattern': cand['pattern'], 'root': cand['root']
                }
                break

    if not entry:
        # prefix+suffix stripping
        for pre, core, suf in try_strip_affixes(w):
            if (cand := words_index.get(core)):
                segs = ([{'text':pre,'type':'prefix'}] if pre else []) \
                     + cand['segments'] \
                     + ([{'text':suf,'type':'suffix'}] if suf else [])
                entry = {'segments':segs, 'pattern':cand['pattern'], 'root':cand['root']}
                break

    if not entry and w in root_set:
        entry = {'segments':[{'text':w,'type':'root'}], 'pattern':'فعل', 'root':w}

    if not entry:
        return jsonify(error="Word not found"), 404

    # dataset result
    r   = entry['root']
    cnt = root_counts.get(r, 0)
    exs = root_examples.get(r, [])

    results.append({
        'source':           'dataset',
        'segments':         entry['segments'],
        'pattern':          entry['pattern'],
        'root_occurrences': cnt,
        'example_verses':   exs
    })

    # 2) hybrid Alkhalil REST fallback
    if current_app.config['USE_HYBRID_ALKHALIL']:
        parses = analyze_with_alkhalil(w)
        for p in parses:
            p['source'] = 'hybrid_alkhalil'
        results.extend(parses)

    return jsonify(results), 200

# JSON error handler for debugging
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.exception(e)
    return jsonify(error=str(e)), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
