from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from app.services.qr_service import generar_qr_bytes


def generar_pdf_pedido(pedido: dict, items: list, qr_url: str) -> BytesIO:
    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)
    pdf.setTitle(f"Pedido #{pedido.get('id')}")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, 800, f"Comprobante de Pedido #{pedido.get('id')}")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 765, f"Número de pedido: {pedido.get('numero_pedido') or 'N/A'}")
    pdf.drawString(50, 740, f"Status: {pedido.get('status', '')}")
    pdf.drawString(50, 715, f"Observación: {pedido.get('observacion') or 'Sin observación'}")

    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(50, 675, "Ítems del pedido:")

    y = 645
    pdf.setFont("Helvetica", 10)

    for index, item in enumerate(items, start=1):
        texto = (
            f"{index}. {item.get('nombre', '')} | "
            f"Cantidad: {item.get('cantidad', '')} | "
            f"Unidad: {item.get('unidad_medida', '')} | "
            f"Presentación: {item.get('presentacion', '')} | "
            f"Categoría: {item.get('categoria', '')}"
        )

        pdf.drawString(50, y, texto[:110])
        y -= 22

        if y < 120:
            pdf.showPage()
            y = 780
            pdf.setFont("Helvetica", 10)

    qr_buffer = generar_qr_bytes(qr_url)
    qr_image = ImageReader(qr_buffer)

    if y < 300:
        pdf.showPage()
        y = 760

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y - 30, "QR de verificación:")

    pdf.drawImage(qr_image, 50, y - 210, width=150, height=150)

    pdf.setFont("Helvetica", 8)
    pdf.drawString(50, y - 230, qr_url)

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer


def generar_pdf_despacho(despacho: dict, items: list, qr_url: str) -> BytesIO:
    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)
    pdf.setTitle(f"Despacho {despacho.get('codigo_despacho')}")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, 800, "Comprobante de Despacho")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, 770, f"Código de despacho: {despacho.get('codigo_despacho', '')}")
    pdf.drawString(50, 750, f"Entregado a: {despacho.get('entregado_a') or 'N/A'}")
    pdf.drawString(50, 730, f"Despachado por: {despacho.get('despachado_por') or 'N/A'}")
    pdf.drawString(50, 710, f"Status: {despacho.get('status', '')}")
    pdf.drawString(50, 690, f"Fecha: {despacho.get('fecha_despacho', '')}")
    pdf.drawString(50, 670, f"Observación: {despacho.get('observacion') or 'Sin observación'}")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 635, "Ítems despachados:")

    y = 610

    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(50, y, "ID")
    pdf.drawString(80, y, "Insumo")
    pdf.drawString(260, y, "Cantidad")
    pdf.drawString(330, y, "Unidad")
    pdf.drawString(400, y, "Presentación")
    pdf.drawString(500, y, "Stock nuevo")

    y -= 18
    pdf.setFont("Helvetica", 9)

    for item in items:
        if y < 120:
            pdf.showPage()
            y = 780
            pdf.setFont("Helvetica-Bold", 9)
            pdf.drawString(50, y, "ID")
            pdf.drawString(80, y, "Insumo")
            pdf.drawString(260, y, "Cantidad")
            pdf.drawString(330, y, "Unidad")
            pdf.drawString(400, y, "Presentación")
            pdf.drawString(500, y, "Stock nuevo")
            y -= 18
            pdf.setFont("Helvetica", 9)

        pdf.drawString(50, y, str(item.get("insumo_id", ""))[:8])
        pdf.drawString(80, y, str(item.get("nombre", ""))[:28])
        pdf.drawString(260, y, str(item.get("cantidad", ""))[:10])
        pdf.drawString(330, y, str(item.get("unidad_medida", ""))[:12])
        pdf.drawString(400, y, str(item.get("presentacion", ""))[:18])
        pdf.drawString(500, y, str(item.get("stock_nuevo", ""))[:10])

        y -= 18

    qr_buffer = generar_qr_bytes(qr_url)
    qr_image = ImageReader(qr_buffer)

    if y < 300:
        pdf.showPage()
        y = 760

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y - 30, "QR de autenticidad:")

    pdf.drawImage(qr_image, 50, y - 210, width=150, height=150)

    pdf.setFont("Helvetica", 8)
    pdf.drawString(50, y - 230, qr_url)

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer