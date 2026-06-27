import os
import sys

# Add repo root to Python path so we can import the FastAPI app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

# Vercel serves the ASGI app exposed as `app`
