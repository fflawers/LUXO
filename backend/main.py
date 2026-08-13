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

# Aquí se incluirán los routers, por ejemplo:
# from routers import ai_router, file_router
# app.include_router(ai_router.router, prefix="/api/ai")
# app.include_router(file_router.router, prefix="/api/files")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8553, reload=True)
