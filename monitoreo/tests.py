from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Cliente, Equipo, OrdenServicio


class BaseAPITest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("tecnico", password="clave-segura-123")
        self.api = APIClient()
        self.api.force_authenticate(self.usuario)
        self.cliente = Cliente.objects.create(
            nombre="Conjunto Los Pinos", tipo="conjunto", direccion="Calle 10 # 5-20, Neiva"
        )
        self.camara = Equipo.objects.create(
            cliente=self.cliente, tipo="camara", ubicacion="Portería", ip="192.168.1.50"
        )


class AutenticacionTest(TestCase):
    def test_sin_login_no_deja_entrar(self):
        respuesta = APIClient().get("/api/clientes/")
        self.assertEqual(respuesta.status_code, 401)

    def test_obtener_token(self):
        User.objects.create_user("ana", password="clave-segura-123")
        respuesta = APIClient().post(
            "/api/token/", {"username": "ana", "password": "clave-segura-123"}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("token", respuesta.data)


class ClienteTest(BaseAPITest):
    def test_crear_y_buscar_cliente(self):
        respuesta = self.api.post(
            "/api/clientes/",
            {"nombre": "Ferretería El Tornillo", "tipo": "empresa", "direccion": "Cra 7 # 8-10"},
        )
        self.assertEqual(respuesta.status_code, 201)
        busqueda = self.api.get("/api/clientes/?search=tornillo")
        self.assertEqual(busqueda.data["count"], 1)

    def test_cuenta_equipos(self):
        respuesta = self.api.get(f"/api/clientes/{self.cliente.id}/")
        self.assertEqual(respuesta.data["total_equipos"], 1)


class EquipoTest(BaseAPITest):
    def test_puerto_por_defecto_segun_tipo(self):
        self.assertEqual(self.camara.puerto_a_revisar, 554)
        self.camara.puerto = 8000
        self.assertEqual(self.camara.puerto_a_revisar, 8000)

    @patch("monitoreo.services.puerto_abierto", return_value=True)
    def test_revisar_equipo_en_linea(self, _):
        respuesta = self.api.post(f"/api/equipos/{self.camara.id}/revisar/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["estado"], "en_linea")
        self.assertIsNotNone(respuesta.data["ultima_revision"])

    @patch("monitoreo.services.puerto_abierto", return_value=False)
    def test_revisar_equipo_caido(self, _):
        respuesta = self.api.post(f"/api/equipos/{self.camara.id}/revisar/")
        self.assertEqual(respuesta.data["estado"], "fuera_de_linea")

    def test_filtrar_por_estado(self):
        respuesta = self.api.get("/api/equipos/?estado=sin_revisar")
        self.assertEqual(respuesta.data["count"], 1)

    def test_no_se_puede_cambiar_estado_a_mano(self):
        self.api.patch(f"/api/equipos/{self.camara.id}/", {"estado": "en_linea"})
        self.camara.refresh_from_db()
        self.assertEqual(self.camara.estado, "sin_revisar")


class OrdenServicioTest(BaseAPITest):
    def crear_orden(self):
        return self.api.post(
            "/api/ordenes/",
            {
                "cliente": self.cliente.id,
                "equipo": self.camara.id,
                "tipo": "falla",
                "descripcion": "La cámara de portería no da imagen",
            },
        )

    def test_crear_y_cerrar_orden(self):
        orden = self.crear_orden()
        self.assertEqual(orden.status_code, 201)
        cierre = self.api.post(
            f"/api/ordenes/{orden.data['id']}/cerrar/", {"solucion": "Se cambió el conector RJ45"}
        )
        self.assertEqual(cierre.status_code, 200)
        self.assertEqual(cierre.data["estado"], "cerrada")
        self.assertIsNotNone(cierre.data["cerrada_en"])

    def test_no_cerrar_dos_veces(self):
        orden = self.crear_orden()
        url = f"/api/ordenes/{orden.data['id']}/cerrar/"
        self.api.post(url, {"solucion": "Listo"})
        segunda = self.api.post(url, {"solucion": "Otra vez"})
        self.assertEqual(segunda.status_code, 400)

    def test_equipo_de_otro_cliente(self):
        otro = Cliente.objects.create(nombre="Casa Pérez", tipo="casa", direccion="Calle 1")
        respuesta = self.api.post(
            "/api/ordenes/",
            {"cliente": otro.id, "equipo": self.camara.id, "tipo": "falla", "descripcion": "x"},
        )
        self.assertEqual(respuesta.status_code, 400)


class ResumenTest(BaseAPITest):
    def test_resumen(self):
        OrdenServicio.objects.create(cliente=self.cliente, tipo="mantenimiento", descripcion="x")
        respuesta = self.api.get("/api/resumen/")
        self.assertEqual(respuesta.data["clientes"], 1)
        self.assertEqual(respuesta.data["equipos"]["sin_revisar"], 1)
        self.assertEqual(respuesta.data["ordenes_abiertas"]["mantenimiento"], 1)


class ComandoRevisarEquiposTest(BaseAPITest):
    @patch("monitoreo.services.puerto_abierto", return_value=False)
    def test_comando_marca_caidos(self, _):
        salida = StringIO()
        call_command("revisar_equipos", stdout=salida)
        self.camara.refresh_from_db()
        self.assertEqual(self.camara.estado, "fuera_de_linea")
        self.assertIn("1 fuera de línea", salida.getvalue())
