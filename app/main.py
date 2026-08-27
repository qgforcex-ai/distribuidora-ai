from fastapi import FastAPI

from app.routes.clientes import router as clientes_router
from app.routes.produtos import router as produtos_router
from app.routes.vendas import router as vendas_router
from app.routes.analises import router as analises_router
from app.routes.ia import router as ia_router


app = FastAPI(
    title="Distribuidora AI",
    version="1.0.0"
)


app.include_router(clientes_router)
app.include_router(produtos_router)
app.include_router(vendas_router)
app.include_router(analises_router)
app.include_router(ia_router)


@app.get("/")
def inicio():
    return {
        "message": "API Distribuidora funcionando!"
    }