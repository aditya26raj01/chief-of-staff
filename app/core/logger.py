import logging

# Centralized logger instance for the application.
# We use "uvicorn.error" so that logs output seamlessly alongside the uvicorn logs.
logger = logging.getLogger("uvicorn.error")
