import re
import sys
from collections import defaultdict

def highlight_word(word, roots, frequency):
    """
    Wrap each letter in 'word' that appears in the 'roots' set
    with a <span> tag having the 'highlight-root' CSS class.
    Also, update the frequency counter for each highlighted letter.
    """
    highlighted = ""
    for char in word:
        if char in roots:
            highlighted += f"<span class='highlight-root'>{char}</span>"
            frequency[char] += 1  # update the count
        else:
            highlighted += char
    return highlighted

def process_verse(verse, roots, frequency):
    """
    Process a single verse:
    - Remove any leading verse numbering (assumes a pattern like "2|83|")
    - Split the verse into words and apply highlighting per word
    - Return the highlighted verse (as HTML)
    """
    verse = verse.strip()
    # Remove leading numbering if present (adjust regex if needed).
    verse = re.sub(r"^\d+\|\d+\|\s*", "", verse)
    words = verse.split()
    highlighted_words = [highlight_word(word, roots, frequency) for word in words]
    return " ".join(highlighted_words)

def generate_frequency_table(frequency):
    """
    Generate an HTML table from the frequency dictionary.
    """
    table_html = "<table border='1' cellspacing='0' cellpadding='5'>\n"
    table_html += "  <tr><th>Letter</th><th>Frequency</th></tr>\n"
    for letter, count in sorted(frequency.items()):
        table_html += f"  <tr><td>{letter}</td><td>{count}</td></tr>\n"
    table_html += "</table>\n"
    return table_html

def main(input_filename, output_filename, roots):
    # Initialize a frequency counter for the roots.
    frequency = defaultdict(int)

    try:
        # Read all verses from the Quran text file.
        with open(input_filename, "r", encoding="utf8") as infile:
            verses = infile.readlines()
    except Exception as e:
        sys.exit(f"Error reading input file: {e}")

    try:
        with open(output_filename, "w", encoding="utf8") as outfile:
            # Write the HTML header and basic CSS.
            outfile.write("<!DOCTYPE html>\n<html>\n<head>\n")
            outfile.write("  <meta charset='UTF-8'>\n")
            outfile.write("  <style>\n")
            outfile.write("    .highlight-root { color: red; font-weight: bold; }\n")
            outfile.write("    .verse { margin-bottom: 1em; }\n")
            outfile.write("    table { margin-bottom: 2em; border-collapse: collapse; }\n")
            outfile.write("    th, td { padding: 8px 12px; }\n")
            outfile.write("  </style>\n")
            outfile.write("  <title>Highlighted Quran with Frequency</title>\n")
            outfile.write("</head>\n<body>\n")

            # Process each verse and update frequency.
            highlighted_verses = []
            for line in verses:
                if line.strip() == "":
                    continue  # Skip empty lines.
                highlighted = process_verse(line, roots, frequency)
                highlighted_verses.append(f"<div class='verse'>{highlighted}</div>")

            # Write a frequency table.
            outfile.write("<h2>Root Letters Frequency</h2>\n")
            outfile.write(generate_frequency_table(frequency))

            # Write the highlighted Quran verses.
            outfile.write("<h2>Highlighted Quran Verses</h2>\n")
            for verse_html in highlighted_verses:
                outfile.write(verse_html + "\n")

            outfile.write("</body>\n</html>")

        print(f"Processing complete. Output is saved in '{output_filename}'.")
    except Exception as e:
        sys.exit(f"Error writing output file: {e}")

if __name__ == "__main__":
    # Define the set of letters you want to highlight.
    # You can adjust this set as needed.
    root_letters = {
        "ا", "ب", "ت", "ث", "ج", "ح", "خ", "د", "ذ", "ر", "ز",
        "س", "ش", "ص", "ض", "ط", "ظ", "ع", "غ", "ف", "ق", "ك",
        "ل", "م", "ن", "ه", "و", "ي"
    }

    # Set the names of your input and output files.
    input_filename = "quraan.txt"
    output_filename = "quraan_highlighted.html"

    main(input_filename, output_filename, root_letters)
