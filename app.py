# app.py

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS)
CORS(app)

# Configure your database URI (replace with your actual URI)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@host:port/database_name'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Example model (replace with your actual models)
class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    score = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Lead {self.business_name}>"

# Simple route for testing
@app.route('/')
def hello_world():
    return jsonify(message="Hello, World!")

# Example route to get all leads from the database (if you have any data)
@app.route('/leads')
def get_leads():
    leads = Lead.query.all()
    return jsonify([lead.business_name for lead in leads])

# If running locally, run the Flask app directly (optional)
if __name__ == "__main__":
    app.run(debug=True)
