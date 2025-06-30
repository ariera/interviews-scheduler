#!/usr/bin/env python3
"""
Local Web Development Server for Interview Scheduler

This script starts both the API backend and serves the frontend locally.
"""

import subprocess
import sys
import os
import signal
import time
from pathlib import Path

def main():
    print("🚀 Interview Scheduler - Local Web Development")
    print("==============================================")

    # Check if we're in the right directory
    if not Path("api/app.py").exists():
        print("❌ Error: api/app.py not found. Please run this from the project root.")
        sys.exit(1)

    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Virtual environment not detected. Consider activating one.")

    print("📥 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)

    print("🌐 Starting local development servers...")
    print("API: http://localhost:5001")
    print("Frontend: http://localhost:8000")
    print("Press Ctrl+C to stop both servers")
    print()

    # Start API server
    api_process = subprocess.Popen([
        sys.executable, "api/app.py"
    ], cwd=os.getcwd())

    # Give API a moment to start
    time.sleep(2)

    # Start frontend server
    frontend_process = subprocess.Popen([
        sys.executable, "-m", "http.server", "8000"
    ], cwd="docs")

    try:
        # Wait for processes
        api_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        api_process.terminate()
        frontend_process.terminate()

        # Wait for graceful shutdown
        try:
            api_process.wait(timeout=5)
            frontend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("⚠️  Force killing processes...")
            api_process.kill()
            frontend_process.kill()

        print("✅ Servers stopped")

if __name__ == "__main__":
    main()