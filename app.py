import os
import zipfile
import xml.etree.ElementTree as ET
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def load_dataset():
    words_index = {}
    zip_path = 'data/Nemlar_dataset.zip'
    print(f"🔎 ZIP path: {zip_path}   exists? {os.path.exists(zip_path)}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            print(f"🔍 ZIP contains {len(names)} entries. Sample:", names[:5])

            for name in names:
                if not name.lower().endswith('.xml'):
                    continue
                xml_bytes = zf.read(name)
                tree = ET.fromstring(xml_bytes)

                # Parse every <ArabicLexical> element
                for al in tree.findall('.//ArabicLexical'):
                    w_text = al.attrib.get('word', '').strip()
                    if not w_text:
                        continue

                    # Initialize or update occurrence count
                    if w_text not in words_index:
                        words_index[w_text] = {
                            'prefix':    al.attrib.get('prefix', '').strip(),
                            'root':      al.attrib.get('root', '').strip(),
                            'suffix':    al.attrib.get('suffix', '').strip(),
                            'pattern':   al.attrib.get('pattern', '').strip(),
                            'occurrences': 0
                        }
                    words_index[w_text]['occurrences'] += 1

        print(f"✅ Parsed {len(words_index)} unique words from {zip_path}")
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")

    return words_index

# Build in-memory index at startup
words_index = load_dataset()

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json(force=True) or {}
    w = data.get('word', '').strip()
    entry = words_index.get(w)
    if not entry:
        return jsonify(error="Word not found"), 404
    return jsonify({
        'prefix':      entry['prefix'],
        'root':        entry['root'],
        'suffix':      entry['suffix'],
        'pattern':     entry['pattern'],
        'occurrences': entry['occurrences']
    })

@app.route('/ping')
def ping():
    return jsonify(status="ok", words_loaded=len(words_index))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
