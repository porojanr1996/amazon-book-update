#!/usr/bin/env python3
"""
Run FastAPI application with uvicorn
Maintains backward compatibility with Flask app
"""
import uvicorn
import config
import os

if __name__ == "__main__":
    # Get root_path from environment variable (for subpath deployment)
    root_path = os.getenv('ROOT_PATH', '')
    
    uvicorn.run(
        "app.main:app",
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        reload=(config.FLASK_ENV == 'development'),
        log_level="info",
        root_path=root_path
    )

