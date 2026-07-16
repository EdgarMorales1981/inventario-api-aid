from fastapi import APIRouter, HTTPException
from app.database import supabase
from app.schemas import InsumoCreate, InsumoUpdate

router = APIRouter(
    prefix="/insumos",
    tags=["Insumos"]
)


@router.post("/")
def crear_insumo(insumo: InsumoCreate):
    try:
        response = supabase.table("insumos").insert(insumo.model_dump()).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="No se pudo crear el insumo")

        return {
            "mensaje": "Insumo creado correctamente",
            "data": response.data[0]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def listar_insumos():
    try:
        response = supabase.table("insumos").select("*").order("id").execute()

        return {
            "total": len(response.data),
            "data": response.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{insumo_id}")
def obtener_insumo(insumo_id: int):
    try:
        response = (
            supabase
            .table("insumos")
            .select("*")
            .eq("id", insumo_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail="Insumo no encontrado")

        return response.data[0]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categoria/{categoria}")
def listar_por_categoria(categoria: str):
    try:
        response = (
            supabase
            .table("insumos")
            .select("*")
            .eq("categoria", categoria)
            .order("id")
            .execute()
        )

        return {
            "total": len(response.data),
            "data": response.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{insumo_id}")
def actualizar_insumo(insumo_id: int, insumo: InsumoUpdate):
    try:
        datos = insumo.model_dump(exclude_unset=True)

        if not datos:
            raise HTTPException(status_code=400, detail="No hay datos para actualizar")

        response = (
            supabase
            .table("insumos")
            .update(datos)
            .eq("id", insumo_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail="Insumo no encontrado")

        return {
            "mensaje": "Insumo actualizado correctamente",
            "data": response.data[0]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{insumo_id}")
def eliminar_insumo(insumo_id: int):
    try:
        response = (
            supabase
            .table("insumos")
            .delete()
            .eq("id", insumo_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail="Insumo no encontrado")

        return {
            "mensaje": "Insumo eliminado correctamente",
            "data": response.data[0]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))