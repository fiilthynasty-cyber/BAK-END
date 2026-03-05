"""AI Lead Vacuum project structure reference.

This module keeps the intended folder/file layout in valid Python form so it can
be imported or executed without syntax errors.
"""

PROJECT_STRUCTURE = """AI_Lead_Vacuum/

# Backend Folder
backend/
    app.py                 # Main FastAPI/Flask application
    models.py              # Database models
    routes/
        auth.py            # Authentication routes
        leads.py           # Lead CRUD and endpoints
        payments.py        # Stripe/Payment routes
    services/
        ai_scraper.py      # AI-driven web scraping & lead detection
        lead_scoring.py    # Lead scoring ML logic
        notification.py    # Email/SMS/alerts
    utils/
        db.py              # Database connection utility
        security.py        # JWT, encryption utilities

# Frontend Folder
frontend/
    src/
        components/
            Dashboard.jsx
            LeadCard.jsx
            SubscriptionForm.jsx
            AlertModal.jsx
        pages/
            Login.jsx
            Signup.jsx
            Leads.jsx
        services/
            api.js           # Axios or fetch API calls
        App.jsx
    package.json            # npm dependencies and scripts

# Worker Folder
worker/
    scraper_worker.py       # Distributed scraping worker script
    queue_manager.py        # Task queue handling (Redis/RabbitMQ)
    config.py               # Worker configuration

# AI Models Folder
ai_models/
    pain_detector.py        # NLP model to detect customer pain points
    lead_predictor.py       # Predictive lead scoring model

# Deployment Files
Dockerfile                  # Docker container build
docker-compose.yml          # Orchestration of services

# Documentation
README.md                   # Project overview and instructions
"""


def get_project_structure() -> str:
    """Return the project structure as a printable string."""
    return PROJECT_STRUCTURE


if __name__ == "__main__":
    print(get_project_structure())
