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

    # Allow the frontend (served on a different origin/port) to reach the API.
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.route("/api/<path:path>", methods=["OPTIONS"])
    def handle_options(path):
        return "", 204

    init_db()
    register_routes(app)

    return app


# Start the backend server when this file is run directly.
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)