from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("✅ Webhook received:", data)
    return jsonify({"status": "received"}), 200

@app.route('/', methods=['GET'])
def home():
    return "🚀 Webhook server is running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
