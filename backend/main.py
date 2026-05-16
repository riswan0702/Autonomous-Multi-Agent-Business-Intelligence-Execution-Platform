"""
Multi-Agent Business Intelligence Platform
FastAPI Application Entry Point
"""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv


load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 BI Platform starting up...")
    # Validate API key on startup
    if not os.getenv("GROQ_API_KEY"):
        print("❌ WARNING: GROQ_API_KEY not set in .env!")
    else:
        print("✅ Groq API key loaded")
    # Initialize memory store
    from memory.vector_store import get_memory_store
    store = get_memory_store()
    status = "enabled" if store.enabled else "disabled (ChromaDB unavailable)"
    print(f"📚 Memory store: {status} ({store.count()} memories stored)")
    print("✅ All 5 agents ready: Research → Strategy → Critic → Planner → QA")
    yield
    print("👋 BI Platform shutting down...")


app = FastAPI(
    title="Multi-Agent BI Platform",
    description="Autonomous business intelligence via specialized AI agents (Groq + ChromaDB)",
    version="2.0.0",
    lifespan=lifespan,
)

#  allow frontend dev server and production build
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "Multi-Agent BI Platform",
        "version": "2.0.0",
        "provider": "Groq (llama-3.3-70b + llama-3.1-8b)",
        "docs": "/docs",
        "agents": [
            "Orchestrator", "Research Agent", "Strategy Agent",
            "Critic Agent", "Planner Agent", "QA Agent", "Memory Agent",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("ENVIRONMENT", "development") == "development",
    )
