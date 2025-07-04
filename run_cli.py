#!/usr/bin/env python3
"""
Entry point for the Interview Scheduler Command Line Interface

This script runs the CLI from the project root.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scheduler.cli import main

if __name__ == '__main__':
    main()