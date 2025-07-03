import os
import re
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

# Load full Quran text from quraan.txt (UTF-8)
QURAN_TEXT = ''
with open(os.path.join(os.path.dirname(__file__), 'quraan.txt'), encoding='utf-8') as f:
    QURAN_TEXT = f.read()

# Define your known Arabic prefixes and suffixes
PREFIXES = [
    "ال", "وال", "بال", "كال", "فال", "لل",
    "و", "ف", "ب", "ك", "ل"
]
SUFFIXES = [
    "ه", "ها", "ك", "ي", "ت", "نا", "هم",
    "هن", "كما", "كم", "كن", "ا", "ان", "ين",
    "وا", "ون", "ات", "ة"
]

def split_arabic(word):
    """
    Split an Arabic word into (prefix, root, suffix).
    Picks the longest matching prefix/suffix.
    """
    pre = ""
    suf = ""
    root = word

    # detect prefix
    for p in sorted(PREFIXES, key=len, reverse=True):
        if root.startswith(p):
            pre = p
            root = root[len(p):]
            break

    # detect suffix
    for s in sorted(SUFFIXES, key=len, reverse=True):
        if root.endswith(s):
            suf = s
            root = root[: -len(s)]
            break

    return pre, root, suf

def count_in_quran(root):
    """Count occurrences of the root in the full Quran text."""
    # simple substring count; adjust to word-boundary if needed
    return len(re.findall(root, QURAN_TEXT))

app = Flask(__name__)

# Enable CORS for POST + preflight on /analyze
CORS(app,
     resources={r"/analyze": {"origins": "*"}},
     methods=["OPTIONS", "POST"],
     allow_headers=["Content-Type"]
)

@app.route('/analyze', methods=['OPTIONS', 'POST'])
def analyze():
    # 1) Reply to CORS preflight
    if request.method == 'OPTIONS':
        resp = make_response()
        resp.status_code = 204
        return resp

    # 2) Handle actual POST
    data = request.get_json(silent=True) or {}
    word = data.get('word', '').strip()
    if not word:
        return jsonify(error="No word provided"), 400

    pre, root, suf = split_arabic(word)
    occurrences = count_in_quran(root)

    return jsonify({
        'prefix': pre,
        'root': root,
        'suffix': suf,
        'occurrences': occurrences
    })

if __name__ == '__main__':
    # bind only to localhost (127.0.0.1) so Windows firewall treats it as private
    app.run(host='127.0.0.1', port=5000, debug=True)
