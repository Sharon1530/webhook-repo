from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# Set your OpenAI API key
# Option 1: Use environment variable
openai.api_key = os.getenv("OPENAI_KEY")

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
        return f"LLM Error: {str(e)}"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Webhook received:", data)

    # Create a simple prompt for GPT
    prompt = f"Summarize this GitHub webhook event:\n{data}"

    # Call OpenAI to process the event
    llm_output = process_with_llm(prompt)
    print("LLM Output:", llm_output)

    return jsonify({
        "status": "received",
        "llm_output": llm_output
    }), 200

@app.route('/', methods=['GET'])
def home():
    return "Webhook Server with LLM is Running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
