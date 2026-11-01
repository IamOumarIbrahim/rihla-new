#!/usr/bin/env python3
# starts the Rihla tkinter app
# the server (start_server.py) has to be running on localhost:5000 already
import subprocess
import sys
import os

client_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "main.py")

print("Starting Rihla client... (server must be running on localhost:5000)")
subprocess.run([sys.executable, client_script])
