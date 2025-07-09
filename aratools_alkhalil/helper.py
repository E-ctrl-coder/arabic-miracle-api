# aratools_alkhalil/helper.py

import requests

# URL of your running Alkhalil REST API
ALKHALIL_URL = "http://localhost:8080/analyze"

def analyze_with_alkhalil(word: str) -> list[dict]:
    """
    Calls the external Alkhalil REST API and returns its JSON analyses.
    """
    resp = requests.get(ALKHALIL_URL, params={'word': word})
    resp.raise_for_status()
    return resp.json()
