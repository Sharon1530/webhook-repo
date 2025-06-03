from flask import Flask, request, jsonify, render_template, send_from_directory
import openai
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os
import pytz

load_dotenv()

print("Loaded MONGO_URI:", os.getenv("MONGO_URI"))  # <-- Add this line

app = Flask(__name__, static_folder='static', template_folder='templates')

# API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# MongoDB
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["webhook_db"]
events = db["events"]

# Generate GPT summary (optional)
def process_with_llm(prompt_text):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt_text}],
            max_tokens=100,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM Error: {str(e)}")
        return "Summary unavailable."

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event_type = request.headers.get("X-GitHub-Event", "unknown")

    # Defaults
    author = "unknown"
    from_branch = "unknown"
    to_branch = "main"
    repo = data.get("repository", {}).get("name", "unknown")

    if event_type == "push":
        author = data.get("pusher", {}).get("name", "unknown")
        to_branch = data.get("ref", "").split("/")[-1]

    elif event_type == "pull_request":
        pr = data.get("pull_request", {})
        author = pr.get("user", {}).get("login", "unknown")
        from_branch = pr.get("head", {}).get("ref", "unknown")
        to_branch = pr.get("base", {}).get("ref", "main")
        if pr.get("merged", False):
            event_type = "merge"

    # Prompt for LLM
    if event_type == "merge":
        prompt = f"{author} merged a pull request from {from_branch} to {to_branch} in {repo}."
    elif event_type == "push":
        prompt = f"{author} pushed to {to_branch} in {repo}."
    elif event_type == "pull_request":
        prompt = f"{author} submitted a pull request from {from_branch} to {to_branch} in {repo}."
    else:
        prompt = f"Summarize this event: {data}"

    summary = process_with_llm(prompt)

    # Save to DB
    events.insert_one({
        "author": author,
        "event_type": event_type,
        "from_branch": from_branch,
        "to_branch": to_branch,
        "timestamp": datetime.utcnow(),
        "summary": summary
    })

    return jsonify({"status": "received", "summary": summary})

# Index supports GET for page, POST returns 405
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return jsonify({"error": "POST method not allowed on root. Use /webhook for POST events."}), 405
    return render_template("index.html")

@app.route('/events/latest')
def latest_events():
    recent_events = events.find().sort("timestamp", -1).limit(10)
    output = []

    for e in recent_events:
        utc_time = e['timestamp'].replace(tzinfo=pytz.utc)
        timestamp = utc_time.strftime("%d %B %Y - %I:%M %p UTC")
        action = e.get("event_type")

        if action == "push":
            text = f'"{e["author"]}" pushed to "{e["to_branch"]}" on {timestamp}'
        elif action == "pull_request":
            text = f'"{e["author"]}" submitted a pull request from "{e["from_branch"]}" to "{e["to_branch"]}" on {timestamp}'
        elif action == "merge":
            text = f'"{e["author"]}" merged branch "{e["from_branch"]}" to "{e["to_branch"]}" on {timestamp}'
        else:
            text = f'{e["author"]} triggered {action} on {timestamp}'

        output.append({"text": text, "summary": e.get("summary", "")})

    return jsonify(output)

# For serving frontend assets
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Test POST endpoint to /webhook internally
@app.route('/test-webhook', methods=['GET'])
def test_webhook():
    import requests
    # Build sample test data matching your webhook expected JSON
    test_data = {
        "repository": {"name": "test-repo"},
        "pusher": {"name": "tester"},
        "ref": "refs/heads/main"
    }
    # Use Flask's own URL for testing - assumes app runs on port 3000
    webhook_url = "http://localhost:3000/webhook"
    try:
        resp = requests.post(webhook_url, json=test_data, headers={"X-GitHub-Event": "push"})
        return jsonify({"test_webhook_response": resp.json()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
