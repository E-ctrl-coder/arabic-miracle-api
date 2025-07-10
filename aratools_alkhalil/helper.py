# aratools_alkhalil/helper.py

import requests

# Hard-code your live Alkhalil endpoint here:
# e.g. "https://arabic-miracle-api.onrender.com/analyze"
ALKHALIL_URL = "https://arabic-miracle-api.onrender.com/analyze"

def analyze_with_alkhalil(word: str) -> list[dict]:
    """
    Send `word` to the remote Alkhalil REST API and return all parses.
    """
    resp = requests.get(ALKHALIL_URL, params={"word": word}, timeout=5)
    resp.raise_for_status()
    return resp.json()
