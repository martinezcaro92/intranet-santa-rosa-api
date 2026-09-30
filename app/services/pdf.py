"""Generador de PDF MÍNIMO sin dependencias externas.

Sirve para que el endpoint GET /ausencias/{id}/pdf devuelva un documento real.
En el proyecto se recomienda usar WeasyPrint o ReportLab, y Pillow para incrustar
la firma manuscrita capturada en el frontend.
"""


def _escapar(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def generar_pdf(titulo: str, lineas: list[str]) -> bytes:
    contenido = ["BT", "/F1 16 Tf", "56 780 Td", f"({_escapar(titulo)}) Tj", "/F1 11 Tf", "0 -30 Td"]
    for linea in lineas:
        contenido += [f"({_escapar(linea)}) Tj", "0 -18 Td"]
    contenido.append("ET")
    stream = "\n".join(contenido).encode("cp1252", errors="replace")

    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    salida = bytearray(b"%PDF-1.4\n")
    posiciones = []
    for i, obj in enumerate(objetos, start=1):
        posiciones.append(len(salida))
        salida += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    inicio_xref = len(salida)
    salida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    for pos in posiciones:
        salida += f"{pos:010d} 00000 n \n".encode()
    salida += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF".encode()
    return bytes(salida)
