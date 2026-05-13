# install.ps1 — bootstrap llmstxtgen into the local venv and verify it works.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $root "env_llmstxtgen"
$py   = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $py)) {
    Write-Host "Creating venv at $venv"
    python -m venv $venv
}

Write-Host "Installing llmstxtgen (editable) ..."
& $py -m pip install --upgrade pip | Out-Null
& $py -m pip install -e $root

Write-Host ""
Write-Host "Smoke test against antonioblago.de ..."
$env:PYTHONIOENCODING = "utf-8"
& $py -m llmstxtgen `
    --sitemap "https://antonioblago.de/sitemap_index.xml" `
    --platform wordpress `
    --out (Join-Path $root "smoke_antonioblago.txt") `
    --title "Antonio Blago" `
    --bucket-lang de `
    --json

Write-Host ""
Write-Host "Done. Try:"
Write-Host "  & $py -m llmstxtgen --sitemap https://www.x-bionic.com/sitemap.xml --platform shopify --out xbionic.txt --locales de --bucket-lang en"
