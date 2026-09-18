Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONWARNINGS = 'ignore'
python -u inject_9router.py 2>&1 | Tee-Object -FilePath run.log -Append
exit $LASTEXITCODE