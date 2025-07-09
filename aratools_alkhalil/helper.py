# aratools_alkhalil/helper.py

from alkhalil_pipeline.pipelines import MorphologyPipeline

# initialize Alkhalil pipeline once
_pipeline = MorphologyPipeline()

def analyze_word_with_alkhalil(word):
    """
    Returns a list of dicts in Aratools-style:
    [{'root':…, 'pattern':…, 'prefixes':…, 'suffixes':…, 'stem':…, 'pos':…}, …]
    """
    analyses = _pipeline.process(word)
    results = []
    for a in analyses:
        results.append({
            'root': '-'.join(a['root']),
            'pattern': a['pattern'],
            'prefixes': a.get('prefixes', []),
            'suffixes': a.get('suffixes', []),
            'stem': a.get('stem'),
            'pos': a.get('pos')
        })
    return results
