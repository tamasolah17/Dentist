from flask import Flask, request, jsonify, render_template
from agent import handle_message
from flask_cors import CORS
app2 = Flask(__name__)
CORS(app2)
user_sessions = {}
@app2.route("/chat", methods=["POST","OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return 'LOL', 200
    data = request.get_json()
    user_id = data.get("user_id")
    message = data.get("message", "").strip()

    if user_id not in user_sessions:
        user_sessions[user_id] = {}

    session = user_sessions[user_id]


    if message == "":
        return jsonify({
            "intent": "welcome_message",
            "confidence": 1.0,
            "reply":  "Hi 👋 Welcome to our clinic. I am your personal Assistant. How can I help you?:)."
        }

        )
    result = handle_message(user_id, message, session)
    return jsonify(result)

@app2.route("/")
def index():
    return render_template("dentistpage.html")

if __name__ == "__main__":
    app2.run(host="0.0.0.0", port=5000)
print("lol")
