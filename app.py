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
    app.logger.info(f"🔎 ZIP path: {zip_path} exists? {os.path.exists(zip_path)}")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            app.logger.info(f"🔍 ZIP contains {len(names)} entries.")
            for name in names:
                if not name.lower().endswith('.xml'):
                    continue
                xml_bytes = zf.read(name)
                try:
                    root = ET.fromstring(xml_bytes)
                except ET.ParseError:
                    app.logger.warning(f"❌ Skipping malformed XML: {name}")
                    continue
                for al in root.findall('.//ArabicLexical'):
                    w_text = al.attrib.get('word', '').strip()
                    if not w_text:
                        continue
                    if w_text not in words_index:
                        words_index[w_text] = {
                            'prefix': al.attrib.get('prefix', '').strip(),
                            'root': al.attrib.get('root', '').strip(),
                            'suffix': al.attrib.get('suffix', '').strip(),
                            'pattern': al.attrib.get('pattern', '').strip(),
                            'occurrences': 0
                        }
                    words_index[w_text]['occurrences'] += 1
        app.logger.info(f"✅ Parsed {len(words_index)} unique words")
    except Exception as e:
        app.logger.error(f"❌ Error loading dataset: {e}")
    return words_index

words_index = load_dataset()

@app.route('/', methods=['GET'])
def home():
    return jsonify(message="Arabic Miracle API is running"), 200

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify(status="ok", words_loaded=len(words_index)), 200

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json(silent=True)
    if not data or 'word' not in data:
        return jsonify(error="Invalid JSON payload"), 400

    w = data['word'].strip()
    app.logger.info(f"Analyzing word: {w}")
    entry = words_index.get(w)
    if not entry:
        return jsonify(error="Word not found"), 404

    return jsonify({
        'prefix': entry['prefix'],
        'root': entry['root'],
        'suffix': entry['suffix'],
        'pattern': entry['pattern'],
        'occurrences': entry['occurrences']
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
