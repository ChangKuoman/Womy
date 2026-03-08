# Script de inicio rapido para el Bot de Telegram
# Ejecuta: .\start_telegram.ps1

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  AMIGA FINANCIERA - BOT DE TELEGRAM" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar archivo .env
if (-not (Test-Path ".env")) {
    Write-Host "Archivo .env no encontrado" -ForegroundColor Yellow
    Write-Host ""

    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Archivo .env creado desde .env.example" -ForegroundColor Green
        Write-Host ""
        Write-Host "IMPORTANTE: Configura tu bot de Telegram" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Pasos rapidos (2 minutos):" -ForegroundColor Yellow
        Write-Host "1. Abre Telegram y busca @BotFather" -ForegroundColor White
        Write-Host "2. Envia /newbot" -ForegroundColor White
        Write-Host "3. Sigue las instrucciones" -ForegroundColor White
        Write-Host "4. Copia el token que te da" -ForegroundColor White
        Write-Host "5. Edita el archivo .env y pega:" -ForegroundColor White
        Write-Host "   TELEGRAM_TOKEN=tu_token_aqui" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Tambien necesitas (registrate gratis):" -ForegroundColor Yellow
        Write-Host "   FEATHERLESS_API_KEY desde https://featherless.ai" -ForegroundColor White
        Write-Host ""
        Write-Host "Guia completa en: TELEGRAM_SETUP.md" -ForegroundColor Magenta
        Write-Host ""
        Write-Host "Presiona Enter despues de configurar el .env..." -ForegroundColor Cyan
        Read-Host
    }
}

# Verificar entorno virtual
if (-not (Test-Path "venv")) {
    Write-Host "Entorno virtual no encontrado" -ForegroundColor Yellow
    Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "Entorno virtual creado" -ForegroundColor Green
}

# Activar entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Cyan
& "venv\Scripts\Activate.ps1"

# Verificar e instalar dependencias
Write-Host "Verificando dependencias..." -ForegroundColor Cyan
$pipList = pip list 2>$null
if ($pipList -notmatch "fastapi") {
    Write-Host "Instalando dependencias..." -ForegroundColor Yellow
    pip install -r requirements.txt --quiet
    Write-Host "Dependencias instaladas" -ForegroundColor Green
}
else {
    Write-Host "Dependencias verificadas" -ForegroundColor Green
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  Iniciando Bot de Telegram..." -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tip: Busca tu bot en Telegram y envia /start" -ForegroundColor Yellow
Write-Host "Tip: Presiona Ctrl+C para detener el bot" -ForegroundColor Yellow
Write-Host ""

# Iniciar bot de Telegram
python src/main_telegram.py
