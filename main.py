from flask import Flask, request, jsonify, render_template, send_from_directory
import openai
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
from threading import Thread
import os
import pytz

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

# API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# MongoDB
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["webhook_db"]
events = db["events"]

# Generate GPT summary
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

# Async event handler
def handle_event_async(data, event_type):
    try:
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

        if event_type == "merge":
            prompt = f"{author} merged a pull request from {from_branch} to {to_branch} in {repo}."
        elif event_type == "push":
            prompt = f"{author} pushed to {to_branch} in {repo}."
        elif event_type == "pull_request":
            prompt = f"{author} submitted a pull request from {from_branch} to {to_branch} in {repo}."
        else:
            prompt = f"Summarize this event: {data}"

        summary = process_with_llm(prompt)

        events.insert_one({
            "author": author,
            "event_type": event_type,
            "from_branch": from_branch,
            "to_branch": to_branch,
            "timestamp": datetime.utcnow(),
            "summary": summary
        })

    except Exception as e:
        print(f"Error in async handler: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        event_type = request.headers.get("X-GitHub-Event", "unknown")

        # Run event processing in a separate thread
        Thread(target=handle_event_async, args=(data, event_type)).start()

        # Respond immediately
        return jsonify({"status": "received"}), 200

    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
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

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
