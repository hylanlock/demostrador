"""Pruebas del demostrador: cada escenario se monta, arranca un Hylanlock REAL y su guion funciona.

    python -m unittest discover -s tests -v      (desde la carpeta demostrador)

Usa la licencia de PRUEBAS de Hylanlock (hylanlock/tests/harness.py): no hace falta tu licencia de demo.
"""
import html
import json
import os
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import motor  # noqa: E402

APP = motor.hylanlock_app()
sys.path.insert(0, os.path.join(os.path.dirname(APP), "tests"))
import harness  # noqa: E402  (arnés de pruebas de Hylanlock)


class TestEscenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="demostrador_")
        motor.DATOS = cls.tmp                       # nunca tocar datos/ reales
        cls.m = motor.Motor(puerto=harness.free_port(),
                            runner=os.path.join(os.path.dirname(APP), "tests", "_run_server.py"),
                            licencia_texto=harness.test_license(),
                            extra_env={"HYLANLOCK_TEST_LICENSE_PUBKEY": harness.TEST_PUBKEY.hex()})
        cls.base = f"http://127.0.0.1:{cls.m.puerto}"

    @classmethod
    def tearDownClass(cls):
        cls.m.parar()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def arrancar(self, eid):
        self.m.arrancar(eid, desde_cero=True)
        return motor.escenario(eid)

    def cliente(self, usuario=None, clave=None):
        c = harness.Client(self.base)
        if usuario:
            self.assertEqual(c.login(usuario, clave), 302, f"{usuario} no puede entrar")
        return c

    def test_todos_los_escenarios_arrancan_y_sus_usuarios_entran(self):
        ids = [eid for eid, _ in motor.escenarios()]
        self.assertGreaterEqual(len(ids), 4)
        for eid in ids:
            with self.subTest(escenario=eid):
                esc = self.arrancar(eid)
                for k in ("nombre", "organizacion", "para", "idea", "usuarios", "guion"):
                    self.assertTrue(esc.get(k), f"{eid}: falta {k}")
                for u, c, _ in esc["usuarios"]:
                    self.cliente(u, c)
                self.assertIn(html.escape(esc["organizacion"]), self.cliente(*esc["usuarios"][0][:2]).get("/")[1])

    def test_gestoria_buzon(self):
        self.arrancar("gestoria")
        enlace = motor.info("gestoria")["enlaces"][0]["ruta"]
        s, body, _ = self.cliente().get(enlace)
        self.assertEqual(s, 200)
        self.assertIn("Dejar un archivo", body)
        luis = self.cliente("luis", "demo1234")
        nombres = [f["name"] for f in json.loads(luis.get("/api/dep/clientes/sub/facturas-recibidas")[1])]
        self.assertIn("Factura 2026-118 Talleres Costa.pdf", nombres)
        becaria = self.cliente("becaria", "demo1234")
        self.assertEqual(becaria.get("/api/dep/recursos-humanos/sub/nominas")[0], 403)

    def test_pdfs_son_validos(self):
        self.arrancar("gestoria")
        ruta = os.path.join(motor.datos_de("gestoria"), "departamentos", "clientes", "Calendario fiscal 2026.pdf")
        with open(ruta, "rb") as f:
            datos = f.read()
        self.assertTrue(datos.startswith(b"%PDF-1.4") and datos.rstrip().endswith(b"%%EOF"))
        self.assertIn(b"startxref", datos)

    def test_despacho_supervisor_no_lee(self):
        self.arrancar("despacho")
        t = self.cliente("tecnico", "demo1234")
        s, body, _ = t.get("/gobernanza")
        self.assertEqual(s, 200)
        self.assertNotIn("Compraventa", body)                     # ningún nombre de archivo
        k = json.loads(body.split("const GOV = ", 1)[1].split(";\n", 1)[0])["kpi"]
        self.assertEqual((k["dup_copies"], k["old_files"]), (1, 2))  # el guion enseña duplicados y antiguos
        self.assertEqual(t.get("/api/dep/mercantil")[0], 403)

    def test_seguridad_simular_internet(self):
        self.arrancar("seguridad")
        adm = self.cliente("admin", "demo1234")
        self.assertNotIn("expo-banner", adm.get("/")[1])
        self.m.simular_internet("8.8.8.8")
        self.assertIn("expo-banner", adm.get("/")[1])

    def test_reanudar_conserva_y_desde_cero_limpia(self):
        self.arrancar("pyme")
        marca = os.path.join(motor.datos_de("pyme"), "departamentos", "ventas", "nuevo.txt")
        with open(marca, "w") as f:
            f.write("x")
        self.m.arrancar("pyme")                                    # «Empezar»: reanuda
        self.assertTrue(os.path.exists(marca))
        self.m.arrancar("pyme", desde_cero=True)                   # «Desde cero»: limpia
        self.assertFalse(os.path.exists(marca))


class TestMenu(unittest.TestCase):
    def test_menu_se_pinta_y_escapa(self):
        import demostrador
        html = demostrador.pagina().decode("utf-8")
        for eid, esc in motor.escenarios():
            self.assertIn(esc["nombre"].replace("&", "&amp;"), html)
        self.assertIn("Demostrador", html)

    def test_escenario_inexistente(self):
        with self.assertRaises(KeyError):
            motor.escenario("../motor")


if __name__ == "__main__":
    unittest.main()
