# aratools_alkhalil/helper.py

import os
import requests

# Either set this ENV var in Render (or Heroku), or hard-code your URL here:
#
#   e.g. https://my-alkhalil-rest-api.onrender.com/analyze
#
ALKHALIL_URL = os.environ.get(
    "ALKHALIL_URL",
    "https://<your-alkhalil-rest-api>.onrender.com/analyze"
)

def analyze_with_alkhalil(word: str) -> list[dict]:
    """
    Send `word` to the remote Alkhalil REST API and return all parses.
    """
    resp = requests.get(ALKHALIL_URL, params={"word": word}, timeout=5)
    resp.raise_for_status()
    return resp.json()
