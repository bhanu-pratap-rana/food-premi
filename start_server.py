#!/usr/bin/env python3
"""
Simple server startup script for Food Premi
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from app import app
    print("Starting Food Premi server...")
    print("Database connection testing...")

    # Test database connection
    from database import get_db
    db = get_db()
    print(f"Database type: {type(db).__name__}")

    # Start server
    print("Starting Flask server on http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)

except Exception as e:
    print(f"Error starting server: {e}")
    import traceback
    traceback.print_exc()