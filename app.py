from flask import Flask, request, jsonify, send_file, abort
import openai
import os
import re
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all endpoints

# Set up logging for debugging
app.logger.setLevel(logging.DEBUG)

# Set up the OpenAI API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    app.logger.error("OPENAI_API_KEY environment variable is not set!")

# --- Temporary GET route for quick testing ---
@app.route('/analyze', methods=['GET'])
def analyze_get():
    return "Analyzer endpoint is up (GET)", 200

# --- POST endpoint that calls the OpenAI ChatCompletion synchronously ---
@app.route('/analyze', methods=['POST'])
def analyze_post():
    app.logger.debug("Received /analyze POST request from %s", request.remote_addr)
    
    # Log the raw request data for debugging
    raw_data = request.get_data(as_text=True)
    app.logger.debug("Raw request data: %s", raw_data)
    
    # Attempt to get JSON data; fallback to form or query parameters if necessary.
    data = request.get_json(silent=True) or {}
    if not data.get("text", "").strip():
        if request.form.get("text", "").strip():
            data["text"] = request.form.get("text")
        elif request.args.get("text", "").strip():
            data["text"] = request.args.get("text")
    
    app.logger.debug("Parsed data: %s", data)
    
    user_input = data.get("text", "").strip()
    if not user_input:
        app.logger.error("No text provided in the request.")
        return jsonify({"error": "No text provided"}), 400
    
    app.logger.debug("User input: %s", user_input)
    
    # Build the prompt for GPT‑3.5
    prompt = (
        f'Analyze the Arabic input: "{user_input}"\n\n'
        "Return:\n"
        "1. Root letters (in Arabic).\n"
        "2. The English meaning of the root.\n"
        "3. The full sentence/contextual English translation.\n"
        "4. Quranic usage: number of times the root appears and 1–2 examples.\n"
        "5. Morphological pattern (وزن صرفي).\n\n"
        "DO NOT include HTML. Format using plain numbered lines."
    )
    
    try:
        # Synchronous call to the ChatCompletion API.
        reply = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in Arabic linguistic analysis with detailed knowledge of Quranic texts."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
        )
        
        # Extract the content from the GPT‑3.5 response.
        response_text = reply['choices'][0]['message']['content']
        app.logger.debug("Raw GPT‑3.5 response: %s", response_text)
        
        # Optionally, extract and highlight the part that lists root letters.
        root_text = None
        for line in response_text.splitlines():
            if "root letter" in line.lower():
                match = re.search(r'[:：]\s*(.+)', line)
                if match:
                    root_text = match.group(1).strip()
                    break
        
        if root_text:
            app.logger.debug("Extracted root text: %s", root_text)
            highlighted = ''.join(
                f"<span class='highlight'>{char}</span>" for char in root_text.replace(" ", "")
            )
            response_text = response_text.replace(root_text, highlighted)
            app.logger.debug("Response after highlighting: %s", response_text)
        else:
            app.logger.warning("No root text found in GPT‑3.5 response.")
        
        # Return the processed analysis as JSON.
        return jsonify({"analysis": response_text.replace("\n", "<br>")})
    except Exception as e:
        app.logger.exception("Exception in /analyze endpoint:")
        return jsonify({"error": str(e)}), 500

# --- Serve a static Quran HTML if needed ---
@app.route("/")
def index():
    OUTPUT_FILE = "quraan_highlighted.html"
    if os.path.exists(OUTPUT_FILE):
        return send_file(OUTPUT_FILE, mimetype="text/html")
    else:
        return abort(404)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.logger.debug("Starting app on port %d", port)
    app.run(host="0.0.0.0", port=port)
