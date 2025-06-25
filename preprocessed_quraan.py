import json
from camel_tools.tokenizers.word import simple_word_tokenize
from camel_tools.morphology.analyzer import Analyzer

analyzer = Analyzer.builtin_analyzer()
verses = []

with open('quraan.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines:
    parts = line.strip().split('|')
    if len(parts) != 3:
        continue
    surah, ayah, text = parts
    tokens = simple_word_tokenize(text)
    root_map = []

    for word in tokens:
        analyses = analyzer.analyze(word)
        if analyses:
            best = analyses[0]
            root = best.get('root', '')
            root_map.append((word, root))
        else:
            root_map.append((word, ''))

    verses.append({
        'surah': surah,
        'ayah': ayah,
        'text': text,
        'roots': root_map
    })

with open('quraan_rooted.json', 'w', encoding='utf-8') as f:
    json.dump(verses, f, ensure_ascii=False, indent=2)
