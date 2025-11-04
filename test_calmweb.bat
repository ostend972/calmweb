@echo off
echo ================================================================
echo                   CalmWeb Test Script
echo ================================================================
echo.

echo Test de l'executable CalmWeb...
echo.

if not exist "dist\CalmWeb.exe" (
    echo ❌ ERREUR: Executable non trouve!
    echo Veuillez d'abord executer build.bat
    pause
    exit /b 1
)

echo ✅ Executable trouve: dist\CalmWeb.exe
for %%A in (dist\CalmWeb.exe) do echo Taille: %%~zA bytes
echo.

echo [TEST 1] Verification des dependances...
echo Demarrage de CalmWeb en mode test (5 secondes)...
echo.

echo IMPORTANT: Ce test va demarrer CalmWeb.
echo - Une icone apparaitra dans la barre des taches
echo - Ouvrez http://127.0.0.1:8081 pour tester le dashboard
echo - Fermez l'application via l'icone systray (clic droit > Quit)
echo.
echo Appuyez sur une touche pour demarrer le test...
pause >nul

echo Demarrage de CalmWeb.exe...
start "" "dist\CalmWeb.exe"

echo.
echo Test en cours...
echo - Verifiez que l'icone systray apparait
echo - Testez le dashboard sur http://127.0.0.1:8081
echo - Testez les fonctionnalites (toggle protection, logs, etc.)
echo.
echo Fermez l'application via l'icone systray quand le test est termine.
echo.
pause