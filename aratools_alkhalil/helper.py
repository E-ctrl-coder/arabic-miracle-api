# aratools_alkhalil/helper.py

from camel_tools.morphology.analyzer import Analyzer

# instantiate CAMeL Tools analyzer once
_analyzer = Analyzer.builtin_analyzer()

def analyze_with_camel(word: str) -> list[dict]:
    """
    Returns a list of dicts in Aratools-style:
    [
      {
        'root':…,
        'pattern':…,
        'prefixes':…,
        'suffixes':…,
        'stem':…,
        'pos':…
      },
      …
    ]
    """
    results = []
    for a in _analyzer.analyze(word):
        results.append({
            'root':     a.get('root', '') or '',
            'pattern':  a.get('pattern', '') or '',
            'prefixes': a.get('prefixes', []) or [],
            'suffixes': a.get('suffixes', []) or [],
            'stem':     a.get('stem', '') or '',
            'pos':      a.get('pos', '') or ''
        })
    return results
