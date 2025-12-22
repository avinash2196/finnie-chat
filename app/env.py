import os
from pathlib import Path

_loaded = False

def load_env_once():
    """Load environment variables from project .env exactly once."""
    global _loaded
    if _loaded:
        return
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, _, value = line.partition("=")
                if key:
                    os.environ.setdefault(key.strip(), value.strip())
    _loaded = True
