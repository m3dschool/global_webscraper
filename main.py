#!/usr/bin/env python3
"""
Main entry point for the Universal Web Scraper & Gemini Enrichment Platform
"""

import uvicorn
from src.core.config import settings
from src.core.logging import setup_logging
from src.core.metrics import start_metrics_server

def main():
    """Main function to start the application"""
    # Setup logging
    setup_logging()
    
    # Start metrics server in a separate thread
    import threading
    metrics_thread = threading.Thread(target=start_metrics_server, daemon=True)
    metrics_thread.start()
    
    # Start the FastAPI application
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

if __name__ == "__main__":
    main()