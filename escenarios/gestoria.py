"""Gestoría: los clientes dejan facturas en un buzón sin ver nada más (el WOW de Hylanlock)."""

CLAVE = "demo1234"

ESCENARIO = {
    "orden": 1,
    "nombre": "Gestoría: buzón de facturas",
    "organizacion": "Gestoría Martín & Asociados",
    "para": "Gestorías, asesorías y cualquier MSP que les dé soporte",
    "idea": "Los clientes de la gestoría dejan sus facturas en un buzón: no ven nada más, no necesitan cuenta, "
            "y la gestoría lo recibe todo en su propio servidor, con quién y desde dónde lo dejó.",
    "usuarios": [("marta", CLAVE, "Administradora de la gestoría"),
                 ("luis", CLAVE, "Asesor fiscal (jefe del departamento Clientes)"),
                 ("becaria", CLAVE, "Empleada: solo ve Clientes, no las carpetas privadas")],
    "guion": [
        "Entra como <b>luis</b>: en Departamentos → Clientes → <b>Facturas recibidas</b> ves lo que han dejado los clientes.",
        "En el portátil del cliente (o en otra pestaña) abre el <b>enlace de buzón</b> de abajo: solo se ve una zona "
        "para soltar archivos. <b>No hay lista, ni nombres, ni cuenta.</b>",
        "Deja un archivo cualquiera escribiendo un nombre (p. ej. «Talleres Costa»).",
        "Vuelve a la pestaña de luis: el archivo ha aparecido, con su huella SHA-256.",
        "Entra como <b>marta</b> → Registro: la auditoría dice quién lo dejó, cuándo y <b>desde qué IP</b>.",
        "Entra como <b>becaria</b>: ve Clientes, pero no la subcarpeta privada <b>Nóminas</b> de Recursos Humanos.",
    ],
}


def sembrar(ctx):
    ctx.usuario("marta", CLAVE, admin=True)
    ctx.usuario("luis", CLAVE)
    ctx.usuario("becaria", CLAVE)
    cli = ctx.departamento("Clientes")
    rrhh = ctx.departamento("Recursos Humanos")
    ctx.db.add_membership("luis", cli, "head")
    ctx.db.add_membership("becaria", cli)
    fact = ctx.subcarpeta(cli, "Facturas recibidas")
    nom = ctx.subcarpeta(rrhh, "Nominas")
    ctx.archivo(cli, None, "Calendario fiscal 2026.pdf", ["Calendario fiscal 2026", "", "20 de octubre: modelo 303 (IVA, 3T)",
                                                         "20 de octubre: modelo 130 (IRPF, 3T)"], por="luis")
    ctx.archivo(cli, None, "Plantilla de gastos.csv", ["fecha;concepto;importe", "2026-10-01;Gasolina;54,20"], por="luis")
    ctx.archivo(cli, fact, "Factura 2026-118 Talleres Costa.pdf",
                ["Talleres Costa S.L.", "Factura 2026-118", "Reparación de flota: 1.240,00 EUR"], dias=3, por="enlace: Talleres Costa")
    ctx.archivo(cli, fact, "Factura 0457 Panadería Sol.pdf",
                ["Panadería Sol", "Factura 0457", "Harinas y levaduras: 389,50 EUR"], dias=1, por="enlace: Panadería Sol",
                descargas=("luis",))
    ctx.archivo(rrhh, nom, "Nominas septiembre.pdf", ["Nóminas de septiembre", "(documento de ejemplo)"], dias=20, por="marta")
    ctx.buzon(cli, fact, "Facturas de clientes (enlace para enviar a los clientes)")
