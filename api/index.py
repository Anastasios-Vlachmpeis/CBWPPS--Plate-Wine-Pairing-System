"""
Vercel serverless function entrypoint for AI Culinary Expert
This file is required by Vercel to find the FastAPI app
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Change working directory to project root
import os
os.chdir(project_root)

# Import the FastAPI app from web_ui/server.py
from web_ui.server import app

# Export for Vercel
__all__ = ['app']
