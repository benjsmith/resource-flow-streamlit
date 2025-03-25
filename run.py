#!/usr/bin/env python3
import os
import sys
import subprocess

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Run Streamlit
subprocess.run(["streamlit", "run", "app/main.py"]) 