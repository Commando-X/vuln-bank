"""SwigDojo target wrapper for vuln-bank."""
import sys
import os

# Ensure the app directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
app_dir = "/app" if os.path.isdir("/app") else os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
os.chdir(app_dir)

from swigdojo_target import TargetWrapper
from config import load_config
from verifiers.registry import register_verifiers

config = load_config()

wrapper = TargetWrapper(
    command="python app.py",
    health_port=5000,
    health_path="/",
    health_type="http",
    proxy=True,
)

registered = register_verifiers(wrapper, config)
print(f"[wrapper] Registered {len(registered)} verifiers: {', '.join(registered)}")

if __name__ == "__main__":
    wrapper.run()
