import xml.etree.ElementTree as ET
import json

# Load the Nemlar XML dataset (must exist in the same directory)
tree = ET.parse("Nemlar.xml")
root = tree.getroot()

word_data = {}

# Loop through each word entry
for lexical in root.iter("ArabicLexical"):
    word = lexical.attrib.get("word")
    if word and word not in word_data:
        word_data[word] = {
            "root": lexical.attrib.get("root", ""),
            "pattern": lexical.attrib.get("pattern", ""),
            "lemma": lexical.attrib.get("lemma", ""),
            "prefix": lexical.attrib.get("prefix", ""),
            "suffix": lexical.attrib.get("suffix", "")
        }

# Output the dictionary to JSON
with open("word_roots.json", "w", encoding="utf-8") as f:
    json.dump(word_data, f, ensure_ascii=False, indent=2)

print(f"✅ Extracted {len(word_data)} entries into word_roots.json")
