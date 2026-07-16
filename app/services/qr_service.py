from io import BytesIO
import qrcode


def generar_qr_bytes(texto: str) -> BytesIO:
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )

    qr.add_data(texto)
    qr.make(fit=True)

    imagen = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer