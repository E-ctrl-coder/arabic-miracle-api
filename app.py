import os
import zipfile
import xml.etree.ElementTree as ET
import re
import logging
from collections import defaultdict, Counter
from flask import Flask, jsonify, request, current_app
from flask_cors import CORS

# ——— Logging Setup —————————————————————————————————————————————
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = Flask(__name__)
CORS(app)

# Toggle hybrid parsing
app.config['USE_HYBRID_ALKHALIL'] = True

# Alkhalil REST API helper
from aratools_alkhalil.helper import analyze_with_alkhalil

# ——— Log Startup Configuration ————————————————————————————————
ALK_URL = os.getenv("ALKHALIL_URL", "<not set>")
logging.warning(
    "MiracleContext starting with USE_HYBRID_ALKHALIL=%s, ALKHALIL_URL=%s",
    app.config['USE_HYBRID_ALKHALIL'],
    ALK_URL
)

# ——— Root Route ————————————————————————————————————————————
@app.route("/", methods=['GET'])
def index():
    return jsonify({
        "status": "ok",
        "routes": ["/analyze?word=…", "/debug/<raw_word>"]
    }), 200

# ——— Arabic Normalization ——————————————————————————————————————
DIACRITICS_PATTERN = re.compile(r'[\u0610-\u061A\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]')
HIDDEN_CHARS = re.compile(r'[\uFEFF\u200B\u00A0]')
NORMALIZE_MAP = str.maketrans({
    'آ': 'ا', 'أ': 'ا', 'إ': 'ا',
    'ة': 'ه', 'ى': 'ي', 'ـ': ''
})
PREFIXES = ['ال', 'و', 'ف', 'ب', 'ك', 'ل', 'س', 'است']
SUFFIXES = ['ه', 'ها', 'هم', 'هن', 'كما', 'نا', 'ني', 'ي',
            'وا', 'ان', 'ين', 'ون', 'ات', 'ة', 'ك']

def normalize_arabic(text: str) -> str:
    if not text:
        return ''
    text = HIDDEN_CHARS.sub('', text)
    text = text.translate(NORMALIZE_MAP)
    return DIACRITICS_PATTERN.sub('', text)

def try_strip_affixes(word: str):
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

# ——— Dataset & Quran Loading ————————————————————————————————————
def load_dataset(zip_path='data/Nemlar_dataset.zip'):
    idx = {}
    with zipfile.ZipFile(zip_path) as zf:
        for fn in zf.namelist():
            if not fn.lower().endswith('.xml'):
                continue
            try:
                xml_data = zf.read(fn)
                root = ET.fromstring(xml_data)
            except Exception:
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
                        segs.append({'text': pref, 'type': 'prefix'})
                    if rt:
                        segs.append({'text': rt,   'type': 'root'})
                    if suff:
                        segs.append({'text': suff, 'type': 'suffix'})
                    idx[w] = {'segments': segs, 'pattern': pat, 'root': rt}
    return idx

def load_quran(q_path='data/quraan.txt'):
    vs = []
    with open(q_path, encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            txt = normalize_arabic(line.strip())
            if txt:
                vs.append({'verseNumber': i, 'text': txt})
    return vs

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

# ——— Analyze Endpoint ——————————————————————————————————————————
@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    app.logger.info(
        f"→ /analyze invoked method={request.method} "
        f"args={request.args.to_dict()} "
        f"json={request.get_json(silent=True)}"
    )

    if request.method == 'GET':
        raw = request.args.get('word', '').strip()
    else:
        data = request.get_json(silent=True) or {}
        raw  = data.get('word', '').strip()

    w = normalize_arabic(raw)
    if not w:
        app.logger.info("↪ Invalid payload (empty after normalize)")
        return jsonify(error="Invalid payload"), 400

    results = []
    try:
        entry = words_index.get(w)

        # Hamza fallback
        if not entry:
            for hamza in ('أ', 'إ', 'آ'):
                if w.startswith(hamza) and (cand := words_index.get(w[1:])):
                    entry = {
                        'segments': [{'text': hamza, 'type': 'prefix'}] + cand['segments'],
                        'pattern':  cand['pattern'],
                        'root':     cand['root']
                    }
                    break

        # Affix fallback
        if not entry:
            for pre, core, suf in try_strip_affixes(w):
                if (cand := words_index.get(core)):
                    segs = (
                        ([{'text': pre, 'type': 'prefix'}] if pre else [])
                        + cand['segments']
                        + ([{'text': suf, 'type': 'suffix'}] if suf else [])
                    )
                    entry = {'segments': segs, 'pattern': cand['pattern'], 'root': cand['root']}
                    break

        # Root-only fallback
        if not entry and w in root_set:
            entry = {
                'segments': [{'text': w, 'type': 'root'}],
                'pattern':  'فعل',
                'root':     w
            }

        if not entry:
            app.logger.info("↪ Word not found in dataset or root set")
            return jsonify(error="Word not found"), 404

        # Dataset result
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

        # Hybrid Alkhalil fallback
        if current_app.config['USE_HYBRID_ALKHALIL']:
            parses = analyze_with_alkhalil(w)
            for p in parses:
                p['source'] = 'hybrid_alkhalil'
            results.extend(parses)

    except Exception as e:
        app.logger.exception("‼ Exception inside /analyze")
        return jsonify(error=str(e)), 500

    app.logger.info(f"↪ /analyze returning {len(results)} items")
    return jsonify(results), 200

# ——— Debug Endpoint ——————————————————————————————————————————
@app.route('/debug/<raw_word>', methods=['GET'])
def debug_word(raw_word):
    w = normalize_arabic(raw_word)
    return jsonify({
        'original': raw_word,
        'normalized': w,
        'in_index': w in words_index,
        'codes': [ord(ch) for ch in raw_word]
    }), 200

# ——— Global Error Handler —————————————————————————————————————
@app.errorhandler(Exception)
def handle_exception
