import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from setproctitle import setproctitle  # Proper import for setproctitle

from servers.status_router import SystemStatusRouter
from servers.chat_router import ChatRouter
from servers.chat_memory_router import ChatMemoryRouter
from servers.settings_router import SettingsRouter
from servers.admin_router import AdminRouter
from servers.login_router import LoginRouter
from servers.editor_router import EditorRouter
from servers.editor_bridge_router import EditorBridgeRouter
from servers.agent_router import AgentRouter
from servers.rag_store import RagRouter


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

app.include_router(LoginRouter)
logger.debug("Mounted login router")

app.include_router(AgentRouter)
logger.debug("Mounted agent router")

app.include_router(RagRouter)
logger.debug("Mounted rag router")

app.include_router(ChatRouter)  # Ensure chat router is included for model management
logger.debug("Mounted chat router")

app.include_router(ChatMemoryRouter)
logger.debug("Mounted memory router")

app.include_router(SettingsRouter)
logger.debug("Mounted settings router")

app.include_router(AdminRouter)
logger.debug("Mounted admin router")

app.include_router(EditorRouter)
logger.debug("Mounted editor router")

app.include_router(EditorBridgeRouter, prefix="/editor")

# Mount static files (frontend)
#app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'nova-ui'), html=True), name="static")
#logger.debug(f"Mounted static files")



logger.info("API endpoints registered ✅")
