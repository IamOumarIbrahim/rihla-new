#!/usr/bin/env python3
"""
start_client.py  –  Start the Rihla Tkinter client application.

The API server (start_server.py) must already be running on localhost:5000.
"""
import subprocess
import sys
import os

client_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "main.py")

print("Starting Rihla client... (server must be running on localhost:5000)")
subprocess.run([sys.executable, client_script])
