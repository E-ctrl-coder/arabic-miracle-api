import os
import zipfile
import xml.etree.ElementTree as ET
import re
from collections import defaultdict, Counter
from flask import Flask, jsonify, request
from flask_cors import CORS

# AraTools imports
from aratools.morphology import Analyzer
from aratools.arabic    import strip_tashkeel, normalize_alef

app = Flask(__name__)
CORS(app)

# ── Normalization & Affixes ──
DIACRITICS_PATTERN = re.compile(r'[\u0610-\u061A\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]')
HIDDEN_CHARS       = re.compile(r'[\uFEFF\u200B\u00A0]')
NORMALIZE_MAP      = str.maketrans({'آ':'ا','أ':'ا','إ':'ا','ة':'ه','ى':'ي','ـ':''})
PREFIXES           = ['ال','و','ف','ب','ك','ل','س','است']
SUFFIXES           = ['ه','ها','هم','هن','كما','نا','ني','ي','وا','ان','ين','ون','ات','ة','ك']

def normalize_arabic(text: str) -> str:
    text = HIDDEN_CHARS.sub('', text).translate(NORMALIZE_MAP)
    return DIACRITICS_PATTERN.sub('', text)

def try_strip_affixes(word: str):
    for pre in PREFIXES:
        if word.startswith(pre) and len(word)>len(pre):
            yield pre, word[len(pre):], None
    for suf in SUFFIXES:
        if word.endswith(suf) and len(word)>len(suf):
            yield None, word[:-len(suf)], suf
    for pre in PREFIXES:
        if word.startswith(pre) and len(word)>len(pre):
            mid = word[len(pre):]
            for suf in SUFFIXES:
                if mid.endswith(suf) and len(mid)>len(suf):
                    yield pre, mid[:-len(suf)], suf

# ── Nemlar Dataset Loader ──
def load_dataset(zip_path='data/Nemlar_dataset.zip'):
    idx = {}
    with zipfile.ZipFile(zip_path,'r') as zf:
        for fn in zf.namelist():
            if not fn.lower().endswith('.xml'): continue
            try:
                root_elem = ET.fromstring(zf.read(fn))
            except ET.ParseError:
                continue
            for al in root_elem.findall('.//ArabicLexical'):
                raw_w, raw_pref, raw_root, raw_suff, raw_pat = (
                  al.attrib.get(k,'').strip()
                  for k in ('word','prefix','root','suffix','pattern')
                )
                w    = normalize_arabic(raw_w)
                pref = normalize_arabic(raw_pref)
                root = normalize_arabic(raw_root)
                suff = normalize_arabic(raw_suff)
                pat  = normalize_arabic(raw_pat)
                if not w or not root: continue
                if w not in idx:
                    segs = []
                    if pref: segs.append({'text':pref,'type':'prefix'})
                    if root: segs.append({'text':root,'type':'root'})
                    if suff: segs.append({'text':suff,'type':'suffix'})
                    idx[w] = {'segments':segs,'pattern':pat,'root':root}
    return idx

def load_quran(q_path='data/quraan.txt'):
    verses=[]
    with open(q_path,encoding='utf-8') as f:
        for i,line in enumerate(f,1):
            t = normalize_arabic(line.strip())
            if t: verses.append({'verseNumber':i,'text':t})
    return verses

# ── Startup Indexing ──
words_index   = load_dataset()
verses        = load_quran()
root_set      = {e['root'] for e in words_index.values()}
root_counts   = Counter()
root_examples = defaultdict(list)
for v in verses:
    tokens = set(re.findall(r'[\u0600-\u06FF]+', v['text']))
    for r in tokens & root_set:
        root_counts[r]+=1
        if len(root_examples[r])<3: root_examples[r].append(v)

# ── AraTools Analyzer ──
ara_analyzer = Analyzer()

def ara_normalize(text: str) -> str:
    t = strip_tashkeel(text)
    t = normalize_alef(t)
    return t.replace('ى','ي').replace('ة','ه')

def ara_analyze_word(word: str):
    w = ara_normalize(word)
    return ara_analyzer.analyze(w)

# ── Morphological Templates ──
TRILITERAL_PATTERNS = ["فَعَلَ","فَعِلَ","فَعُلَ","فَعَّلَ","فَاعَلَ","أَفْعَلَ",
                       "تَفَعَّلَ","تَفَاعَلَ","اِفْتَعَلَ","اِنْفَعَلَ","اِفْعَلَّ",
                       "اِسْتَفْعَلَ","مُفَاعَلَة","فِعَال","فُعُول","فَعِيل",
                       "فَعُول","فَعَالَة"]
QUADRILITERAL_PATTERNS = ["فَعْلَلَ","تَفَعْلَلَ","اِفْعَنْلَلَ","فَعْلَلِيّ","فَعْلَلَة","فِعْلَال"]

def apply_pattern(root: str, pattern: str) -> str:
    if len(root)==3:
        return pattern.replace('ف',root[0]).replace('ع',root[1]).replace('ل',root[2])
    if len(root)==4:
        out = pattern
        for ph,l in zip(('ف','ع','ل','ن'), root):
            out = out.replace(ph,l)
        return out
    return None

def generate_forms_from_root(root: str):
    pats = TRILITERAL_PATTERNS if len(root)==3 else QUADRILITERAL_PATTERNS
    return [apply_pattern(root,p) for p in pats if apply_pattern(root,p)]

# ── Debug Route ──
@app.route('/debug/<raw_word>', methods=['GET'])
def debug_word(raw_word):
    w     = normalize_arabic(raw_word)
    codes = [ord(ch) for ch in raw_word]
    return jsonify({'original':raw_word,'codes':codes,'normalized':w,'in_index':w in words_index}),200

# ── Original Analyze ──
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json(silent=True) or {}
    raw  = data.get('word','').strip()
    w    = normalize_arabic(raw)
    if not w: return jsonify(error="Invalid JSON payload"),400

    entry = words_index.get(w)
    # hamza-strip
    if not entry:
        for hamza in ('أ','إ','آ'):
            if w.startswith(hamza):
                core= w[1:];cand=words_index.get(core)
                if cand:
                    entry={'segments':[{'text':hamza,'type':'prefix'}]+cand['segments'],
                           'pattern':cand['pattern'],'root':cand['root']}
                    break
    # affix-strip
    if not entry:
        for pre,core,suf in try_strip_affixes(w):
            cand = words_index.get(core)
            if cand:
                segs = ([] if not pre else [{'text':pre,'type':'prefix'}]) + cand['segments']
                if suf: segs.append({'text':suf,'type':'suffix'})
                entry={'segments':segs,'pattern':cand['pattern'],'root':cand['root']}
                break
    # bare-root
    if not entry and w in root_set:
        entry={'segments':[{'text':w,'type':'root'}],'pattern':'فعل','root':w}

    if not entry: return jsonify(error="Word not found"),404

    r = entry['root']
    # Nemlar-based patterns
    patterns_for_root = sorted({e['pattern'] for e in words_index.values() if e['root']==r})
    # Quran counts & samples
    word_occ, word_exs = 0, []
    for v in verses:
        toks = re.findall(r'[\u0600-\u06FF]+',v['text'])
        if w in toks:
            word_occ+=1
            if len(word_exs)<3: word_exs.append(v)

    return jsonify({
        'original_word':         raw,
        'segments':              entry['segments'],
        'root':                 
