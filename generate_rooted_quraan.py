import json
from camel_tools.tokenizers.word import simple_word_tokenize
from camel_tools.morphology.analyzer import Analyzer

# Load Quran text
with open('quraan.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

analyzer = Analyzer.builtin_analyzer()
rooted_data = []

for line in lines:
    if not line.strip():
        continue
    try:
        sura, aya, text = line.strip().split('|')
    except ValueError:
        continue  # skip malformed lines

    tokens = simple_word_tokenize(text)
    rooted_line = []

    for word in tokens:
        analyses = analyzer.analyze(word)
        root = ''
        if analyses:
            # Use the first valid root
            for a in analyses:
                if 'root' in a and a['root'] not in ['', '0']:
                    root = a['root']
                    break
        rooted_line.append({
            'word': word,
            'root': root
        })

    rooted_data.append({
        'sura': int(sura),
        'aya': int(aya),
        'text': text,
        'words': rooted_line
    })

# Save as JSON
with open('quraan_rooted.json', 'w', encoding='utf-8') as f:
    json.dump(rooted_data, f, ensure_ascii=False, indent=2)

print("✅ Done: quraan_rooted.json generated.")
