"""Motor del demostrador: prepara y arranca un Hylanlock REAL por escenario. Solo librería estándar.

- Cada escenario vive en escenarios/<id>.py (ESCENARIO + sembrar(ctx)).
- Sus datos van a datos/<id>/ (se regeneran al reiniciar). La licencia se copia desde licencias/.
- Hylanlock se busca en: $HYLANLOCK_SRC, ../hylanlock (PC) o ./hylanlock (clon en el móvil).
- Solo hay un Hylanlock encendido a la vez (el móvil no es un servidor de verdad).
"""
import importlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(RAIZ, "datos")
LICENCIA = os.path.join(RAIZ, "licencias", "hylanlock.license.key")
PUERTO = int(os.environ.get("DEMO_PORT", "8000"))
# El móvil abre localhost: sin 127.0.0.0/8, Hylanlock trataría al propio móvil como "fuera de la red".
LAN = "127.0.0.0/8,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"


def hylanlock_app():
    """Carpeta app/ de Hylanlock, o '' si no se encuentra."""
    candidatos = [os.environ.get("HYLANLOCK_SRC", ""),
                  os.path.join(os.path.dirname(RAIZ), "hylanlock"),
                  os.path.join(RAIZ, "hylanlock")]
    for c in candidatos:
        if c and os.path.isfile(os.path.join(c, "app", "hylanlock.py")):
            return os.path.join(c, "app")
    return ""


def escenarios():
    """[(id, ESCENARIO)] en el orden de su campo 'orden'."""
    out = []
    for f in sorted(os.listdir(os.path.join(RAIZ, "escenarios"))):
        if f.endswith(".py") and not f.startswith("_"):
            mod = importlib.import_module("escenarios." + f[:-3])
            out.append((f[:-3], mod.ESCENARIO))
    return sorted(out, key=lambda x: x[1].get("orden", 99))


def escenario(eid):
    if not re.fullmatch(r"[a-z0-9_]+", eid or ""):
        raise KeyError(eid)
    return importlib.import_module("escenarios." + eid).ESCENARIO


def datos_de(eid):
    return os.path.join(DATOS, eid)


def info(eid):
    """Lo que la siembra dejó para el menú (enlaces de buzón…)."""
    try:
        with open(os.path.join(datos_de(eid), "demo-info.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def ips_locales():
    """IPs privadas de este equipo (para conectar desde el punto de acceso). Lo mejor que se pueda."""
    ips = set()
    try:
        out = subprocess.run(["ip", "-4", "-o", "addr"], capture_output=True, text=True, timeout=3).stdout
        ips |= set(re.findall(r"inet (\d+\.\d+\.\d+\.\d+)", out))
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        ips |= set(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError:
        pass
    for destino in ("192.168.43.1", "10.0.0.1", "8.8.8.8"):     # sin enviar nada: solo elige interfaz
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect((destino, 9))
                ips.add(s.getsockname()[0])
        except OSError:
            pass
    privadas = [ip for ip in ips if not ip.startswith("127.") and
                (ip.startswith(("10.", "192.168.")) or re.match(r"172\.(1[6-9]|2\d|3[01])\.", ip))]
    return sorted(privadas)


class Motor:
    def __init__(self, puerto=PUERTO, runner=None, licencia_texto=None, extra_env=None):
        """runner/licencia_texto: solo para las pruebas (servidor y licencia de pruebas de Hylanlock)."""
        self.puerto = puerto
        self.runner = runner
        self.licencia_texto = licencia_texto
        self.extra_env = extra_env or {}
        self.proc = None
        self.activo = None
        self.log = None

    # ---------------------------------------------------------------- preparar
    def preparar(self, eid, desde_cero=False):
        """Crea los datos del escenario si no existen (o desde cero). Devuelve la carpeta."""
        esc = escenario(eid)
        carpeta = datos_de(eid)
        if desde_cero and os.path.isdir(carpeta):
            shutil.rmtree(carpeta)
        if os.path.isfile(os.path.join(carpeta, "hylanlock.db")):
            return carpeta
        app = hylanlock_app()
        if not app:
            raise RuntimeError("No encuentro Hylanlock. Clónalo junto al demostrador (ver README).")
        os.makedirs(carpeta, exist_ok=True)
        destino = os.path.join(carpeta, "license.key")
        if self.licencia_texto:
            with open(destino, "w", encoding="ascii") as f:
                f.write(self.licencia_texto)
        elif os.path.isfile(LICENCIA):
            shutil.copy(LICENCIA, destino)
        else:
            raise RuntimeError("Falta la licencia: copia tu licencia de demo a licencias/hylanlock.license.key")
        env = dict(os.environ, HYLANLOCK_DATA_DIR=carpeta, PYTHONIOENCODING="utf-8")
        env.pop("HYLANLOCK_DB_PATH", None)
        r = subprocess.run([sys.executable, os.path.join(RAIZ, "_sembrar.py"), eid, app, carpeta],
                           cwd=RAIZ, env=env, capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            raise RuntimeError(f"Fallo al preparar «{esc['nombre']}»:\n{r.stdout}\n{r.stderr}")
        return carpeta

    # ---------------------------------------------------------------- arrancar / parar
    def arrancar(self, eid, desde_cero=False):
        self.parar()
        esc = escenario(eid)
        carpeta = self.preparar(eid, desde_cero)
        app = hylanlock_app()
        env = dict(os.environ)
        env.pop("HYLANLOCK_DB_PATH", None)
        env.update({"HYLANLOCK_DATA_DIR": carpeta, "HYLANLOCK_PORT": str(self.puerto),
                    "HYLANLOCK_BIND": "0.0.0.0", "HYLANLOCK_LAN_CIDR": LAN,
                    "HYLANLOCK_ORG_NAME": esc["organizacion"], "PYTHONIOENCODING": "utf-8",
                    "HYLANLOCK_TG_TOKEN": "", "HYLANLOCK_TG_CHAT": ""})
        env.update({f"HYLANLOCK_{k}": str(v) for k, v in esc.get("entorno", {}).items()})
        env.update(self.extra_env)
        orden = [sys.executable, self.runner] if self.runner else [sys.executable, "hylanlock.py"]
        self.log = open(os.path.join(carpeta, "servidor.log"), "w", encoding="utf-8")
        self.proc = subprocess.Popen(orden, cwd=app, env=env, stdout=self.log, stderr=subprocess.STDOUT)
        self.activo = eid
        for _ in range(80):
            if self.vivo():
                return True
            if self.proc.poll() is not None:
                break
            time.sleep(0.25)
        self.parar()
        raise RuntimeError("Hylanlock no arrancó; mira " + os.path.join(carpeta, "servidor.log"))

    def parar(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(8)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if self.log:
            self.log.close()
        self.proc, self.activo, self.log = None, None, None

    def vivo(self):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{self.puerto}/healthz", timeout=1) as r:
                return r.status == 200
        except (OSError, urllib.error.URLError):
            return False

    # ---------------------------------------------------------------- acciones de demo
    def simular_internet(self, ip="8.8.8.8"):
        """Hace como si alguien visitara Hylanlock desde internet (para la demo del aviso de exposición).
        Funciona porque el escenario confía en 127.0.0.1 como proxy y aquí se le dice la IP 'real'."""
        req = urllib.request.Request(f"http://127.0.0.1:{self.puerto}/login", headers={"X-Forwarded-For": ip})
        try:
            urllib.request.urlopen(req, timeout=3).read()
        except (OSError, urllib.error.URLError):
            pass
