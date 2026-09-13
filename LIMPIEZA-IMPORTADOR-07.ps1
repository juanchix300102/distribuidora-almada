$ErrorActionPreference = "Stop"

Write-Host "Almada 2 - eliminando archivos antiguos de Importar catalogo..."

$paths = @(
  "frontend\almada2-app\src\app\components\importador-catalogo",
  "frontend\almada2-app\src\app\services\api\importacion-api.service.ts",
  "backend\routes\importador_catalogo.py"
)

foreach ($path in $paths) {
  if (Test-Path $path) {
    Remove-Item $path -Recurse -Force
    Write-Host "Eliminado: $path"
  }
}

Write-Host "Listo. Productos y Catalogo visual se mantienen sin cambios."
