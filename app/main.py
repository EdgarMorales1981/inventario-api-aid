from fastapi import FastAPI

from app.routes.insumos import router as insumos_router
from app.routes.recepciones import router as recepciones_router
from app.routes.despachos import router as despachos_router


app = FastAPI(
    title="API Sistema de Inventario",
    version="1.0.0",
    description="API para control de insumos, recepciones de stock y despachos con PDF y QR."
)


app.include_router(insumos_router)
app.include_router(recepciones_router)
app.include_router(despachos_router)


@app.get("/")
def home():
    return {
        "mensaje": "API funcionando correctamente",
        "modulos": [
            "insumos",
            "recepciones",
            "despachos"
        ]
    }