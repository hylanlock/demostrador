"""Despacho: el técnico del MSP gestiona sin leer (Gobernanza), papelera y verificación en dos pasos."""

CLAVE = "demo1234"

ESCENARIO = {
    "orden": 2,
    "nombre": "Despacho: gestionar sin leer",
    "organizacion": "Despacho Ruiz Abogados",
    "para": "Despachos, clínicas y el técnico del MSP que los mantiene (RGPD)",
    "idea": "El técnico del MSP ve la salud de todas las carpetas —tamaño, antigüedad, accesos, duplicados— "
            "SIN abrir ni ver el nombre de ningún archivo. Y nada se borra de golpe: hay papelera.",
    "usuarios": [("elena", CLAVE, "Socia y administradora"),
                 ("tecnico", CLAVE, "Técnico del MSP: rol Supervisor (no lee nada)"),
                 ("pablo", CLAVE, "Abogado del área Mercantil")],
    "guion": [
        "Entra como <b>tecnico</b> → <b>Gobernanza</b>: carpetas, tamaños, archivos antiguos, <b>duplicados</b> y quién "
        "tiene acceso… y ningún nombre de archivo. Así un MSP mantiene sin ver datos de clientes.",
        "Con <b>tecnico</b>, intenta abrir una carpeta del despacho: <b>no puede</b>. Ve la estructura, no el contenido.",
        "Entra como <b>elena</b> → abre Mercantil y borra un archivo: va a la <b>Papelera</b>, no desaparece.",
        "En <b>Papelera</b>, restáuralo: vuelve a su carpeta exacta.",
        "Con <b>elena</b> → Mi perfil → <b>Verificación en dos pasos</b>: actívala con el móvil del cliente "
        "(Google Authenticator o similar) y cierra sesión para ver el segundo paso.",
    ],
}


def sembrar(ctx):
    ctx.usuario("elena", CLAVE, admin=True)
    ctx.usuario("tecnico", CLAVE)
    ctx.usuario("pablo", CLAVE)
    ctx.db.set_supervisor("tecnico", True)
    mer = ctx.departamento("Mercantil")
    lab = ctx.departamento("Laboral")
    arc = ctx.departamento("Archivo")
    ctx.db.add_membership("pablo", mer)
    exp = ctx.subcarpeta(mer, "Expedientes 2026")
    contrato = ["Contrato de compraventa de participaciones", "Borrador v3 (ejemplo)"]
    ctx.archivo(mer, exp, "Compraventa participaciones v3.pdf", contrato, por="pablo", descargas=("elena",))
    ctx.archivo(mer, exp, "Estatutos sociales.pdf", ["Estatutos sociales", "(ejemplo)"], por="pablo")
    ctx.archivo(mer, None, "Minuta de honorarios.pdf", ["Minuta de honorarios", "Expediente 2026/031"], por="elena")
    ctx.archivo(lab, None, "Demanda despido (borrador).pdf", ["Demanda por despido", "Borrador — confidencial"], dias=12,
                por="elena")
    ctx.archivo(lab, None, "Copia compraventa (de Mercantil).pdf", contrato, dias=5, por="elena")   # duplicado
    ctx.archivo(arc, None, "Expediente 2021-114.pdf", ["Expediente cerrado 2021-114"], dias=420)        # antiguo
    ctx.archivo(arc, None, "Expediente 2022-009.pdf", ["Expediente cerrado 2022-009"], dias=390)
