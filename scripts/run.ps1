$ErrorActionPreference = 'Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    & uv run --locked --python 3.12 local-readable
    if ($LASTEXITCODE -ne 0) { throw 'Local Readable stopped with an error.' }
} finally {
    Pop-Location
}
