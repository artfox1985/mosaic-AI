# Nachtlauf 2026-08-20: Elo-Neuverankerung + Asym-Korpus.
# Registrierung: PREREG_round5_minfix_elo_reset.md par.3 (Leiter-Kanten)
# und PREREG_asymmetric_curriculum.md par.11 (Korpus-Bloecke, Fruehwarn-Gate).
# Aufruf aus beliebigem Verzeichnis:  pwsh -File tools\night_run_20260820.ps1
# (oder in einer offenen PowerShell:  .\tools\night_run_20260820.ps1)
# Das Fenster offen lassen; Log: logs\nacht_20260820.log

$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)
New-Item -ItemType Directory -Force -Path "data\asym_corpus" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
$log = "logs\nacht_20260820.log"

function Lauf {
    param([string]$Titel, [string[]]$PyArgs)
    "### $Titel  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Tee-Object -FilePath $log -Append
    & python -u -X utf8 @PyArgs 2>&1 | Tee-Object -FilePath $log -Append
    if ($LASTEXITCODE -ne 0) {
        "### ABBRUCH bei '$Titel' (exit $LASTEXITCODE)  $(Get-Date -Format 'HH:mm:ss')" | Tee-Object -FilePath $log -Append
        exit 1
    }
}

# ── Teil 1: Elo-Neuverankerung (5 Kanten, Fix-Engine) ──────────────────────
$arena = "tools\paired_arena_env_ab.py"
$tot   = @("--env-name", "MOSAIC_OWNERSHIP_W", "--arms", "0", "--control", "0", "--block-size", "25")

Lauf "Anker v21"  (@($arena) + $tot + @("--model", "models\alphazero_v21_2d_brierbest.onnx",  "--n-games", "150", "--seed", "20260834", "--out-prefix", "elo_r5fix_v21_anchor"))
Lauf "Anker v20"  (@($arena) + $tot + @("--model", "models\alphazero_v20_2d_opp_brierbest.onnx", "--n-games", "150", "--seed", "20260834", "--out-prefix", "elo_r5fix_v20_anchor"))
Lauf "Anker v19"  (@($arena) + $tot + @("--model", "models\alphazero_v19_2d_best.onnx",        "--n-games", "150", "--seed", "20260834", "--out-prefix", "elo_r5fix_v19_anchor"))
Lauf "Kante v21-v20" (@($arena) + $tot + @("--model", "models\alphazero_v21_2d_brierbest.onnx", "--model-b", "models\alphazero_v20_2d_opp_brierbest.onnx", "--sims-b", "400", "--net-sims", "400", "--n-games", "400", "--seed", "20260835", "--out-prefix", "elo_r5fix_v21_v20"))
Lauf "Kante v20-v19" (@($arena) + $tot + @("--model", "models\alphazero_v20_2d_opp_brierbest.onnx", "--model-b", "models\alphazero_v19_2d_best.onnx", "--sims-b", "400", "--net-sims", "400", "--n-games", "400", "--seed", "20260836", "--out-prefix", "elo_r5fix_v20_v19"))

# ── Teil 2: Asym-Korpus (4 Bloecke a 4.000, Fruehwarn-Gate nach S1) ────────
$env:MOSAIC_DATA_DIR = "data\asym_corpus"
$sp = @("self_play.py", "--mode", "network", "--model", "v21_2d_brierbest", "--games", "4000", "--sims", "200", "--threads", "8")

$env:MOSAIC_ASYM_VORZUG = "1"; $env:MOSAIC_PLATTENBAU = "1"
Lauf "Asym S1" ($sp + @("--version", "v21_asymS", "--seed", "20260830"))
Lauf "Fruehwarn-Gate S1" @("tools\probes\asym_early_rate_check.py", "--korpus", "data/asym_corpus/selfplay_v21_asymS_*.pkl", "--log", $log, "--abbruch-pp", "10")
Lauf "Asym S2" ($sp + @("--version", "v21_asymS", "--seed", "20260831"))

Remove-Item Env:MOSAIC_ASYM_VORZUG; Remove-Item Env:MOSAIC_PLATTENBAU
Lauf "Asym N1" ($sp + @("--version", "v21_asymN", "--seed", "20260832"))
Lauf "Asym N2" ($sp + @("--version", "v21_asymN", "--seed", "20260833"))

"### ALLES FERTIG  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Tee-Object -FilePath $log -Append
