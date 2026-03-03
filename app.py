from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# Create Flask app
app = Flask(__name__)

# Enable CORS (allows frontend to connect)
CORS(app)

# -------------------
# ROOT ROUTE
# -------------------
@app.route("/")
def home():
    return "Backend is live!"

# -------------------
# TEST API ROUTE
# -------------------
@app.route("/api/hello", methods=["GET"])
def hello():
    return jsonify({
        "status": "success",
        "message": "Hello from backend!"
    })

# -------------------
# EXAMPLE POST ROUTE
# -------------------
@app.route("/api/data", methods=["POST"])
def receive_data():
    data = request.json

    return jsonify({
        "status": "received",
        "you_sent": data
    })

# -------------------
# GET LEADS
# -------------------
@app.route("/api/getLeads", methods=["POST"])
def get_leads():
    data = request.json

    return jsonify({
        "status": "success",
        "leads": [
            {
                "id": 1,
                "title": "Example Lead",
                "content": "This is a test lead",
                "score": 85,
                "intent": "high"
            }
        ]
    })

# -------------------
# ANALYZE LEAD
# -------------------
@app.route("/api/analyzeLead", methods=["POST"])
def analyze_lead():
    data = request.json

    return jsonify({
        "status": "success",
        "analysis": {
            "score": 92,
            "intent": "high",
            "reason": "Contains buying signals"
        }
    })

# -------------------
# UPDATE LEAD
# -------------------
@app.route("/api/updateLead", methods=["POST"])
def update_lead():
    data = request.json

    return jsonify({
        "status": "success",
        "message": "Lead updated successfully"
    })

# -------------------
# REQUIRED FOR RENDER
# -------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
