# If PowerShell execution policy blocks this script, run:
# powershell -ExecutionPolicy Bypass -File .\Start-BlogPublisher.ps1

$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
Set-Location -LiteralPath $repoRoot

conda run -n psblog python -m tools.blog_publisher --repo "$repoRoot" @args
exit $LASTEXITCODE