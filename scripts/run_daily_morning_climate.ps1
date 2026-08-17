$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$Python = $env:AI_INTEL_PYTHON
if (-not $Python) {
    $BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $BundledPython) {
        $Python = $BundledPython
    } else {
        $Python = "python"
    }
}

& $Python src\intel_mvp\cli.py daily-run --profile morning_climate --config config\daily_runs.json
exit $LASTEXITCODE
