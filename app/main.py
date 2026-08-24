from fastapi import FastAPI

from app.routes.clientes import router as clientes_router


app = FastAPI(
    title="Distribuidora AI",
    version="1.0.0"
)


app.include_router(clientes_router)


@app.get("/")
def inicio():
    return {
        "message": "API Distribuidora funcionando!"
    }