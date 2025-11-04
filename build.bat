@echo off
echo ================================================================
echo                    CalmWeb Build Script
echo ================================================================
echo.

echo [1/4] Installation des dependances...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERREUR: Installation des dependances echouee
    pause
    exit /b 1
)

echo.
echo [2/4] Nettoyage des anciens builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo.
echo [3/4] Construction de l'executable avec PyInstaller...
pyinstaller CalmWeb_Final.spec
if errorlevel 1 (
    echo ERREUR: Construction de l'executable echouee
    pause
    exit /b 1
)

echo.
echo [4/4] Verification de l'executable...
if exist "dist\CalmWeb.exe" (
    echo ✅ SUCCESS: Executable cree avec succes!
    echo.
    echo Fichier genere: dist\CalmWeb.exe
    for %%A in (dist\CalmWeb.exe) do echo Taille: %%~zA bytes
    echo.
    echo L'executable est pret pour l'installation.
    echo N'oubliez pas de l'executer en tant qu'administrateur.
) else (
    echo ❌ ERREUR: Executable non trouve
    pause
    exit /b 1
)

echo.
echo ================================================================
echo                     Build Complete!
echo ================================================================
pause