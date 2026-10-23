"""Demostrador: menú en el navegador del móvil para lanzar demos REALES de los productos.

    python3 demostrador.py            # y abre http://127.0.0.1:8080 en el navegador del móvil

El menú solo escucha en 127.0.0.1: quien se conecte a tu punto de acceso ve Hylanlock (puerto 8000),
pero nunca este panel de control. Solo librería estándar.
"""
import html
import os
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import motor

PUERTO_MENU = int(os.environ.get("DEMO_MENU_PORT", "8080"))
M = motor.Motor()
ESTADO = {"error": "", "ok": ""}
_lock = threading.Lock()

CSS = """
:root { --bg:#f4f6fb; --card:#fff; --text:#141a2b; --muted:#5d6782; --line:#dde2ee; --acc:#1e40af;
  --acc-weak:#e3e9fb; --ok:#13795b; --err:#b42318; --warn:#9a6700; }
@media (prefers-color-scheme: dark) { :root { --bg:#0e1220; --card:#161b2e; --text:#e8ecf7; --muted:#9aa4c0;
  --line:#2a3150; --acc:#7c9cff; --acc-weak:#1f2a4d; --ok:#4fd1a5; --err:#ff8a80; --warn:#f5c451; } }
* { box-sizing: border-box; } a { color: var(--acc); } body { margin:0; background:var(--bg); color:var(--text);
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width: 760px; margin: 0 auto; padding: 16px; }
h1 { font-size: 1.35rem; margin: 6px 0 2px; } h2 { font-size: 1.05rem; margin: 22px 0 8px; }
.sub { color: var(--muted); font-size: .88rem; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 14px 16px; margin-top: 12px; }
.card.on { border-color: var(--acc); box-shadow: 0 0 0 2px var(--acc-weak); }
.para { color: var(--muted); font-size: .85rem; margin-top: 2px; }
.idea { margin-top: 8px; font-size: .92rem; }
.row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
button, .btn { font: inherit; font-weight: 700; border: 0; border-radius: 10px; padding: 10px 14px; cursor: pointer;
  background: var(--acc); color: #fff; text-decoration: none; display: inline-block; }
button.sec, .btn.sec { background: var(--acc-weak); color: var(--acc); }
button.dan { background: transparent; color: var(--err); border: 1px solid var(--err); }
.msg { border-radius: 12px; padding: 10px 14px; margin-top: 12px; font-size: .9rem; white-space: pre-wrap; }
.msg.err { background: color-mix(in srgb, var(--err) 12%, transparent); color: var(--err); }
.msg.ok { background: color-mix(in srgb, var(--ok) 12%, transparent); color: var(--ok); }
table { width: 100%; border-collapse: collapse; font-size: .9rem; margin-top: 6px; }
td, th { text-align: left; padding: 6px 8px 6px 0; border-top: 1px solid var(--line); vertical-align: top; }
th { color: var(--muted); font-weight: 600; border-top: 0; }
code, .mono { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: .86rem; word-break: break-all; }
ol { padding-left: 20px; margin: 6px 0 0; } li { margin: 6px 0; }
.url { display: block; margin-top: 4px; }
.pill { display: inline-block; font-size: .75rem; font-weight: 700; padding: 2px 9px; border-radius: 999px;
  background: color-mix(in srgb, var(--ok) 16%, transparent); color: var(--ok); }
"""


def e(s):
    return html.escape(str(s))


