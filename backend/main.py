#!/usr/bin/env python3
"""
HowYouBeen Backend Server

Run this file to start the development server:
python main.py
"""

import os
import uuid
import uvicorn
from pathlib import Path

# Configure local storage for debugging
storage_dir = Path("storage") / str(uuid.uuid4())[:8]  # Short UUID for readability
storage_dir.mkdir(parents=True, exist_ok=True)

# Set environment variables to force local storage
os.environ["STORAGE_BACKEND"] = "local"
os.environ["LOCAL_STORAGE_BACKUP"] = str(storage_dir / "backup.json")
os.environ["LOCAL_STORAGE_TEMP_DIR"] = str(storage_dir / "temp")

# Create temp directory
(storage_dir / "temp").mkdir(exist_ok=True)

print(f"🗂️  Using local storage directory: {storage_dir.absolute()}")
print(f"📄 Backup file: {storage_dir / 'backup.json'}")
print(f"📁 Temp directory: {storage_dir / 'temp'}")

from src.howyoubeen.server.main import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",  # localhost only
        port=8002,
        reload=True,
        log_level="info"
    )