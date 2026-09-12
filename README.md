# Almada 2

Sistema independiente de gestión para la segunda Distribuidora Almada.

Este proyecto se creó a partir de la base técnica de Almada 1, pero no comparte
su base de datos, sus clientes, sus pedidos, sus solicitudes ni sus credenciales.

## Tecnología

- Frontend: Angular standalone.
- Backend: Flask.
- Base local de desarrollo: SQLite independiente en `backend/data/almada2.db`.

## Puesta en marcha

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:ALMADA2_ADMIN_USER="admin"
$env:ALMADA2_ADMIN_PASSWORD="elegir-una-clave-segura"
python app.py
```

### Frontend

En otra terminal:

```powershell
cd frontend\almada2-app
npm install
npm start
```

El frontend se abre normalmente en `http://localhost:4200` y el backend en
`http://127.0.0.1:5000`.

Si se inicia solamente para desarrollo sin definir variables, el acceso inicial
es `admin` / `almada2-dev`. Debe reemplazarse antes de usar el sistema fuera de
la computadora local.

## Pruebas rápidas

Con el entorno virtual del backend activo:

```powershell
python -m unittest discover -s backend\tests -v
```

Para verificar el frontend:

```powershell
cd frontend\almada2-app
npm run build
```

## Documentación del proyecto

- `REQUISITOS.md`: alcance confirmado para Almada 2.
- `PENDIENTES.md`: etapas y estado del desarrollo.
