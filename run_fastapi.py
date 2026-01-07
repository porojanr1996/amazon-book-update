#!/usr/bin/env python3
"""
Run FastAPI application with uvicorn
Maintains backward compatibility with Flask app
"""
import uvicorn
import config

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        reload=(config.FLASK_ENV == 'development'),
        log_level="info"
    )

