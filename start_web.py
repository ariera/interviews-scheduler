#!/usr/bin/env python3
"""
Start script for the Interview Scheduler Web Interface

This script starts the Flask web server and provides helpful information
about accessing the interface.
"""

import sys
import os
import webbrowser
import time
from pathlib import Path

def main():
    """Start the web interface with helpful instructions."""

    # Check if we're in the right directory
    if not Path('app.py').exists():
        print("❌ Error: app.py not found in current directory")
        print("Please run this script from the interview_scheduler directory")
        sys.exit(1)

    # Check if templates directory exists
    if not Path('templates').exists():
        print("❌ Error: templates directory not found")
        print("Please ensure the web interface files are properly installed")
        sys.exit(1)

    print("🚀 Starting Interview Scheduler Web Interface...")
    print()
    print("📋 Features:")
    print("  • Drag & drop YAML configuration upload")
    print("  • Multiple scheduling solutions (up to 3)")
    print("  • Interactive solution comparison")
    print("  • Download results as JSON")
    print()
    print("🌐 The web interface will be available at:")
    print("   http://localhost:5001")
    print()
    print("📁 Example configuration file: example-web.yaml")
    print()
    print("⏳ Starting server... (Press Ctrl+C to stop)")
    print("=" * 50)

    # Try to open browser after a short delay
    def open_browser():
        time.sleep(2)
        try:
            webbrowser.open('http://localhost:5001')
        except:
            pass  # Browser opening is optional

    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    # Start the Flask app
    try:
        from app import app
        app.run(debug=False, host='0.0.0.0', port=5001)
    except KeyboardInterrupt:
        print("\n👋 Web interface stopped")
    except Exception as e:
        print(f"\n❌ Error starting web interface: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()