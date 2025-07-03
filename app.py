from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os

app = Flask(__name__)
CORS(app)

# 1. Define your prefix/suffix inventories
PREFIXES = ['سوف', 'وال', 'فال', 'ولل', 'ول', 'كال', 'فل', 'لل', 'وب', 'وب', 'سب', 'ب', 'و', 'ف', 'ل']
SUFFIXES = ['كما', 'هما', 'كم', 'نا', 'ه', 'ها', 'هم', 'هن', 'ني', 'ني', 'ون', 'ات', 'ة', 'ت', 'ا']

# 2. Load Quran corpus once
QURAN_TEXT = ''
with open(os.path.join(os.path.dirname(__file__), 'quraan.txt'), 'r', encoding='utf-8') as f:
    QURAN_TEXT = f.read()

def detect_prefix_suffix(word):
    """
    Strips the longest matching prefix and suffix.
    Returns tuple (prefix, core, suffix).
    """
    pre, suf = '', ''
    core = word

    # detect prefix (longest first)
    for p in sorted(PREFIXES, key=len, reverse=True):
        if core.startswith(p):
            pre = p
            core = core[len(p):]
            break

    # detect suffix (longest first)
    for s in sorted(SUFFIXES, key=len, reverse=True):
        if core.endswith(s):
            suf = s
            core = core[:-len(s)]
            break

    return pre, core, suf

def find_root_pattern(core):
    """
    Your existing root+pattern logic.
    Here’s a placeholder: treat core letters as root.
    Replace with your Nemlar-based logic.
    """
    letters = re.findall(r'.', core)
    root = ' '.join(letters[:3]) if len(letters) >= 3 else ' '.join(letters)
    pattern = core  # or however you compute it
    return root, pattern

def count_root_occurrence(root):
    """
    Count space-normalised root occurrences in the Quran text.
    """
    # remove spaces to match corpus form
    search = root.replace(' ', '')
    # simple count
    return QURAN_TEXT.count(search)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    word = data.get('word', '').strip()
    if not word:
        return jsonify({'error': 'No word provided'}), 400

    # 1. split prefix/root/suffix
    pre, core, suf = detect_prefix_suffix(word)

    # 2. identify root + pattern
    root, pattern = find_root_pattern(core)

    # 3. count in Quran
    root_count = count_root_occurrence(root)

    return jsonify({
        'prefix': pre,
        'root': root,
        'pattern': pattern,
        'suffix': suf,
        'root_count': root_count
    })

if __name__ == '__main__':
    # default port 5000
    app.run(host='0.0.0.0', debug=True)
