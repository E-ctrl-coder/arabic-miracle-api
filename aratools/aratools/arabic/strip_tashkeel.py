import re

DIACRITICS_RE = re.compile(r'[\u064B-\u0652\u0610-\u061A\u06D6-\u06ED]')

def strip_tashkeel(text):
    return DIACRITICS_RE.sub('', text)
