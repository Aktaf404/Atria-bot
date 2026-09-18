Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONWARNINGS = 'ignore'
python -u astra_glogin.py 2>&1 | Tee-Object -FilePath run.log
exit $LASTEXITCODE