# backend/app.py
"""
Main backend entry point.

This file will start the server, initialize the app, connect shared
components like routes and database setup, and run the main application.
It acts as the central startup file for the backend.
"""

from flask import Flask
from routes import register_routes
from database import init_db