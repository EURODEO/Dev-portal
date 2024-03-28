"""
Defines the FastAPI app.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from app.exceptions import http_exception_handler, general_exception_handler
from app.routers import apikey
from app.config import settings

config = settings()

app = FastAPI()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.server.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Routers
app.include_router(apikey.router)


def start_dev() -> None:
    """
    Start the Uvicorn server with Poetry script for development using hot reload
    """
    uvicorn.run("app.main:app", host=config.server.host, port=config.server.port, reload=True)


if __name__ == "__main__":
    # Start the Uvicorn server in docker by running this module python -m app.main
    uvicorn.run("app.main:app", host=config.server.host, port=config.server.port)
