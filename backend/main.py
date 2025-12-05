import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers from layered modules
from app.routes.health_routes import router as health_router
from app.routes.upload_routes import router as upload_router
from app.routes.chat_routes import router as chat_router

def create_app() -> FastAPI:
    app = FastAPI(title="Secure Self-Hosted Chatbot - Backend (Layered Architecture)")

    # CORS - allow local dev from frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health_router, prefix="/api/health", tags=["health"])
    app.include_router(upload_router, prefix="/api/upload", tags=["upload"])
    app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

    return app

app = create_app()

@app.get("/")
def root():
    return {"message": "Secure Self-Hosted Chatbot Backend running"}