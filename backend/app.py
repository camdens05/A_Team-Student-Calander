# backend/app.py
"""
Main backend entry point.

This file will start the server, initialize the app, connect shared
components like routes and database setup, and run the main application.
It acts as the central startup file for the backend.
"""

from flask import Flask

from database import init_db
from routes import register_routes


# Create and configure the Flask application.
def create_app():
    app = Flask(__name__)

    init_db()
    register_routes(app)

    return app


# Start the backend server when this file is run directly.
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)