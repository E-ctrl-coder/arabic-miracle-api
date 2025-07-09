import os
import zipfile
import xml.etree.ElementTree as ET
import re
from collections import defaultdict, Counter
from flask import Flask, jsonify, request, current_app
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Toggle our hybrid analyzer on/off
app.config['USE_HYBRID_ALKHALIL'] = True

# Import the HTTP-based Alkhalil helper instead of CAMeL
from aratools_alkhalil.helper import analyze_with_alkhalil

# remove diacritics
DIACRITICS_PATTERN = re.compile(
    r'[\u0610-\u061A\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]'
)

# strip invisible chars (BOM, zero‐width, non‐breaking space)
HIDDEN_CHARS = re.compile(r'[\uFEFF\u200B\u00A0]')

# normalize letter variants
NORMALIZE_MAP = str.maketrans({
    'آ': 'ا', 'أ': 'ا', 'إ': 'ا',
    'ة': 'ه', 'ى': 'ي', 'ـ': ''
})

# common Arabic prefixes and particles
PREFIXES = [
    'ال', 'و', 'ف', 'ب', 'ك', 'ل', 'س',
    'است'
]

# common pronoun/plural/dual suffixes
SUFFIXES = [
    'ه', 'ها', 'هم', 'هن', 'كما', 'نا', 'ني', 'ي',
    'وا', 'ان', 'ين', 'ون', 'ات', 'ة', 'ك'
]

def normalize_arabic(text: str) -> str:
    """Remove hidden chars, strip tashkeel, normalize alef/ta-marbuta/tatweel."""
    if not text:
        return ''
    text = HIDDEN_CHARS.sub('', text)
    text = text.translate(NORMALIZE_MAP)
    return DIACRITICS_PATTERN.sub('', text)

def try_strip_affixes(word: str):
    """
    Yield (prefix, core, suffix) for each affix-stripping possibility.
    Skip the no-affix case in analyze().
    """
    for pre in PREFIXES:
        if word.startswith(pre) and len(word) > len(pre):
            yield pre, word[len(pre):], None

    for suf in SUFFIXES:
        if word.endswith(suf) and len(word) > len(suf):
            yield None, word[:-len(suf)], suf

    for pre in PREFIXES:
        if word.startswith(pre) and len(word) > len(pre):
            mid = word[len(pre):]
            for suf in SUFFIXES:
                if mid.endswith(suf) and len(mid) > len(suf):
                    yield pre, mid[:-len(suf)], suf

def load_dataset(zip_path='data/Nemlar_dataset.zip'):
    idx = {}
    with zipfile.ZipFile(zip_path
