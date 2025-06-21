from flask import Flask, request, jsonify, send_file, abort
import openai
import os
import re
import sys
from collections import defaultdict

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")  # Ensure this environment variable is set

# -------------------------------------------
# GPT‑3.5 Analysis Functions (Your Existing Code)
# -------------------------------------------
def extract_root_line(response_text):
    """
    Finds the line that includes root letters.
    """
    for line in response_text.splitlines():
        if "root letter" in line.lower() or "Root letters" in line:
            match = re.search(r'[:：]\s*(.+)', line)
            if match:
                return match.group(1).strip()
    return None

def highlight_root_letters(letters):
    """
    Wrap each Arabic root letter in a span with the 'highlight' class.
    """
    clean = letters.replace(" ", "")
    return ''.join(f"<span class='highlight'>{char}</span>" for char in clean)

@app.route('/analyze', methods=['POST'])
def analyze():
    user_input = request.json.get("text", "").strip()

    prompt = f"""
    Analyze the Arabic input: "{user_input}"

    Return:
    1. Root letters (in Arabic).
    2. The English meaning of the root.
    3. The full sentence/contextual English translation.
    4. Quranic usage: number of times the root appears and 1–2 examples.
    5. Morphological pattern (وزن صرفي).

    DO NOT include HTML. Format using plain numbered lines.
    """

    try:
        reply = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        response_text = reply.choices[0].message.content

        # Highlight root letters in the GPT‑3.5 analysis output
        root_text = extract_root_line(response_text)
        if root_text:
            highlighted = highlight_root_letters(root_text)
            response_text = response_text.replace(root_text, highlighted)

        return jsonify({
            "analysis": response_text.replace("\n", "<br>")
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

# -------------------------------------------
# Quran Text Processing Functions
# -------------------------------------------
def highlight_word_quran(word, roots, frequency):
    """
    For each letter in the word, if it is in the target roots, wrap it in a span.
    Count its occurrence in the frequency dictionary.
    """
    highlighted = ""
    for char in word:
        if char in roots:
            highlighted += f"<span class='highlight'>{char}</span>"
            frequency[char] += 1  # Update frequency count
        else:
            highlighted += char
    return highlighted

def process_verse_quran(verse, roots, frequency):
    """
    Process a single verse from quraan.txt:
    Remove any leading numbering (e.g., "2|83|"), split the verse into words,
    and apply highlighting to each word.
    """
    verse = verse.strip()
    # Remove leading numbering such as "2|83|"
    verse = re.sub(r"^\d+\|\d+\|\s*", "", verse)
    words = verse.split()
    highlighted_words = [highlight_word_quran(word, roots, frequency) for word in words]
    return " ".join(highlighted_words)

def generate_frequency_table(frequency):
    """
    Generate an HTML table that displays the frequency of each highlighted letter.
    """
    table_html = "<table border='1' cellspacing='0' cellpadding='5'>\n"
    table_html += "  <tr><th>Letter</th><th>Frequency</th></tr>\n"
    for letter, count in sorted(frequency.items()):
        table_html += f"  <tr><td>{letter}</td><td>{count}</td></tr>\n"
    table_html += "</table>\n"
    return table_html

def process_quran(input_filename, output_filename, roots):
    """
    Read the raw Quran text from quraan.txt, process each verse by highlighting
    the target root letters, and generate an HTML file that includes a frequency
    table at the top.
    """
    frequency = defaultdict(int)
    highlighted_verses = []
    
    try:
        with open(input_filename, "r", encoding="utf8") as infile:
            verses = infile.readlines()
    except Exception as e:
        sys.exit(f"Error reading input file: {e}")

    for line in verses:
        if line.strip() == "":
            continue
        hv = process_verse_quran(line, roots, frequency)
        highlighted_verses.append(f"<div class='verse'>{hv}</div>")
    
    html_content = "<!DOCTYPE html>\n<html>\n<head>\n"
    html_content += "  <meta charset='UTF-8'>\n"
    html_content += "  <style>\n"
    html_content += "    .highlight { color: red; font-weight: bold; }\n"
    html_content += "    .verse { margin-bottom: 1em; }\n"
    html_content += "    table { margin-bottom: 2em; border-collapse: collapse; }\n"
    html_content += "    th, td { padding: 8px 12px; }\n"
    html_content += "  </style>\n"
    html_content += "  <title>Highlighted Quran</title>\n"
    html_content += "</head>\n<body>\n"
    html_content += "<h2>Root Letters Frequency</h2>\n"
    html_content += generate_frequency_table(frequency)
    html_content += "<h2>Highlighted Quran Verses</h2>\n"
    for verse in highlighted_verses:
        html_content += verse + "\n"
    html_content += "</body>\n</html>"
    
    try:
        with open(output_filename, "w", encoding="utf8") as outfile:
            outfile.write(html_content)
        print(f"Processing complete. Output saved in '{output_filename}'.")
    except Exception as e:
        sys.exit(f"Error writing output file: {e}")

# Configuration variables for Quran text processing
INPUT_FILE = "quraan.txt"
OUTPUT_FILE = "quraan_highlighted.html"
ROOT_LETTERS = {
    "ا", "ب", "ت", "ث", "ج", "ح", "خ", "د", "ذ", "ر", "ز",
    "س", "ش", "ص", "ض", "ط", "ظ", "ع", "غ", "ف", "ق", "ك",
    "ل", "م", "ن", "ه", "و", "ي"
}

# -------------------------------------------
# Web Endpoint to Serve the Processed Quran File
# -------------------------------------------
@app.route("/")
def index():
    """
    Serve the generated quraan_highlighted.html file.
    """
    if os.path.exists(OUTPUT_FILE):
        return send_file(OUTPUT_FILE, mimetype="text/html")
    else:
        return abort(404)

# -------------------------------------------
# Application Entry Point
# -------------------------------------------
if __name__ == "__main__":
    # Process the Quran text once at startup if the output file doesn't exist.
    if not os.path.exists(OUTPUT_FILE):
        process_quran(INPUT_FILE, OUTPUT_FILE, ROOT_LETTERS)
    # Bind to the port provided by the environment (e.g., by Render) or default to 5000.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
