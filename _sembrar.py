"""Siembra los datos de un escenario en su carpeta. Lo lanza motor.py en un proceso aparte:
    python _sembrar.py <escenario> <carpeta app de Hylanlock> <carpeta de datos>
Así el módulo db de Hylanlock apunta a la BD del escenario sin interferir con nada más."""
import hashlib
import importlib
import json
import os
import sys
import time

eid, app, carpeta = sys.argv[1:4]
sys.path.insert(0, app)
os.environ["HYLANLOCK_DATA_DIR"] = carpeta
import db  # noqa: E402  (el de Hylanlock)


def _pdf(lineas):
    """PDF mínimo pero VÁLIDO (se abre en cualquier visor), con varias líneas de texto."""
    def esc(t):
        return t.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    cuerpo = "BT /F1 13 Tf 16 TL 60 760 Td " + " ".join(f"({esc(l)}) Tj T*" for l in lineas) + " ET"
    cuerpo = cuerpo.encode("cp1252", "replace")
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length " + str(len(cuerpo)).encode() + b" >>\nstream\n" + cuerpo + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
    out, offs = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offs)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


class Ctx:
    """Lo que un escenario necesita para montarse. Ver escenarios/*.py."""

    def __init__(self):
        self.db = db
        self.enlaces = []

    def usuario(self, nombre, clave, admin=False, jefe=False):
        db.create_user(nombre, clave, scope="admin" if admin else "member", boss=1 if jefe else 0)

    def departamento(self, nombre):
        db.create_department(nombre)
        return db.slugify(nombre)

    def subcarpeta(self, dep, nombre):
        db.create_subfolder(dep, nombre)
        return db.slugify(nombre)

    def archivo(self, dep, sub, nombre, lineas=None, datos=None, dias=0, por=None, descargas=()):
        """Deja un archivo (PDF real si es .pdf), su huella SHA-256 y, si 'por', el evento de subida."""
        base = os.path.join(carpeta, "departamentos", dep, *( [sub] if sub else []))
        os.makedirs(base, exist_ok=True)
        if datos is None:
            texto = lineas or [nombre]
            datos = _pdf(texto) if nombre.lower().endswith(".pdf") else ("\n".join(texto) + "\n").encode("utf-8")
        ruta = os.path.join(base, nombre)
        with open(ruta, "wb") as f:
            f.write(datos)
        h = hashlib.sha256(datos).hexdigest()
        with open(ruta + ".sha256", "w", encoding="utf-8", newline="") as f:
            f.write(f"{h} *{nombre}\n")
        if dias:
            t = time.time() - dias * 86400
            os.utime(ruta, (t, t))
        tag = db.folder_tag(dep, sub)
        if por:
            db.log_event("upload_sub" if sub else "upload_dep", user=por, origin="local", ip="192.168.1.20",
                         detail=f"{tag}{nombre} · sha256:{h[:12]}…", bytes=len(datos))
        for quien in descargas:
            db.log_event("download", user=quien, origin="local", ip="192.168.1.21", detail=f"{tag}{nombre}")

    def buzon(self, dep, sub, etiqueta, horas=720, un_solo_uso=False):
        token = db.create_buzon_link(dep, sub, etiqueta, created_by="demo", hours=horas, one_shot=un_solo_uso)
        self.enlaces.append({"etiqueta": etiqueta, "ruta": f"/b/{token}"})
        return token


ctx = Ctx()
db.init_db()
importlib.import_module("escenarios." + eid).sembrar(ctx)
with open(os.path.join(carpeta, "demo-info.json"), "w", encoding="utf-8") as f:
    json.dump({"enlaces": ctx.enlaces, "creado": time.strftime("%Y-%m-%d %H:%M")}, f, ensure_ascii=False)
print("ok")
