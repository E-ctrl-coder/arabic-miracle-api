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

# Toggle our hybrid analyzer on/off
app.config['USE_HYBRID_ALKHALIL'] = True

# Import the HTTP-based Alkhalil helper
from aratools_alkhalil.helper import analyze_with_alkhalil

# ——— Log Startup Configuration ——————————————————————————————————
# Runs at import time so it shows up immediately in Render logs
ALK_URL = os.getenv("ALKHALIL_URL", "<not set>")
logging.warning(
    "MiracleContext starting with USE_HYBRID_ALKHALIL=%s, ALKHALIL_URL=%s",
    app.config['USE_HYBRID_ALKHALIL'],
    ALK_URL
)

# ——— Root Health Check ——————————————————————————————————————
@app.route("/", methods=['GET'])
def index():
    return jsonify({
        "status": "ok",
        "routes": ["/analyze?word=…", "/debug/<raw_word>"]
    }), 200

# ——— Arabic Normalization Helpers ——————————————————————————————
DIACRITICS_PATTERN = re.compile(
    r'[\u0610-\u061A\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]'
)
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
    return
