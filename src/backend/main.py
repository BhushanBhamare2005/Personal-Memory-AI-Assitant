"""
FastAPI Backend for Personal AI Memory Assistant
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import logging

from dotenv import load_dotenv

load_dotenv()

from .routes import memory_routes, chat_routes, suggestions_routes, habits_routes, documents_routes, documents_debug_routes


from ..memory.manager import MemoryManager
from ..llm.llm_handler import LLMHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
memory_manager = None
llm_handler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle"""
    global memory_manager, llm_handler
    
    # Startup
    logger.info("Starting Personal AI Memory Assistant...")
    try:
        memory_manager = MemoryManager()
        llm_handler = LLMHandler()
        logger.info("Systems initialized successfully")
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Personal AI Memory Assistant...")

app = FastAPI(
    title="Personal AI Memory Assistant",
    description="A futuristic AI that remembers everything about you",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(memory_routes.router, prefix="/api/memory", tags=["Memory"])
app.include_router(chat_routes.router, prefix="/api/chat", tags=["Chat"])
app.include_router(suggestions_routes.router, prefix="/api/suggestions", tags=["Suggestions"])
app.include_router(habits_routes.router, prefix="/api/habits", tags=["Habits"])
app.include_router(documents_routes.router, prefix="/api/documents", tags=["Documents"])
app.include_router(documents_debug_routes.router, prefix="/api/documents_debug", tags=["DocumentsDebug"])

app.include_router(documents_debug_routes.router, prefix="/api/documents", tags=["Documents"])



@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "name": "Personal AI Memory Assistant",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """Health check with system info"""
    return {
        "status": "healthy",
        "memory_system": "ready",
        "llm_system": "ready",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
