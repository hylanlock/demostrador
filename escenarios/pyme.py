"""Pyme con departamentos: cada uno ve lo suyo, permisos separados y auditoría."""

CLAVE = "demo1234"

ESCENARIO = {
    "orden": 3,
    "nombre": "Pyme: departamentos y permisos",
    "organizacion": "Talleres Costa S.L.",
    "para": "Cualquier pyme con varios departamentos (el cliente típico de un MSP)",
    "idea": "Pertenecer a la empresa no da acceso: cada departamento ve lo suyo, las subcarpetas son privadas desde "
            "que nacen y ver, subir, descargar y borrar son permisos distintos.",
    "usuarios": [("admin", CLAVE, "Administrador de sistemas"),
                 ("carmen", CLAVE, "Jefa de Contabilidad"),
                 ("javi", CLAVE, "Comercial (solo Ventas)"),
                 ("proveedor", CLAVE, "Proveedor: solo puede DEJAR albaranes, sin ver nada")],
    "guion": [
        "Entra como <b>javi</b>: solo ve <b>Ventas</b>. Contabilidad ni aparece.",
        "Entra como <b>carmen</b>: ve Contabilidad y su subcarpeta privada <b>Cierres</b>; javi no puede.",
        "Entra como <b>proveedor</b> → Ventas → <b>Albaranes</b>: puede subir, pero <b>no ve la lista</b> de lo que hay "
        "(buzón con cuenta: «dejar» y «ver» son permisos distintos).",
        "Entra como <b>admin</b> → Registro: todo lo que ha pasado, filtrable y exportable a CSV.",
        "Con <b>admin</b> → Ajustes → <b>Marca blanca</b>: cambia el nombre y el color y se aplica al momento "
        "(el MSP lo entrega con su marca o la del cliente).",
    ],
}


def sembrar(ctx):
    ctx.usuario("admin", CLAVE, admin=True)
    for u in ("carmen", "javi", "proveedor"):
        ctx.usuario(u, CLAVE)
    ven = ctx.departamento("Ventas")
    con = ctx.departamento("Contabilidad")
    ctx.db.add_membership("javi", ven)
    ctx.db.add_membership("carmen", con, "head")
    alb = ctx.subcarpeta(ven, "Albaranes")
    cie = ctx.subcarpeta(con, "Cierres")
    ctx.db.set_subfolder_access("proveedor", ven, alb, "depositor")
    ctx.archivo(ven, None, "Tarifa 2026.pdf", ["Tarifa de precios 2026", "Mano de obra: 48 EUR/h"], por="javi")
    ctx.archivo(ven, None, "Presupuesto flota Hermanos Gil.pdf", ["Presupuesto 2026-77", "Mantenimiento de 6 furgonetas"],
                por="javi", descargas=("carmen",))
    ctx.archivo(ven, alb, "Albaran 3381 recambios.pdf", ["Albarán 3381", "Pastillas de freno x 24"], dias=2, por="proveedor")
    ctx.archivo(con, None, "Previsión tesorería Q4.csv", ["mes;cobros;pagos", "octubre;48200;39150"], por="carmen")
    ctx.archivo(con, cie, "Cierre septiembre.pdf", ["Cierre contable de septiembre", "(ejemplo)"], dias=16, por="carmen")
