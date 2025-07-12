import os
import logging
import requests

# Load stub URL from ENV, fallback to the Render-onrender stub
ALKHALIL_URL = os.getenv(
    "ALKHALIL_URL",
    "https://alkhalil-rest-api.onrender.com/analyze"
)

# Log on import so you can verify in Render logs
logging.warning("aratools_alkhalil helper loaded with ALKHALIL_URL=%s", ALKHALIL_URL)

# (connect timeout, read timeout)
TIMEOUT = (5, 30)

def analyze_with_alkhalil(word: str) -> list[dict]:
    """
    Send `word` to the remote Alkhalil REST API and return all parses.
    If the request times out reading, returns an empty list.
    """
    try:
        resp = requests.get(
            ALKHALIL_URL,
            params={"word": word},
            timeout=TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()
    except requests.Timeout:
        logging.error("alkhalil REST call timed out for URL: %s", ALKHALIL_URL)
        return []
    except requests.RequestException as e:
        logging.error("alkhalil REST call error (%s): %s", ALKHALIL_URL, e)
        raise
