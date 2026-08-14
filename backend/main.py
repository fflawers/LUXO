from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import conectar_db
import os

app = FastAPI(title="LUXO API Microservice")

# Configurar CORS si la UI (Flet) o los clientes web van a consumirlo desde otro puerto
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    db = conectar_db()
    if db:
        db.close()
        return {"status": "ok", "database": "connected"}
    return {"status": "ok", "database": "disconnected"}

from routers import files, biometrics, ai, auth, chat, notifications, tasks, support, suggestions, manuals
app.include_router(files.router)
app.include_router(biometrics.router, prefix="/api/biometria")
app.include_router(ai.router, prefix="/api/ai")
app.include_router(auth.router, prefix="/api/auth")
app.include_router(chat.router, prefix="/api/chat")
app.include_router(notifications.router, prefix="/api/notifications")
app.include_router(tasks.router, prefix="/api/tasks")
app.include_router(support.router, prefix="/api/support")
app.include_router(suggestions.router, prefix="/api/suggestions")
app.include_router(manuals.router, prefix="/api/manuals")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8553, reload=True)
