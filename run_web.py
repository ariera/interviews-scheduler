#!/usr/bin/env python3
"""
Entry point for the Interview Scheduler Web Interface

This script starts the Flask web server from the project root.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from web.app import app

if __name__ == '__main__':
    print("🚀 Starting Interview Scheduler Web Interface...")
    print("🌐 Available at: http://localhost:5001")
    print("📁 Example files: examples/")
    print("⏳ Press Ctrl+C to stop")
    print("=" * 50)

    app.run(debug=False, host='0.0.0.0', port=5001)