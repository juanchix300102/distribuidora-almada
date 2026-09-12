import os
import io
import tempfile
import unittest
from pathlib import Path


class Almada2SmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.temp_dir.name) / "almada2-test.db"

        os.environ["ALMADA2_DB_PATH"] = str(cls.db_path)
        os.environ["ALMADA2_ADMIN_USER"] = "admin-test"
        os.environ["ALMADA2_ADMIN_PASSWORD"] = "clave-test-segura"

        import app as backend

        cls.backend = backend
        backend.app.config.update(TESTING=True)
        backend.crear_tablas()
        backend.asegurar_columnas()
        backend.cargar_datos_iniciales()
        cls.client = backend.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_health_and_admin_login(self):
        health = self.client.get("/")
        self.assertEqual(health.status_code, 200)
        self.assertIn("Almada 2", health.get_json()["mensaje"])

        login = self.client.post(
            "/api/login",
            json={
                "usuario": "admin-test",
                "contrasena": "clave-test-segura"
            }
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.get_json()["rol"], "admin")

    def test_database_does_not_create_client_portal_tables(self):
        connection = self.backend.conectar_db()
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        connection.close()

        self.assertNotIn("pedidos", tables)
        self.assertNotIn("pedido_detalle", tables)
        self.assertNotIn("solicitudes_clientes", tables)
        self.assertNotIn("configuracion_reventa", tables)

    def test_internal_client_registration_remains_available(self):
        response = self.client.post(
            "/api/clientes",
            json={
                "nombre": "Cliente de prueba",
                "localidad": "Córdoba"
            }
        )
        self.assertEqual(response.status_code, 201)

        clients = self.client.get("/api/clientes")
        self.assertEqual(clients.status_code, 200)
        self.assertEqual(len(clients.get_json()), 1)
        self.assertNotIn("usuario", clients.get_json()[0])

    def test_removed_public_modules_return_not_found(self):
        self.assertEqual(
            self.client.get("/api/solicitudes-clientes").status_code,
            404
        )
        self.assertEqual(self.client.get("/api/pedidos").status_code, 404)

    def test_product_crud_has_no_reventa_field(self):
        provider = self.client.post(
            "/api/proveedores",
            json={"nombre": "Proveedor de prueba"}
        )
        self.assertEqual(provider.status_code, 201)
        provider_id = provider.get_json()["id"]

        payload = {
            "nombre": "Producto de prueba",
            "precio_base": 100,
            "ganancia": 40,
            "variantes": [
                {
                    "nombre_variante": "Única",
                    "codigo": "PR-001",
                    "cantidad_caja": 1,
                    "precio_unidad": 140,
                    "precio_caja": 140,
                    "precio_venta": 140,
                    "stock": 10
                }
            ]
        }

        created = self.client.post(
            f"/api/proveedores/{provider_id}/productos",
            json=payload
        )
        self.assertEqual(created.status_code, 201)

        products = self.client.get("/api/productos").get_json()
        product = next(
            item for item in products
            if item["nombre"] == "Producto de prueba"
        )

        self.assertNotIn("precio_reventa", product)
        self.assertNotIn("precio_reventa", product["variantes"][0])

        payload["variantes"][0]["id"] = product["variantes"][0]["id"]
        payload["variantes"][0]["precio_venta"] = 155

        updated = self.client.put(
            f"/api/productos/{product['id']}",
            json=payload
        )
        self.assertEqual(updated.status_code, 200)

    def test_csv_import_without_reventa_column(self):
        csv_content = (
            "Proveedor;Código;Producto;Precio venta;Stock\n"
            "Proveedor CSV;CSV-001;Producto CSV;2500;5\n"
        ).encode("utf-8")

        response = self.client.post(
            "/api/importar-catalogo",
            data={
                "tipo_importacion": "catalogo_completo",
                "archivo": (io.BytesIO(csv_content), "catalogo.csv")
            },
            content_type="multipart/form-data"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["productos_creados"], 1)


if __name__ == "__main__":
    unittest.main()
