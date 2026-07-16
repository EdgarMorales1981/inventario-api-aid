from fastapi import APIRouter, HTTPException
from app.database import supabase
from app.schemas import RecepcionCreate, RecepcionUpdate

router = APIRouter(
    prefix="/recepciones",
    tags=["Recepciones"]
)


def buscar_insumo(insumo_id: int):
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


def actualizar_insumo_cantidad(insumo_id: int, nueva_cantidad: float):
    response = (
        supabase
        .table("insumos")
        .update({
            "cantidad": nueva_cantidad
        })
        .eq("id", insumo_id)
        .select("*")
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=400,
            detail="No se pudo actualizar la cantidad del insumo"
        )

    return response.data[0]


@router.post("/")
def crear_recepcion(recepcion: RecepcionCreate):
    try:
        datos = recepcion.model_dump(mode="json")

        insumo_id = datos.get("insumo_id")
        cantidad_recibida = float(datos.get("cantidad") or 0)
        status_recepcion = datos.get("status", "recibido")

        if not insumo_id:
            raise HTTPException(status_code=400, detail="El insumo_id es obligatorio")

        if cantidad_recibida <= 0:
            raise HTTPException(status_code=400, detail="La cantidad debe ser mayor que cero")

        # 1. Buscar insumo actual
        insumo_actual = buscar_insumo(insumo_id)

        stock_anterior = float(insumo_actual.get("cantidad") or 0)

        # 2. Calcular nuevo stock
        if status_recepcion == "recibido":
            stock_nuevo = stock_anterior + cantidad_recibida
        else:
            stock_nuevo = stock_anterior

        # 3. Agregar stock_anterior y stock_nuevo a la recepción
        datos["stock_anterior"] = stock_anterior
        datos["stock_nuevo"] = stock_nuevo

        # 4. Actualizar tabla insumos
        insumo_actualizado = insumo_actual

        if status_recepcion == "recibido":
            insumo_actualizado = actualizar_insumo_cantidad(
                insumo_id=insumo_id,
                nueva_cantidad=stock_nuevo
            )

        # 5. Guardar recepción como historial
        recepcion_response = (
            supabase
            .table("recepciones")
            .insert(datos)
            .select("*")
            .execute()
        )

        if not recepcion_response.data:
            raise HTTPException(status_code=400, detail="No se pudo crear la recepción")

        return {
            "mensaje": "Recepción creada y stock actualizado correctamente",
            "stock_anterior": stock_anterior,
            "cantidad_recibida": cantidad_recibida,
            "stock_nuevo": stock_nuevo,
            "insumo_actualizado": insumo_actualizado,
            "recepcion": recepcion_response.data[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def listar_recepciones():
    try:
        response = (
            supabase
            .table("recepciones")
            .select("*")
            .order("id", desc=False)
            .execute()
        )

        return {
            "total": len(response.data),
            "data": response.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insumo/{insumo_id}")
def listar_recepciones_por_insumo(insumo_id: int):
    try:
        response = (
            supabase
            .table("recepciones")
            .select("*")
            .eq("insumo_id", insumo_id)
            .order("id", desc=False)
            .execute()
        )

        return {
            "total": len(response.data),
            "data": response.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{recepcion_id}")
def obtener_recepcion(recepcion_id: int):
    try:
        response = (
            supabase
            .table("recepciones")
            .select("*")
            .eq("id", recepcion_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail="Recepción no encontrada")

        return response.data[0]

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{recepcion_id}")
def actualizar_recepcion(recepcion_id: int, recepcion: RecepcionUpdate):
    try:
        datos = recepcion.model_dump(exclude_unset=True, mode="json")

        if not datos:
            raise HTTPException(status_code=400, detail="No hay datos para actualizar")

        # OJO:
        # Este PUT solo actualiza datos informativos.
        # No vuelve a sumar stock para evitar duplicados.
        response = (
            supabase
            .table("recepciones")
            .update(datos)
            .eq("id", recepcion_id)
            .select("*")
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail="Recepción no encontrada")

        return {
            "mensaje": "Recepción actualizada correctamente",
            "data": response.data[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{recepcion_id}")
def eliminar_recepcion(recepcion_id: int):
    try:
        # 1. Buscar recepción
        recepcion_response = (
            supabase
            .table("recepciones")
            .select("*")
            .eq("id", recepcion_id)
            .execute()
        )

        if not recepcion_response.data:
            raise HTTPException(status_code=404, detail="Recepción no encontrada")

        recepcion = recepcion_response.data[0]

        insumo_id = recepcion.get("insumo_id")
        cantidad_recibida = float(recepcion.get("cantidad") or 0)
        status_recepcion = recepcion.get("status")

        # 2. Si estaba recibida, revertimos el stock
        if status_recepcion == "recibido":
            insumo_actual = buscar_insumo(insumo_id)

            stock_actual = float(insumo_actual.get("cantidad") or 0)
            stock_nuevo = stock_actual - cantidad_recibida

            if stock_nuevo < 0:
                raise HTTPException(
                    status_code=400,
                    detail="No se puede eliminar porque el stock quedaría negativo"
                )

            actualizar_insumo_cantidad(
                insumo_id=insumo_id,
                nueva_cantidad=stock_nuevo
            )

        # 3. Eliminar recepción
        delete_response = (
            supabase
            .table("recepciones")
            .delete()
            .eq("id", recepcion_id)
            .select("*")
            .execute()
        )

        if not delete_response.data:
            raise HTTPException(status_code=404, detail="Recepción no encontrada")

        return {
            "mensaje": "Recepción eliminada y stock revertido correctamente",
            "data": delete_response.data[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))