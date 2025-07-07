import os
import zipfile
import xml.etree.ElementTree as ET
import re
from collections import defaultdict, Counter
from flask import Flask, jsonify, request
from flask_cors import CORS

# Vendored AraTools imports
from aratools.arabic import strip_tashkeel, normalize_alef
from aratools.morphology import Analyzer

app = Flask(__name__)
CORS(app)

# ── Normalization & Affixes ──
DIACRITICS = re.compile(r'[\u0610-\u061A\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]')
HIDDEN     = re.compile(r'[\uFEFF\u200B\u00A0]')
MAP        = str.maketrans({'آ':'ا','أ':'ا','إ':'ا','ة':'ه','ى':'ي','ـ':''})
PREFIXES   = ['ال','و','ف','ب','ك','ل','س','است']
SUFFIXES   = ['ه','ها','هم','هن','كما','نا','ني','ي','وا','ان','ين','ون','ات','ة','ك']

def normalize_arabic(text: str) -> str:
    t = HIDDEN.sub('', text).translate(MAP)
    return DIACRITICS.sub('', t)

def try_strip_affixes(w: str):
    for p in PREFIXES:
        if w.startswith(p) and len(w)>len(p):
            yield p, w[len(p):], None
    for s in SUFFIXES:
        if w.endswith(s) and len(w)>len(s):
            yield None, w[:-len(s)], s
    for p in PREFIXES:
        if w.startswith(p) and len(w)>len(p):
            mid = w[len(p):]
            for s in SUFFIXES:
                if mid.endswith(s) and len(mid)>len(s):
                    yield p, mid[:-len(s)], s

# ── Morphological Pattern Helpers ──
TRI_PATTERNS = [
    "فَعَلَ","فَعِلَ","فَعُلَ","فَعَّلَ","فَاعَلَ","أَفْعَلَ",
    "تَفَعَّلَ","تَفَاعَلَ","اِفْتَعَلَ","اِنْفَعَلَ","اِفْعَلَّ",
    "اِسْتَفْعَلَ","مُفَاعَلَة","فِعَال","فُعُول","فَعِيل",
    "فَعُول","فَعَالَة"
]
QUAD_PATTERNS = [
    "فَعْلَلَ","تَفَعْلَلَ","اِفْعَنْلَلَ",
    "فَعْلَلِيّ","فَعْلَلَة","فِعْلَال"
]

def apply_pattern(root: str, pattern: str) -> str:
    if len(root)==3:
        return (pattern
                .replace("ف", root[0])
                .replace("ع", root[1])
                .replace("ل", root[2]))
    if len(root)==4:
        out = pattern
        for ph, l in zip(("ف","ع","ل","ن"), root):
            out = out.replace(ph, l)
        return out
    return None

def generate_forms_from_root(root: str):
    pats = TRI_PATTERNS if len(root)==3 else QUAD_PATTERNS
    return [f for f in (apply_pattern(root,p) for p in pats) if f]

# ── Dataset Loading ──
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
                raw, pre, rt, sfx, pat = (
                    al.attrib.get(k,'').strip()
                    for k in ('word','prefix','root','suffix','pattern')
                )
                w = normalize_arabic(raw)
                if not w or not rt:
                    continue
                segs = []
                if pre: segs.append({'text': normalize_arabic(pre), 'type': 'prefix'})
                segs.append({'text': normalize_arabic(rt), 'type': 'root'})
                if sfx: segs.append({'text': normalize_arabic(sfx), 'type': 'suffix'})
                idx[w] = {'segments': segs, 'pattern': normalize_arabic(pat), 'root': normalize_arabic(rt)}
    return idx

def load_quran(path='data/quraan.txt'):
    verses = []
    with open(path, encoding='utf-8') as f:
        for i, line in enumerate(f, start=1):
            t = normalize_arabic(line.strip())
            if t:
                verses.append({'verseNumber': i, 'text': t})
    return verses

words_index   = load_dataset()
verses        = load_quran()
root_set      = {e['root'] for e in words_index.values()}
root_counts   = Counter()
root_examples = defaultdict(list)

for v in verses:
    toks = set(re.findall(r'[\u0600-\u06FF]+', v['text']))
    for r in toks & root_set:
        root_counts[r] += 1
        if len(root_examples[r]) < 3:
            root_examples[r].append(v)

# ── Initialize AraTools Analyzer ──
ara = Analyzer()

def ara_normalize(text: str) -> str:
    t = strip_tashkeel(text)
    t = normalize_alef(t)
    return t.replace('ى', 'ي').replace('ة', 'ه')

def ara_analyze(word: str):
    return ara.analyze(ara_normalize(word))

# ── Debug Endpoint ──
@app.route('/debug/<raw>', methods=['GET'])
def debug_route(raw):
    w     = normalize_arabic(raw)
    codes = [ord(ch) for ch in raw]
    return jsonify({'original': raw, 'codes': codes, 'normalized': w, 'in_index': w in words_index}), 200

# ── Main Analyze Endpoint ──
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json(silent=True) or {}
    raw  = data.get('word','').strip()
    w    = normalize_arabic(raw)
    if not w:
        return jsonify(error="Invalid JSON payload"), 400

    entry = words_index.get(w)

    # hamza-strip fallback
    if not entry:
        for h in ('أ','إ','آ'):
            if w.startswith(h) and w[1:] in words_index:
                cand = words_index[w[1:]]
                entry = {
                    'segments': [{'text': h, 'type': 'prefix'}] + cand['segments'],
                    'pattern': cand['pattern'],
                    'root': cand['root']
                }
                break

    # generic affix-strip fallback
    if not entry:
        for pre, core, suf in try_strip_affixes(w):
            cand = words_index.get(core)
            if cand:
                segs = []
                if pre:
                    segs.append({'text': pre, 'type': 'prefix'})
                segs.extend(cand['segments'])
                if suf:
                    segs.append({'text': suf, 'type': 'suffix'})
                entry = {'segments': segs, 'pattern': cand['pattern'], 'root': cand['root']}
                break

    # bare-root fallback
    if not entry and w in root_set:
        entry = {'segments': [{'text': w, 'type': 'root'}], 'pattern': 'فعل', 'root': w}

    if not entry:
        return jsonify(error="Word not found"), 404

    r = entry['root']
    patterns_for_root = sorted({e['pattern'] for e in words_index.values() if e['root']==r})
    word_occ, word_exs = 0, []
    for v in verses:
        if w in re.findall(r'[\u0600-\u06FF]+', v['text']):
            word_occ += 1
            if len(word_exs) < 3:
                word_exs.append(v)

    possible_forms = generate_forms_from_root(r)

    return jsonify({
        'original_word': raw,
        'segments': entry['segments'],
        'root': r,
        'pattern': entry['pattern'],
        'all_patterns_for_root': patterns_for_root,
        'root_occurrences': root_counts.get(r, 0),
        'example_verses_root': root_examples.get(r, []),
        'word_occurrences': word_occ,
        'example_verses_word': word_exs,
        'possible_forms_from_root': possible_forms
    }), 200

# ── AraTools Route ──
@app.route('/ara-tools', methods=['POST'])
def ara_tools_route():
    data = request.get_json(silent=True) or {}
    raw  = data.get('word','').strip()
    if not raw:
        return jsonify(error="Invalid JSON payload"), 400

    results = ara_analyze(raw)
    if not results:
        return jsonify(error="No analysis found"), 404

    roots    = sorted({r.get('root')    for r in results if r.get('root')})
    patterns = sorted({r.get('pattern') for r in results if r.get('pattern')})

    return jsonify({'input': raw, 'roots_found': roots, 'patterns': patterns}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
