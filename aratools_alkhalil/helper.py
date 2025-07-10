# aratools_alkhalil/helper.py

import requests

# Hard-code your live Alkhalil endpoint here (no < > brackets):
ALKHALIL_URL = "https://arabic-miracle-api.onrender.com/analyze"

# (connect timeout, read timeout)
TIMEOUT = (5, 30)

def analyze_with_alkhalil(word: str) -> list[dict]:
    """
    Send `word` to the remote Alkhalil REST API and return all parses.
    If the request times out reading, returns an empty list.
    """
    try:
        resp = requests.get(ALKHALIL_URL, params={"word": word}, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.Timeout:
        # The remote service took too long to respond
        return []
    except requests.RequestException as e:
        # Propagate other HTTP errors
        raise
