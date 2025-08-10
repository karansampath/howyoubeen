#!/usr/bin/env python3
"""
KeepInTouch Backend Server

Run this file to start the development server:
python main.py
"""

import uvicorn

from src.keepintouch.server.main import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )