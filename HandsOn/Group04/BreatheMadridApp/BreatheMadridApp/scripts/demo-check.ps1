$ErrorActionPreference = 'Stop'
$failed = $false
$root = Split-Path -Parent $PSScriptRoot

function Pass([string]$message) { Write-Host "[OK] $message" -ForegroundColor Green }
function Fail([string]$message, [string]$fix) {
    $script:failed = $true
    Write-Host "[FALLO] $message" -ForegroundColor Red
    Write-Host "        Solución: $fix" -ForegroundColor Yellow
}

Push-Location $root
try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Fail 'Docker no está disponible.' 'Instala o inicia Docker Desktop y vuelve a ejecutar este script.'
    } else {
        try {
            docker info --format '{{.ServerVersion}}' *> $null
            if ($LASTEXITCODE -ne 0) { throw 'Motor de Docker inactivo' }
            Pass 'Motor de Docker disponible.'
            $services = @(docker compose ps --services --status running)
            if ($LASTEXITCODE -ne 0 -or $services -notcontains 'fuseki') {
                Fail 'Fuseki no está en ejecución.' 'Ejecuta docker compose up -d --build desde la raíz de BreatheMadrid.'
            } else {
                Pass 'Contenedor Fuseki en ejecución.'
            }
        } catch {
            Fail 'No se pudo consultar Docker Compose.' 'Inicia Docker Desktop y ejecuta docker compose up -d --build.'
        }
    }

    try {
        $query = 'SELECT * WHERE { } LIMIT 1'
        $response = Invoke-RestMethod -Uri 'http://localhost:3030/breathemadrid/sparql' -Method Post `
            -ContentType 'application/x-www-form-urlencoded' `
            -Headers @{ Accept = 'application/sparql-results+json' } -Body @{ query = $query } -TimeoutSec 10
        if ($null -eq $response.results.bindings) { throw 'Respuesta SPARQL JSON inválida' }
        Pass 'Endpoint accesible y respuesta SPARQL JSON válida.'
    } catch {
        Fail 'El endpoint no responde con SPARQL JSON.' 'Ejecuta docker compose up -d --build y consulta docker compose logs fuseki.'
    }

    try {
        & "$PSScriptRoot\verify-sparql.ps1" | ForEach-Object { Pass $_ }
    } catch {
        Fail 'Las consultas SPARQL no devuelven los recuentos esperados.' 'Comprueba el RDF montado en compose.yaml y ejecuta docker compose restart fuseki.'
    }

    $adbCommand = Get-Command adb -ErrorAction SilentlyContinue
    if ($adbCommand) {
        $adb = $adbCommand.Source
    } else {
        $adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
    }
    if (-not (Test-Path -LiteralPath $adb)) {
        Fail 'ADB no está disponible.' 'Instala Android SDK Platform-Tools o añade adb al PATH.'
    } else {
        Pass "ADB disponible: $adb"
        $devices = @(& $adb devices | Select-String '^([^\s]+)\s+device$' | ForEach-Object { $_.Matches[0].Groups[1].Value })
        if ($devices.Count -eq 0) {
            Fail 'No hay emulador o dispositivo conectado.' 'Inicia el emulador en Android Studio o conecta el móvil con depuración USB.'
        } elseif ($devices.Count -gt 1) {
            Fail 'Hay varios dispositivos conectados; no se configuró el túnel.' 'Deja uno conectado o ejecuta adb -s ID reverse tcp:3030 tcp:3030 para el elegido.'
        } else {
            Pass "Dispositivo conectado: $($devices[0])"
            $existing = @(& $adb -s $devices[0] reverse --list)
            if ($existing -match 'tcp:3030\s+tcp:3030') {
                Pass 'Túnel ADB tcp:3030 configurado.'
            } else {
                & $adb -s $devices[0] reverse tcp:3030 tcp:3030 | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Pass 'Túnel ADB tcp:3030 configurado ahora.'
                } else {
                    Fail 'No se pudo configurar el túnel ADB.' "Ejecuta adb -s $($devices[0]) reverse tcp:3030 tcp:3030."
                }
            }
        }
    }
} finally {
    Pop-Location
}

if ($failed) { exit 1 }
Write-Host 'Demo lista. Abre Datos semánticos y pulsa Consultar el grafo.' -ForegroundColor Green
