from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# Load OpenAI API key from Replit Secret
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to process a prompt using GPT
def process_with_llm(prompt_text):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt_text}
            ],
            max_tokens=100,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        # Fallback: Handle quota errors or other API issues
        print(f"LLM Error: {str(e)}")
        return (
            "LLM call failed (likely due to quota exhaustion). "
            "This is a simulated response for demonstration purposes."
        )

# Webhook endpoint to receive GitHub events
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Webhook received:", data)

    # Detect merged PR
    if data.get("event") == "pull_request" and data.get("merged") == "true":
        prompt = (
            f"A pull request was just merged in the repository '{data.get('repository')}' "
            f"by user '{data.get('sender')}'. Generate a concise changelog summary or merge announcement."
        )
    else:
        # Default push or other event
        prompt = f"Summarize this GitHub webhook event:\n{data}"

    # Call LLM
    llm_output = process_with_llm(prompt)

    print("LLM Output:", llm_output)
    return jsonify({
        "status": "received",
        "llm_output": llm_output
    }), 200

# Default route
@app.route('/', methods=['GET'])
def home():
    return "Webhook Server with LLM is Running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
