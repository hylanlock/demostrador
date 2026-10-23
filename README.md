# 📱 Demostrador

Demos **reales** de mis productos que llevo en el móvil. Hoy: **Hylanlock**, con cuatro escenarios listos.

La idea: llego a una MSP o a un cliente, enciendo el **punto de acceso del móvil**, su portátil se conecta
y abre Hylanlock. **El servidor está en mi bolsillo, sin internet y sin nube**: la prueba viva de que nada
sale de su red.

```
 [móvil: Ubuntu en Termux]
   demostrador.py  ── menú en http://127.0.0.1:8080  (solo lo ve el móvil)
        │ arranca / para / reinicia
        ▼
   Hylanlock real  ── http://<IP del punto de acceso>:8000  (lo abre el portátil del cliente)
```

## Escenarios

| Demo | Para quién | Lo que enseña |
|---|---|---|
| 🧾 **Gestoría: buzón de facturas** | Gestorías y su MSP | El cliente deja facturas en un enlace sin cuenta y sin ver nada; la gestoría lo recibe con auditoría e IP |
| ⚖️ **Despacho: gestionar sin leer** | Despachos, clínicas, el técnico del MSP | Gobernanza (el Supervisor ve la salud sin ver archivos), papelera, 2FA |
| 🏢 **Pyme: departamentos y permisos** | Cualquier pyme | Cada departamento ve lo suyo, subcarpetas privadas, proveedor que solo deja albaranes, marca blanca |
| 🛡️ **Seguridad: aviso de exposición** | El técnico del MSP | Botón "Simular visita desde internet" → Hylanlock avisa solo |

Cada escenario trae **empresa ficticia, usuarios (contraseña `demo1234`) y un guion paso a paso** que sale en el menú.
Los PDF de ejemplo son reales: se pueden descargar y abrir.

## Instalar en el móvil (una vez)

En el Ubuntu de Termux:

```bash
git clone <URL de este repo> demostrador
cd demostrador
bash instalar-movil.sh
```

`instalar-movil.sh` instala Python y git si faltan y descarga Hylanlock dentro de la carpeta.

**Licencia de demo** (no se sube nunca, ver `.gitignore`): en el PC, en la carpeta de Hylanlock:

```bash
python tools/license_gen.py -c "Demo Nicolas" -t commercial --expires 2027-12-31 -o demo
```

y copia el texto del `.txt` al móvil como `licencias/hylanlock.license.key`.

## Usarlo

```bash
python3 demostrador.py
```

Abre **http://127.0.0.1:8080** en el navegador del móvil →
1. **Desde cero** en la demo que vayas a enseñar (déjala limpia antes de cada visita).
2. Activa el **punto de acceso** del móvil y que el cliente se conecte.
3. El menú te dice la dirección que debe abrir (`http://192.168.x.x:8000`), los usuarios y el guion.

- **Empezar** reanuda la demo como la dejaste; **Desde cero** la vuelve a montar.
- Solo hay una demo encendida a la vez (el móvil no es un servidor de verdad).
- Actualizar Hylanlock en el móvil: `bash instalar-movil.sh` (hace `git pull`).

## Añadir un escenario

Copia `escenarios/pyme.py` y cambia `ESCENARIO` (textos, usuarios, guion) y `sembrar(ctx)` (los datos):

| `ctx.` | Para qué |
|---|---|
| `usuario(nombre, clave, admin=False)` | crear un usuario |
| `departamento(nombre)` → slug | crear un departamento |
| `subcarpeta(dep, nombre)` → slug | crear una subcarpeta (privada) |
| `archivo(dep, sub, nombre, lineas=[…], dias=0, por="usuario", descargas=("x",))` | archivo con huella; PDF real si acaba en `.pdf`; `dias` lo envejece; `por` deja el evento de subida |
| `buzon(dep, sub, etiqueta)` | enlace de buzón (sale en el menú) |
| `db.*` | cualquier función de `app/db.py` de Hylanlock (`add_membership`, `set_supervisor`…) |

Opciones de `ESCENARIO`: `entorno` (variables `HYLANLOCK_*` sin prefijo) y `simular_internet: True` (botón en el menú).

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Cada escenario se monta, arranca un Hylanlock real y se comprueba que sus usuarios entran y que su guion
funciona. Usan la licencia de pruebas de Hylanlock: no necesitan la tuya.

## Seguridad

- El menú escucha **solo en 127.0.0.1**: quien se conecte a tu punto de acceso no puede tocar el panel.
- Las demos son datos ficticios; aun así, **no subas nada real** a una demo.
- La licencia y los datos de las demos están en `.gitignore`.
