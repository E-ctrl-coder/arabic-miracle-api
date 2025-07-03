import os
import re
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

# 1) Load the entire Quran text once
BASE_DIR = os.path.dirname(__file__)
with open(os.path.join(BASE_DIR, 'quraan.txt'), encoding='utf-8') as f:
    QURAN_TEXT = f.read()

# 2) Define affixes
PREFIXES = sorted([
    "وال", "بال", "كال", "فال", "لل",
    "ال", "و", "ف", "ب", "ك", "ل"
], key=len, reverse=True)

SUFFIXES = sorted([
    "كما", "كم", "كن", "هم", "هن",
    "وا", "ون", "ات",
    "ه", "ها", "ك", "ي", "ت", "نا",
    "ان", "ين", "ا", "ة"
], key=len, reverse=True)

# 3) Known triliteral patterns (use ف ع ل placeholders)
PATTERNS = [
    "فعّل", "فعل", "فعول", "مفعل", "فاعل", "مفعول",
    "افتعل", "انفعل", "استفعل", "افعلّ", "افتعال"
    # …add more patterns as needed…
]

def split_affixes(word: str):
    """Return (prefix, core, suffix)."""
    core = word
    pre = ""
    for p in PREFIXES:
        if core.startswith(p):
            pre, core = p, core[len(p):]
            break

    suf = ""
    for s in SUFFIXES:
        if core.endswith(s):
            suf, core = s, core[: -len(s)]
            break

    return pre, core, suf

def detect_root(core: str):
    """
    Naively assume the remaining core is triliteral.
    If it's not 3 letters, take the middle 3.
    """
    letters = list(core)
    if len(letters) == 3:
        return "".join(letters)
    # fallback: take the 3 middle chars
    mid = len(letters) // 2
    return "".join(letters[mid-1:mid+2])

def detect_pattern(core: str, root: str):
    """
    For each template in PATTERNS, substitute the root letters
    and see if it exactly matches core.
    """
    for tpl in PATTERNS:
        candidate = tpl.replace("ف", root[0]) \
                       .replace("ع", root[1]) \
                       .replace("ل", root[2])
        if candidate == core:
            return tpl
    return ""  # unknown

def count_in_quran(root: str):
    """Count raw occurrences of the root substring."""
    return len(re.findall(root, QURAN_TEXT))

app = Flask(__name__)
CORS(app,
     resources={r"/analyze": {"origins": "*"}},
     methods=["OPTIONS", "POST"],
     allow_headers=["Content-Type"]
)

@app.route('/analyze', methods=['OPTIONS', 'POST'])
def analyze():
    # 1) CORS preflight
    if request.method == 'OPTIONS':
        return make_response((), 204)

    # 2) Actual POST
    data = request.get_json(silent=True) or {}
    word = data.get('word', '').strip()
    if not word:
        return jsonify(error="No word provided"), 400

    # 3) Affix split
    prefix, core, suffix = split_affixes(word)

    # 4) Root & pattern
    root = detect_root(core)
    pattern = detect_pattern(core, root)

    # 5) Occurrence count
    occurrences = count_in_quran(root)

    return jsonify({
        "prefix": prefix,
        "root": root,
        "suffix": suffix,
        "pattern": pattern,
        "occurrences": occurrences
    }), 200

if __name__ == '__main__':
    # bind only to localhost to avoid firewall issues
    app.run(host='127.0.0.1', port=5000, debug=True)
