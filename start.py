import subprocess
import sys
import time
import os

PORT = os.environ.get("PORT", "8501")

flask_process = subprocess.Popen([sys.executable, "call_webhook.py"])

time.sleep(2)

streamlit_process = subprocess.Popen([
    sys.executable,
    "-m",
    "streamlit",
    "run",
    "app.py",
    "--server.port", PORT,
    "--server.address", "0.0.0.0"
])

streamlit_process.wait()
flask_process.terminate()