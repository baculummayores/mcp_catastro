# Setup automatizado del entorno virtual para MCP Catastro
# Ejecutar: .\setup-env.ps1

Write-Host "🐍 CONFIGURANDO ENTORNO VIRTUAL PARA MCP CATASTRO" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "mcp_server.py")) {
    Write-Host "❌ Error: No se encuentra mcp_server.py" -ForegroundColor Red
    Write-Host "   Ejecuta este script desde la carpeta del proyecto" -ForegroundColor Yellow
    exit 1
}

# Crear entorno virtual si no existe
if (-not (Test-Path "venv_mcp")) {
    Write-Host "📦 Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv venv_mcp
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error creando entorno virtual" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Entorno virtual creado" -ForegroundColor Green
} else {
    Write-Host "📦 Entorno virtual ya existe" -ForegroundColor Green
}

# Activar entorno virtual
Write-Host "🔄 Activando entorno virtual..." -ForegroundColor Yellow
& ".\venv_mcp\Scripts\Activate.ps1"

# Verificar activación
$pythonPath = (Get-Command python).Source
if ($pythonPath -like "*venv_mcp*") {
    Write-Host "✅ Entorno virtual activado correctamente" -ForegroundColor Green
    Write-Host "   Python: $pythonPath" -ForegroundColor Gray
} else {
    Write-Host "❌ Error: Entorno virtual no se activó correctamente" -ForegroundColor Red
    exit 1
}

# Actualizar pip
Write-Host "⬆️ Actualizando pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# Instalar dependencias
Write-Host "📚 Instalando dependencias..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

# Verificar instalación crítica
Write-Host "🔍 Verificando dependencias críticas..." -ForegroundColor Yellow
$dependencies = @("mcp", "httpx", "pydantic")
$allGood = $true

foreach ($dep in $dependencies) {
    try {
        python -c "import $dep; print('✅ $dep: OK')"
    } catch {
        Write-Host "❌ $dep: FALLO" -ForegroundColor Red
        $allGood = $false
    }
}

if ($allGood) {
    Write-Host "`n🎉 ¡ENTORNO CONFIGURADO EXITOSAMENTE!" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Green
    Write-Host "🚀 Comandos disponibles:" -ForegroundColor Cyan
    Write-Host "   python mcp_server.py                 # Iniciar servidor MCP" -ForegroundColor White
    Write-Host "   python scripts/test-startup.py       # Test básico" -ForegroundColor White
    Write-Host "   python scripts/test-mcp-local.py     # Test completo" -ForegroundColor White
    Write-Host "   deactivate                           # Salir del entorno" -ForegroundColor White
    Write-Host "`n💡 Tu entorno está listo para trabajar con MCP" -ForegroundColor Yellow
} else {
    Write-Host "`n⚠️ Hay problemas con las dependencias" -ForegroundColor Red
    Write-Host "   Revisa los errores arriba" -ForegroundColor Yellow
}

Write-Host "`n🔥 Para empezar las pruebas:" -ForegroundColor Cyan
Write-Host "   python scripts/test-startup.py" -ForegroundColor White