# strumenti/server.ps1 — accende, spegne e riavvia i due server di sviluppo di PitWall.
#
#   .\strumenti\server.ps1 avvia      backend (:8000) e frontend (:3000)
#   .\strumenti\server.ps1 ferma      li spegne tutti e due
#   .\strumenti\server.ps1 riavvia    solo il backend: va fatto dopo ogni modifica a
#                                     backend, guide o catalogo (non si ricarica da solo)
#   .\strumenti\server.ps1 stato      chi è acceso
#
# Il backend parte staccato dal terminale e SENZA --reload: su Windows --reload continua a
# servire il codice vecchio (HAZARD-V2-B in INCIDENTS.md).
param([ValidateSet("avvia", "ferma", "riavvia", "stato")][string]$Azione = "stato")

$radice = Split-Path -Parent $PSScriptRoot
$python = Join-Path $radice "backend\.venv\Scripts\python.exe"

function Processo-Sulla-Porta([int]$porta) {
    (Get-NetTCPConnection -LocalPort $porta -State Listen -ErrorAction SilentlyContinue).OwningProcess | Select-Object -Unique
}

function Ferma([int]$porta, [string]$nome) {
    $id = Processo-Sulla-Porta $porta
    if ($id) {
        $id | ForEach-Object { Stop-Process -Id $_ -Force -Confirm:$false }
        "$nome spento (porta $porta)."
    } else { "$nome era già spento." }
}

function Risponde([string]$url, [int]$secondi) {
    $fine = (Get-Date).AddSeconds($secondi)
    while ((Get-Date) -lt $fine) {
        try { Invoke-WebRequest -UseBasicParsing $url -TimeoutSec 5 | Out-Null; return $true } catch { Start-Sleep -Milliseconds 700 }
    }
    return $false
}

function Avvia-Backend {
    if (Processo-Sulla-Porta 8000) { "Backend già acceso."; return }
    if (-not (Test-Path $python)) { "Manca backend\.venv: crealo come dice il README."; return }
    Start-Process -FilePath $python -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" `
        -WorkingDirectory (Join-Path $radice "backend") -WindowStyle Hidden
    if (Risponde "http://127.0.0.1:8000/" 30) { "Backend acceso su http://localhost:8000" } else { "Il backend non risponde: guarda backend\logs\pitwall.log" }
}

function Avvia-Frontend {
    if (Processo-Sulla-Porta 3000) { "Frontend già acceso."; return }
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm run dev" -WorkingDirectory (Join-Path $radice "frontend") -WindowStyle Hidden
    if (Risponde "http://localhost:3000/login" 90) { "Frontend acceso su http://localhost:3000" } else { "Il frontend non risponde ancora: riprova fra poco con 'stato'." }
}

switch ($Azione) {
    "avvia"   { Avvia-Backend; Avvia-Frontend }
    "ferma"   { Ferma 8000 "Backend"; Ferma 3000 "Frontend" }
    "riavvia" { Ferma 8000 "Backend"; Start-Sleep -Seconds 1; Avvia-Backend }
    "stato"   {
        if (Processo-Sulla-Porta 8000) { "Backend: acceso (porta 8000)" } else { "Backend: spento" }
        if (Processo-Sulla-Porta 3000) { "Frontend: acceso (porta 3000)" } else { "Frontend: spento" }
    }
}
