[CmdletBinding()]
param(
    [ValidateSet('Skill', 'Web')]
    [string]$Mode = 'Skill'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw 'Install uv first: winget install --id astral-sh.uv -e; then reopen PowerShell.'
}
if ($Mode -eq 'Web' -and -not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw 'The legacy web app requires Ollama. Skill mode does not.'
}

Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    & uv sync --locked --python 3.12 --extra dev --extra skill
    if ($LASTEXITCODE -ne 0) { throw 'uv sync failed.' }

    # Keep the translator and its compatibility dependency aligned with setup.sh.
    & uv tool install --force --python 3.12 --with 'tencentcloud-sdk-python-tmt==3.0.1257' 'pdf2zh==1.9.11'
    if ($LASTEXITCODE -ne 0) { throw 'pdf2zh installation failed.' }

    if ($Mode -eq 'Web') {
        Write-Host 'Setup complete. Start Ollama with your model, then run scripts/run.ps1.'
    } else {
        Write-Host 'Setup complete. Open this folder in Codex and use the bundled readable-pdf-translation skill.'
    }
} finally {
    Pop-Location
}
