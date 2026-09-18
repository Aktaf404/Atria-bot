@echo off
cd /d "%~dp0"

echo.
echo   9Router Auto-Add (Atria)  -  Made by Rofi Indistira
echo.
echo ============================================
echo  STEP 1: Google login + create Atria API key
echo  (new accounts go in akun.txt, format email:password)
echo ============================================
powershell -NoProfile -ExecutionPolicy Bypass -File run_step1.ps1
if errorlevel 1 (
  echo [ERROR] astra_glogin.py failed
  pause
  exit /b 1
)

echo.
echo ============================================
echo  STEP 2: Inject keys into 9Router + test all
echo ============================================
powershell -NoProfile -ExecutionPolicy Bypass -File run_step2.ps1
if errorlevel 1 (
  echo [ERROR] inject_9router.py failed
  pause
  exit /b 1
)

echo.
echo ===== DONE. Full log saved to run.log =====
pause