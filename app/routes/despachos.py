import os
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.database import supabase
from app.models import DespachoCreate, DespachoUpdate
from app.services.qr_service import generar_qr_bytes
from app.services.pdf_service import generar_pdf_despacho


router = APIRouter(
    prefix="/despachos",
    tags=["Despachos"]
)


APP_PUBLIC_URL = os.getenv("APP_PUBLIC_URL", "http://127.0.0.1:8000")


def generar_codigo_despacho() -> str:
    fecha = datetime.now().strftime("%Y%m%d-%H%M%S")
    codigo_corto = str(uuid4())[:8].upper()
    return f"DESP-{fecha}-{codigo_corto}"


def buscar_insumo(insumo_id: int):
    response = (
        supabase
        .table("insumos")
        .select("*")
        .eq("id", insumo_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insumo {insumo_id} no encontrado"
        )

    return response.data[0]


def actualizar_stock_insumo(insumo_id: int, nueva_cantidad: float):
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo actualizar el stock del insumo {insumo_id}"
        )

    return response.data[0]


def obtener_despacho_por_id(despacho_id: int):
    response = (
        supabase
        .table("despachos")
        .select("*")
        .eq("id", despacho_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Despacho no encontrado"
        )

    return response.data[0]


def obtener_items_despacho(despacho_id: int):
    response = (
        supabase
        .table("despacho_items")
        .select("*")
        .eq("despacho_id", despacho_id)
        .order("id", desc=False)
        .execute()
    )

    return response.data


def normalizar_items(items):
    acumulados = {}

    for item in items:
        insumo_id = item.insumo_id
        cantidad = float(item.cantidad)

        if cantidad <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Todas las cantidades deben ser mayores que cero"
            )

        if insumo_id not in acumulados:
            acumulados[insumo_id] = 0

        acumulados[insumo_id] += cantidad

    return [
        {
            "insumo_id": insumo_id,
            "cantidad": cantidad
        }
        for insumo_id, cantidad in acumulados.items()
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
def crear_despacho(despacho: DespachoCreate):
    try:
        if not despacho.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El despacho debe tener al menos un ítem"
            )

        items_normalizados = normalizar_items(despacho.items)

        items_preparados = []

        # 1. Validar stock antes de guardar
        for item in items_normalizados:
            insumo_id = item["insumo_id"]
            cantidad_despachar = float(item["cantidad"])

            insumo = buscar_insumo(insumo_id)

            stock_actual = float(insumo.get("cantidad") or 0)

            if cantidad_despachar > stock_actual:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Stock insuficiente para {insumo.get('nombre')}. "
                        f"Stock actual: {stock_actual}, solicitado: {cantidad_despachar}"
                    )
                )

            stock_nuevo = stock_actual - cantidad_despachar

            items_preparados.append({
                "insumo": insumo,
                "insumo_id": insumo_id,
                "cantidad": cantidad_despachar,
                "stock_anterior": stock_actual,
                "stock_nuevo": stock_nuevo
            })

        # 2. Crear despacho principal
        codigo_despacho = generar_codigo_despacho()

        despacho_payload = {
            "codigo_despacho": codigo_despacho,
            "entregado_a": despacho.entregado_a,
            "despachado_por": despacho.despachado_por,
            "observacion": despacho.observacion,
            "status": "despachado"
        }

        despacho_response = (
            supabase
            .table("despachos")
            .insert(despacho_payload)
            .select("*")
            .execute()
        )

        if not despacho_response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo crear el despacho"
            )

        despacho_creado = despacho_response.data[0]
        despacho_id = despacho_creado["id"]

        # 3. Crear ítems del despacho
        items_payload = []

        for item in items_preparados:
            insumo = item["insumo"]

            items_payload.append({
                "despacho_id": despacho_id,
                "insumo_id": item["insumo_id"],
                "nombre": insumo.get("nombre"),
                "unidad_medida": insumo.get("unidad_medida"),
                "cantidad": item["cantidad"],
                "presentacion": insumo.get("presentacion"),
                "categoria": insumo.get("categoria"),
                "stock_anterior": item["stock_anterior"],
                "stock_nuevo": item["stock_nuevo"]
            })

        items_response = (
            supabase
            .table("despacho_items")
            .insert(items_payload)
            .select("*")
            .execute()
        )

        if not items_response.data:
            supabase.table("despachos").delete().eq("id", despacho_id).execute()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudieron crear los ítems del despacho"
            )

        # 4. Restar stock en insumos
        for item in items_preparados:
            actualizar_stock_insumo(
                insumo_id=item["insumo_id"],
                nueva_cantidad=item["stock_nuevo"]
            )

        despacho_creado["items"] = items_response.data

        return {
            "mensaje": "Despacho creado correctamente y stock actualizado",
            "despacho": despacho_creado
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def listar_despachos():
    try:
        response = (
            supabase
            .table("despachos")
            .select("*")
            .order("id", desc=False)
            .execute()
        )

        despachos = response.data

        for despacho in despachos:
            despacho["items"] = obtener_items_despacho(despacho["id"])

        return {
            "total": len(despachos),
            "data": despachos
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/codigo/{codigo_despacho}")
def obtener_despacho_por_codigo(codigo_despacho: str):
    try:
        response = (
            supabase
            .table("despachos")
            .select("*")
            .eq("codigo_despacho", codigo_despacho)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Despacho no encontrado"
            )

        despacho = response.data[0]
        despacho["items"] = obtener_items_despacho(despacho["id"])

        return despacho

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verificar-qr/{qr_token}")
def verificar_qr_despacho(qr_token: str):
    try:
        response = (
            supabase
            .table("despachos")
            .select("*")
            .eq("qr_token", qr_token)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="QR no válido"
            )

        despacho = response.data[0]

        if not despacho.get("qr_activo", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="QR inactivo"
            )

        despacho["items"] = obtener_items_despacho(despacho["id"])

        return {
            "mensaje": "QR válido. Despacho auténtico.",
            "despacho": despacho
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{despacho_id}")
def obtener_despacho(despacho_id: int):
    try:
        despacho = obtener_despacho_por_id(despacho_id)
        despacho["items"] = obtener_items_despacho(despacho_id)

        return despacho

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{despacho_id}/items")
def listar_items_despacho(despacho_id: int):
    try:
        obtener_despacho_por_id(despacho_id)

        items = obtener_items_despacho(despacho_id)

        return {
            "total": len(items),
            "data": items
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{despacho_id}/qr")
def generar_qr_despacho(despacho_id: int):
    try:
        despacho = obtener_despacho_por_id(despacho_id)

        qr_url = f"{APP_PUBLIC_URL}/despachos/verificar-qr/{despacho['qr_token']}"

        qr_buffer = generar_qr_bytes(qr_url)

        return StreamingResponse(
            qr_buffer,
            media_type="image/png",
            headers={
                "Content-Disposition": f"inline; filename=despacho_{despacho_id}_qr.png"
            }
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{despacho_id}/pdf")
def generar_pdf_despacho_endpoint(despacho_id: int):
    try:
        despacho = obtener_despacho_por_id(despacho_id)
        items = obtener_items_despacho(despacho_id)

        qr_url = f"{APP_PUBLIC_URL}/despachos/verificar-qr/{despacho['qr_token']}"

        pdf_buffer = generar_pdf_despacho(
            despacho=despacho,
            items=items,
            qr_url=qr_url
        )

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=despacho_{despacho_id}.pdf"
            }
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{despacho_id}/cancelar")
def cancelar_despacho(despacho_id: int):
    try:
        despacho = obtener_despacho_por_id(despacho_id)

        if despacho.get("status") == "cancelado":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El despacho ya está cancelado"
            )

        items = obtener_items_despacho(despacho_id)

        # Devolver stock de cada ítem
        for item in items:
            insumo = buscar_insumo(item["insumo_id"])

            stock_actual = float(insumo.get("cantidad") or 0)
            cantidad_devolver = float(item.get("cantidad") or 0)
            stock_nuevo = stock_actual + cantidad_devolver

            actualizar_stock_insumo(
                insumo_id=item["insumo_id"],
                nueva_cantidad=stock_nuevo
            )

        response = (
            supabase
            .table("despachos")
            .update({
                "status": "cancelado",
                "qr_activo": False,
                "fecha_cierre": datetime.now(timezone.utc).isoformat()
            })
            .eq("id", despacho_id)
            .select("*")
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo cancelar el despacho"
            )

        return {
            "mensaje": "Despacho cancelado y stock devuelto correctamente",
            "despacho": response.data[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))