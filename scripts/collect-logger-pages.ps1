param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^(?:\d{1,3}\.){3}\d{1,3}$')]
    [string]$LoggerIP
)

$ErrorActionPreference = 'Stop'
$baseUrl = "http://$LoggerIP"
$outDir = Join-Path (Split-Path -Parent $PSScriptRoot) "logger_research"
New-Item -Path $outDir -ItemType Directory -Force | Out-Null

# Only retrieve static pages/assets. Avoid authenticated or configuration CGI calls.
$resources = @(
    'index.html',
    'status.html',
    'js/index.js',
    'js/status.js',
    'js/utils.js'
)

foreach ($resource in $resources) {
    $target = Join-Path $outDir ($resource -replace '/', '\')
    New-Item -Path (Split-Path -Parent $target) -ItemType Directory -Force | Out-Null

    $url = "$baseUrl/$resource"
    Write-Host "GET $url"
    & curl.exe --fail --silent --show-error --max-time 8 $url --output $target

    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Could not download $resource (exit code $LASTEXITCODE)."
        Remove-Item -LiteralPath $target -ErrorAction SilentlyContinue
        continue
    }

    Write-Host "Saved: $target"
}

Write-Host ""
Write-Host "Collection complete. Review and redact before sharing."
Write-Host "The logger_research folder is ignored by Git by default."
