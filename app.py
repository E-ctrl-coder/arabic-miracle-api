import os
import zipfile
import xml.etree.ElementTree as ET
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def load_dataset():
    words_index = {}
    zip_path = 'data/nemlar_dataset.zip'    # ← adjust to your exact filename
    print(f"🔎 Attempting to open ZIP at: {zip_path}")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            print(f"🔍 ZIP contains {len(names)} total entries.")
            print("📋 Sample entries:", names[:10])

            for name in names:
                if not name.lower().endswith('.xml'):
                    continue
                xml_bytes = zf.read(name)
                tree = ET.fromstring(xml_bytes)
                for w in tree.findall('.//word'):
                    text = w.findtext('text', '').strip()
                    words_index[text] = {
                        'prefix':  w.findtext('prefix', '').strip(),
                        'root':    w.findtext('root', '').strip(),
                        'suffix':  w.findtext('suffix', '').strip(),
                        'pattern': w.findtext('pattern', '').strip()
                    }

        print(f"✅ Loaded {len(words_index)} entries from {zip_path}")
    except FileNotFoundError:
        print("❌ ERROR: ZIP file not found at that path!")
    except Exception as e:
        print(f"❌ Failed to load dataset: {e}")

    return words_index

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
        'occurrences': entry.get('occurrences', 0)
    })

@app.route('/ping')
def ping():
    return jsonify(status="ok", words_loaded=len(words_index))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
