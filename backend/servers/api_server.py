import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from setproctitle import setproctitle  # Proper import for setproctitle

from tray.tray_status import server_status_router
from servers.status_router import SystemStatusRouter
from servers.chat_router import router as chat_router
from auth.login import login_router
from utils.logger import logger, setup_logger

# Set the process title
setproctitle("nova_API_server")

setup_logger()
logger = logger.bind(name="Servers-Routes")


# Initialize FastAPI app
app = FastAPI()
logger.debug("Starting FastAPI Server")

# Add middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.debug("CORS middleware added")

# Include all routers
app.include_router(SystemStatusRouter)
logger.debug("Mounted system status router")

app.include_router(login_router)
logger.debug("Mounted login router")

app.include_router(server_status_router)
logger.debug("Mounted server status router")

app.include_router(chat_router)  # Ensure chat router is included for model management
logger.debug("Mounted chat router")

# Mount static files (frontend)
app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), '..', '..', 'nova-UI/src'), html=True), name="static")
logger.debug(f"Mounted static files")

logger.debug("All routes set up")
