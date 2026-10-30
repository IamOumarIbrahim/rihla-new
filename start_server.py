#!/usr/bin/env python3
"""
start_server.py  –  Start the Rihla API server.

Run this BEFORE starting the Tkinter client.
The server will stay running until you close it (Ctrl+C).
"""
import subprocess
import sys
import os

server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server", "server.py")

print("=" * 55)
print("  Rihla API Server")
print("  http://localhost:5000")
print("  Press Ctrl+C to stop.")
print("=" * 55)

subprocess.run([sys.executable, server_script])
