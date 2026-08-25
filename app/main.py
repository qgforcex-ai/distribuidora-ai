from fastapi import FastAPI

from app.routes.clientes import router as clientes_router
from app.routes.produtos import router as produtos_router


app = FastAPI(
    title="Distribuidora AI",
    version="1.0.0"
)


app.include_router(clientes_router)
app.include_router(produtos_router)


@app.get("/")
def inicio():
    return {
        "message": "API Distribuidora funcionando!"
    }