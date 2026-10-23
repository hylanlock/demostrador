"""Seguridad: qué pasa si alguien abre el puerto del router (aviso de exposición) + 2FA."""

CLAVE = "demo1234"

ESCENARIO = {
    "orden": 4,
    "nombre": "Seguridad: aviso de exposición",
    "organizacion": "Clínica Dental Mar",
    "para": "Para el técnico del MSP: Hylanlock avisa si alguien lo deja expuesto a internet",
    "idea": "Hylanlock es para la red local. Si alguien abre el puerto en el router, lo detecta solo —sin consultar "
            "ningún servicio externo— y avisa al administrador al momento.",
    "usuarios": [("admin", CLAVE, "Administrador (el técnico del MSP)"),
                 ("recepcion", CLAVE, "Recepción de la clínica")],
    # La demo hace de "proxy de confianza" para poder simular visitas desde internet (botón del menú).
    "entorno": {"TRUSTED_PROXIES": "127.0.0.1/32"},
    "simular_internet": True,
    "guion": [
        "Entra como <b>admin</b> → Ajustes → <b>Exposición a internet</b>: «no se ha detectado ningún acceso».",
        "En el menú del demostrador pulsa <b>«Simular visita desde internet»</b> (hace como si alguien entrara desde una IP pública).",
        "Recarga Hylanlock: aparece el <b>aviso rojo</b> arriba, solo para administradores, y la IP en la tabla de Ajustes.",
        "Pulsa <b>Revisado</b>: desaparece… hasta que llegue una IP nueva (vuelve a simular).",
        "Explica: todo esto pasa <b>sin que nada salga de la red</b>; el aviso también queda en la auditoría.",
        "Extra: Mi perfil → <b>Verificación en dos pasos</b> para el administrador.",
    ],
}


def sembrar(ctx):
    ctx.usuario("admin", CLAVE, admin=True)
    ctx.usuario("recepcion", CLAVE)
    pac = ctx.departamento("Pacientes")
    ctx.db.add_membership("recepcion", pac)
    ctx.archivo(pac, None, "Consentimiento informado (plantilla).pdf",
                ["Consentimiento informado", "Plantilla de ejemplo"], por="admin")
    ctx.archivo(pac, None, "Citas semana 42.csv", ["día;hora;gabinete", "lunes;09:30;1"], por="recepcion")
