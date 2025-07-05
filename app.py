import os
import zipfile
import xml.etree.ElementTree as ET
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def load_dataset():
    words_index = {}
    zip_path = 'data/Nemlar_dataset.zip'   # ← Ensure this matches exactly your GitHub file

    # 1) Confirm file exists
    exists = os.path.exists(zip_path)
    print(f"🔎 ZIP path: {zip_path}   exists? {exists}")

    if not exists:
        return {}

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            print(f"🔍 ZIP contains {len(names)} entries. Sample:", names[:10])

            # 2) Debug first XML file
            first_xml = next((n for n in names if n.lower().endswith('.xml')), None)
            if first_xml:
                xml_bytes = zf.read(first_xml)
                snippet = xml_bytes[:500].decode('utf-8', 'ignore')
                print("📝 First XML filename:", first_xml)
                print("📝 Snippet of first XML:\n", "\n".join(snippet.splitlines()[:10]))

                root_elem = ET.fromstring(xml_bytes)
                child_tags = [child.tag for child in list(root_elem)[:10]]
                print("🏷️ root.tag:", root_elem.tag, "child tags:", child_tags)
            else:
                print("⚠️ No XML files found in ZIP.")

            # 3) Attempt to parse <word> tags (likely none)
            for name in names:
                if not name.lower().endswith('.xml'):
                    continue
                xml_bytes = zf.read(name)
                tree = ET.fromstring(xml_bytes)
                for w in tree.findall('.//word'):
                    text = w.findtext('text','').strip()
                    words_index[text] = {
                        'prefix':  w.findtext('prefix','').strip(),
                        'root':    w.findtext('root','').strip(),
                        'suffix':  w.findtext('suffix','').strip(),
                        'pattern': w.findtext('pattern','').strip()
                    }

            print(f"✅ Parsed {len(words_index)} <word> entries from all XMLs")
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")

    return words_index

words_index = load_dataset()

@app.route('/analyze', methods=['POST'])
def analyze():
    w = (request.get_json(force=True) or {}).get('word','').strip()
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
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
