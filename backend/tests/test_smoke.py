import os
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


    def test_price_increases_round_up_to_ten_and_keep_history(self):
        provider = self.client.post(
            "/api/proveedores",
            json={"nombre": "Proveedor aumentos"}
        )
        self.assertEqual(provider.status_code, 201)
        provider_id = provider.get_json()["id"]

        product_with_variants = self.client.post(
            f"/api/proveedores/{provider_id}/productos",
            json={
                "nombre": "Producto aumento con variantes",
                "categoria": "Categoría aumentos",
                "variantes": [
                    {
                        "nombre_variante": "Medida A",
                        "codigo": "AUM-A",
                        "precio_venta": 101,
                        "stock": 1
                    },
                    {
                        "nombre_variante": "Medida B",
                        "codigo": "AUM-B",
                        "precio_venta": 205,
                        "stock": 1
                    }
                ]
            }
        )
        self.assertEqual(product_with_variants.status_code, 201)
        product_id = product_with_variants.get_json()["producto_id"]

        single_product = self.client.post(
            f"/api/proveedores/{provider_id}/productos",
            json={
                "nombre": "Producto aumento individual",
                "codigo": "AUM-IND",
                "categoria": "Categoría aumentos",
                "precio_venta": 333,
                "stock": 1
            }
        )
        self.assertEqual(single_product.status_code, 201)
        single_product_id = single_product.get_json()["producto_id"]

        options = self.client.get("/api/aumentos-precios/opciones")
        self.assertEqual(options.status_code, 200)
        option = next(
            item for item in options.get_json()["productos"]
            if item["id"] == product_id
        )
        self.assertEqual(option["precio_actual"], 101)
        self.assertNotIn("precio_reventa", option)

        preview = self.client.post(
            "/api/aumentos-precios/vista-previa",
            json={
                "modo": "individual",
                "porcentaje": 7,
                "producto_ids": [product_id]
            }
        )
        self.assertEqual(preview.status_code, 200)
        preview_data = preview.get_json()
        self.assertEqual(preview_data["cantidad_productos"], 1)
        self.assertEqual(preview_data["cantidad_precios"], 2)
        self.assertEqual(
            [item["precio_nuevo"] for item in preview_data["productos"][0]["precios"]],
            [110, 220]
        )

        applied = self.client.post(
            "/api/aumentos-precios",
            json={
                "modo": "individual",
                "porcentaje": 7,
                "producto_ids": [product_id]
            }
        )
        self.assertEqual(applied.status_code, 201)
        increase_id = applied.get_json()["aumento_id"]

        products = self.client.get("/api/productos").get_json()
        updated_product = next(
            item for item in products if item["id"] == product_id
        )
        self.assertEqual(updated_product["precio_venta"], 110)
        self.assertEqual(
            [item["precio_venta"] for item in updated_product["variantes"]],
            [110, 220]
        )

        partial = self.client.post(
            "/api/aumentos-precios",
            json={
                "modo": "parcial",
                "porcentaje": 10,
                "proveedor_id": provider_id,
                "producto_ids": [single_product_id]
            }
        )
        self.assertEqual(partial.status_code, 201)

        products = self.client.get("/api/productos").get_json()
        updated_single = next(
            item for item in products if item["id"] == single_product_id
        )
        self.assertEqual(updated_single["precio_venta"], 370)

        history = self.client.get("/api/aumentos-precios/historial")
        self.assertEqual(history.status_code, 200)
        self.assertGreaterEqual(len(history.get_json()), 2)

        detail = self.client.get(
            f"/api/aumentos-precios/historial/{increase_id}"
        )
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(len(detail.get_json()["detalles"]), 2)
        self.assertNotIn("precio_reventa", detail.get_json()["detalles"][0])

        general_preview = self.client.post(
            "/api/aumentos-precios/vista-previa",
            json={"modo": "general", "porcentaje": 5}
        )
        self.assertEqual(general_preview.status_code, 200)
        self.assertEqual(general_preview.get_json()["modo"], "general")

        invalid = self.client.post(
            "/api/aumentos-precios/vista-previa",
            json={"modo": "general", "porcentaje": 0}
        )
        self.assertEqual(invalid.status_code, 400)


    def test_vendor_stock_trip_and_sale_flow(self):
        provider = self.client.post(
            "/api/proveedores",
            json={"nombre": "Proveedor viaje"}
        )
        self.assertEqual(provider.status_code, 201)
        provider_id = provider.get_json()["id"]

        product_response = self.client.post(
            f"/api/proveedores/{provider_id}/productos",
            json={
                "nombre": "Producto de viaje",
                "codigo": "VIAJE-001",
                "precio_venta": 1000,
                "stock": 12,
                "precio_base": 800,
                "iva": 0,
                "ganancia": 25
            }
        )
        self.assertEqual(product_response.status_code, 201)
        producto_id = product_response.get_json()["producto_id"]

        client_response = self.client.post(
            "/api/clientes",
            json={"nombre": "Cliente cuenta viaje"}
        )
        self.assertEqual(client_response.status_code, 201)
        cliente_id = client_response.get_json()["cliente_id"]

        seller_response = self.client.post(
            "/api/vendedores",
            json={
                "nombre": "Vendedor prueba",
                "usuario": "vendedor-prueba",
                "contrasena": "1234",
                "zona": "Zona norte"
            }
        )
        self.assertEqual(seller_response.status_code, 201)
        vendedor_id = seller_response.get_json()["id"]

        seller_login = self.client.post(
            "/api/login",
            json={
                "usuario": "vendedor-prueba",
                "contrasena": "1234"
            }
        )
        self.assertEqual(seller_login.status_code, 200)
        self.assertEqual(seller_login.get_json()["rol"], "vendedor")
        self.assertEqual(seller_login.get_json()["vendedor_id"], vendedor_id)

        assigned = self.client.post(
            f"/api/vendedores/{vendedor_id}/stock-viaje/asignar",
            json={"producto_id": producto_id, "cantidad": 5}
        )
        self.assertEqual(assigned.status_code, 201)
        self.assertEqual(assigned.get_json()["stock_viaje"], 5)
        self.assertEqual(assigned.get_json()["stock_central"], 7)

        returned = self.client.post(
            f"/api/vendedores/{vendedor_id}/stock-viaje/devolver",
            json={"producto_id": producto_id, "cantidad": 1}
        )
        self.assertEqual(returned.status_code, 200)
        self.assertEqual(returned.get_json()["stock_viaje"], 4)
        self.assertEqual(returned.get_json()["stock_central"], 8)

        sale = self.client.post(
            f"/api/vendedores/{vendedor_id}/ventas",
            json={
                "cliente_id": cliente_id,
                "forma_pago": "Cuenta corriente",
                "items": [
                    {
                        "producto_id": producto_id,
                        "cantidad": 2
                    }
                ]
            }
        )
        self.assertEqual(sale.status_code, 201)
        self.assertEqual(sale.get_json()["total"], 2000)

        trip_stock = self.client.get(
            f"/api/vendedores/{vendedor_id}/stock-viaje"
        ).get_json()
        self.assertEqual(len(trip_stock), 1)
        self.assertEqual(trip_stock[0]["cantidad"], 2)

        account = self.client.get(
            f"/api/clientes/{cliente_id}/cuenta-corriente"
        ).get_json()
        self.assertEqual(account["saldo_actual"], 2000)
        self.assertEqual(account["movimientos"][0]["tipo"], "Venta vendedor")

    def test_visual_catalog_tracks_stock_without_private_data(self):
        provider = self.client.post(
            "/api/proveedores",
            json={"nombre": "Proveedor catálogo visual"}
        )
        self.assertEqual(provider.status_code, 201)

        product_response = self.client.post(
            f"/api/proveedores/{provider.get_json()['id']}/productos",
            json={
                "nombre": "Bisagra catálogo visual",
                "descripcion": "Bisagra reforzada para muebles.",
                "categoria": "Bisagras",
                "foto": "catalogo-productos/bisagra-prueba.webp",
                "precio_base": 500,
                "ganancia": 40,
                "variantes": [
                    {
                        "nombre_variante": "35 mm",
                        "codigo": "CAT-35",
                        "cantidad_caja": 1,
                        "precio_venta": 700,
                        "stock": 2
                    },
                    {
                        "nombre_variante": "40 mm",
                        "codigo": "CAT-40",
                        "cantidad_caja": 1,
                        "precio_venta": 800,
                        "stock": 1
                    }
                ]
            }
        )
        self.assertEqual(product_response.status_code, 201)
        producto_id = product_response.get_json()["producto_id"]

        seller_response = self.client.post(
            "/api/vendedores",
            json={
                "nombre": "Vendedor catálogo",
                "usuario": "vendedor-catalogo",
                "contrasena": "1234"
            }
        )
        self.assertEqual(seller_response.status_code, 201)
        vendedor_id = seller_response.get_json()["id"]

        catalog_response = self.client.get(
            f"/api/vendedores/{vendedor_id}/catalogo-visual"
        )
        self.assertEqual(catalog_response.status_code, 200)
        self.assertEqual(catalog_response.headers["Cache-Control"], "no-store")

        product = next(
            item for item in catalog_response.get_json()["productos"]
            if item["id"] == producto_id
        )
        self.assertFalse(product["disponible"])
        self.assertNotIn("precio_venta", product)
        self.assertNotIn("proveedor", product)
        self.assertNotIn("cantidad_viaje", product)
        self.assertEqual(len(product["variantes"]), 2)
        self.assertNotIn("precio_venta", product["variantes"][0])
        self.assertNotIn("stock", product["variantes"][0])

        assigned = self.client.post(
            f"/api/vendedores/{vendedor_id}/stock-viaje/asignar",
            json={"producto_id": producto_id, "cantidad": 2}
        )
        self.assertEqual(assigned.status_code, 201)

        available_catalog = self.client.get(
            f"/api/vendedores/{vendedor_id}/catalogo-visual"
        ).get_json()
        available_product = next(
            item for item in available_catalog["productos"]
            if item["id"] == producto_id
        )
        self.assertTrue(available_product["disponible"])

        client_response = self.client.post(
            "/api/clientes",
            json={"nombre": "Cliente catálogo visual"}
        )
        self.assertEqual(client_response.status_code, 201)

        sale = self.client.post(
            f"/api/vendedores/{vendedor_id}/ventas",
            json={
                "cliente_id": client_response.get_json()["cliente_id"],
                "forma_pago": "Efectivo",
                "items": [
                    {"producto_id": producto_id, "cantidad": 2}
                ]
            }
        )
        self.assertEqual(sale.status_code, 201)

        unavailable_catalog = self.client.get(
            f"/api/vendedores/{vendedor_id}/catalogo-visual"
        ).get_json()
        unavailable_product = next(
            item for item in unavailable_catalog["productos"]
            if item["id"] == producto_id
        )
        self.assertFalse(unavailable_product["disponible"])



if __name__ == "__main__":
    unittest.main()