def pagina():
    app = motor.hylanlock_app()
    lic = os.path.isfile(motor.LICENCIA)
    ips = motor.ips_locales()
    p = [f"<!doctype html><html lang='es'><head><meta charset='utf-8'><meta name='viewport' "
         f"content='width=device-width,initial-scale=1'><title>Demostrador</title><style>{CSS}</style></head>"
         "<body><main><h1>Demostrador</h1><div class='sub'>Demos reales de Hylanlock, sin internet, desde el móvil</div>"]
    if ESTADO["error"]:
        p.append(f"<div class='msg err'>{e(ESTADO['error'])}</div>")
    if ESTADO["ok"]:
        p.append(f"<div class='msg ok'>{e(ESTADO['ok'])}</div>")
    if not app:
        p.append("<div class='msg err'>No encuentro Hylanlock. En la carpeta del demostrador: "
                 "<code>git clone https://github.com/hylanlock/hylanlock</code></div>")
    if not lic:
        p.append("<div class='msg err'>Falta la licencia de demo: genérala en el PC con "
                 "<code>python tools/license_gen.py -c \"Demo Nicolás\" -t commercial --expires 2027-12-31 -o demo</code> "
                 "y cópiala aquí como <code>licencias/hylanlock.license.key</code>.</div>")

    activo = M.activo if (M.activo and M.vivo()) else None
    if activo:
        esc = motor.escenario(activo)
        inf = motor.info(activo)
        base_local = f"http://localhost:{M.puerto}"
        p.append(f"<div class='card on'><span class='pill'>EN MARCHA</span> <b>{e(esc['nombre'])}</b>"
                 f"<div class='para'>{e(esc['organizacion'])}</div>"
                 f"<h2>Abrir</h2><a class='btn' href='{base_local}/login' target='_blank'>Abrir en este móvil</a>")
        if ips:
            p.append("<div class='sub' style='margin-top:10px'>Desde el portátil del cliente, conectado a tu punto de acceso:</div>"
                     + "".join(f"<code class='url'>http://{e(ip)}:{M.puerto}</code>" for ip in ips))
        else:
            p.append("<div class='sub' style='margin-top:10px'>Activa el punto de acceso del móvil para que otro equipo "
                     "pueda conectarse (y recarga esta página para ver su dirección).</div>")
        if inf.get("enlaces"):
            p.append("<h2>Enlaces de buzón</h2>")
            for l in inf["enlaces"]:
                p.append(f"<div class='sub'>{e(l['etiqueta'])}</div>"
                         f"<a class='url mono' href='{base_local}{e(l['ruta'])}' target='_blank'>{base_local}{e(l['ruta'])}</a>"
                         + "".join(f"<code class='url'>http://{e(ip)}:{M.puerto}{e(l['ruta'])}</code>" for ip in ips))
        p.append("<h2>Usuarios</h2><table><tr><th>Usuario</th><th>Contraseña</th><th>Quién es</th></tr>"
                 + "".join(f"<tr><td><b>{e(u)}</b></td><td><code>{e(c)}</code></td><td>{e(d)}</td></tr>"
                           for u, c, d in esc["usuarios"]) + "</table>")
        p.append("<h2>Guion</h2><ol>" + "".join(f"<li>{paso}</li>" for paso in esc["guion"]) + "</ol>")
        p.append("<div class='row'>")
        if esc.get("simular_internet"):
            p.append("<form method='post' action='/simular'><button>Simular visita desde internet</button></form>")
        p.append(f"<form method='post' action='/arrancar'><input type='hidden' name='id' value='{e(activo)}'>"
                 "<input type='hidden' name='cero' value='1'><button class='sec'>Reiniciar desde cero</button></form>"
                 "<form method='post' action='/parar'><button class='dan'>Parar</button></form></div></div>")

    p.append("<h2>Demos de Hylanlock</h2>")
    for eid, esc in motor.escenarios():
        if eid == activo:
            continue
        p.append(f"<div class='card'><b>{e(esc['nombre'])}</b><div class='para'>{e(esc['para'])}</div>"
                 f"<div class='idea'>{e(esc['idea'])}</div><div class='row'>"
                 f"<form method='post' action='/arrancar'><input type='hidden' name='id' value='{e(eid)}'>"
                 "<button>Empezar</button></form>"
                 f"<form method='post' action='/arrancar'><input type='hidden' name='id' value='{e(eid)}'>"
                 "<input type='hidden' name='cero' value='1'><button class='sec'>Desde cero</button></form></div></div>")
    p.append("<p class='sub' style='margin-top:24px'>«Empezar» reanuda la demo tal como la dejaste; «Desde cero» la "
             "vuelve a montar limpia (úsalo antes de cada visita). Solo hay una demo encendida a la vez.</p>"
             "</main></body></html>")
    return "".join(p).encode("utf-8")


class Menu(BaseHTTPRequestHandler):
    server_version = "Demostrador"

    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body=b"", extra=()):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'")
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if urlparse(self.path).path != "/":
            return self._send(404, b"No encontrado")
        self._send(200, pagina())
        ESTADO["ok"] = ESTADO["error"] = ""

    def do_POST(self):
        # Una web cualquiera abierta en el móvil no debe poder pulsar estos botones por ti.
        origen = self.headers.get("Origin", "")
        if origen and urlparse(origen).netloc != self.headers.get("Host", ""):
            return self._send(403, b"Origen no permitido")
        n = int(self.headers.get("Content-Length") or 0)
        d = parse_qs(self.rfile.read(n).decode("utf-8", "replace")) if n else {}
        ruta = urlparse(self.path).path
        ESTADO["ok"] = ESTADO["error"] = ""
        with _lock:
            try:
                if ruta == "/arrancar":
                    eid = d.get("id", [""])[0]
                    cero = d.get("cero", [""])[0] == "1"
                    M.arrancar(eid, desde_cero=cero)
                    ESTADO["ok"] = f"«{motor.escenario(eid)['nombre']}» en marcha" + (" (montada desde cero)" if cero else "")
                elif ruta == "/parar":
                    M.parar()
                    ESTADO["ok"] = "Demo parada"
                elif ruta == "/simular":
                    import random
                    M.simular_internet(f"{random.choice([8, 31, 51, 88, 185])}.{random.randint(1, 254)}."
                                       f"{random.randint(1, 254)}.{random.randint(1, 254)}")
                    ESTADO["ok"] = "Simulada una visita desde internet: recarga Hylanlock como admin"
                else:
                    return self._send(404, b"No encontrado")
            except KeyError:
                ESTADO["error"] = "Esa demo no existe."
            except Exception as ex:      # el menú no debe caerse nunca delante de un cliente
                ESTADO["error"] = str(ex) or traceback.format_exc(limit=1)
        self._send(303, extra=[("Location", "/")])


def main():
    os.makedirs(motor.DATOS, exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", PUERTO_MENU), Menu)
    print(f"\n  Demostrador listo: abre  http://127.0.0.1:{PUERTO_MENU}  en el navegador del móvil")
    print(f"  Hylanlock: {motor.hylanlock_app() or 'NO ENCONTRADO (ver README)'}")
    print(f"  Licencia:  {'OK' if os.path.isfile(motor.LICENCIA) else 'FALTA (ver README)'}")
    print("  Ctrl+C para salir.\n", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        M.parar()


if __name__ == "__main__":
    sys.exit(main())
