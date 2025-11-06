@echo off
:: Script de désinstallation complète de CalmWeb
:: Supprime tous les fichiers, tâches, règles firewall, entrées registre et remet les proxy par défaut

echo ========================================
echo    DÉSINSTALLATION COMPLÈTE CALMWEB
echo ========================================
echo.

:: Vérifier les privilèges administrateur
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Ce script nécessite les privilèges administrateur.
    echo Clic droit sur le fichier et sélectionnez "Exécuter en tant qu'administrateur"
    pause
    exit /b 1
)

echo [1/8] Arrêt des processus CalmWeb...
taskkill /F /IM CalmWeb.exe >nul 2>&1
taskkill /F /IM CalmWeb_Fr.exe >nul 2>&1
taskkill /F /IM CalmWeb_Installer.exe >nul 2>&1
taskkill /F /IM CalmWeb_Fr_Installer.exe >nul 2>&1
taskkill /F /IM calmweb.exe >nul 2>&1
echo    ✓ Processus arrêtés

echo.
echo [2/8] Suppression des entrées de démarrage automatique...
:: Supprimer l'entrée du registre (Applications de démarrage)
reg delete "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v "CalmWeb" /f >nul 2>&1
echo    ✓ Entrée registre supprimée

:: Supprimer la tâche planifiée
schtasks /Delete /tn "CalmWeb" /F >nul 2>&1
echo    ✓ Tâche planifiée supprimée

echo.
echo [3/8] Suppression des règles firewall...
netsh advfirewall firewall delete rule name="CalmWeb" >nul 2>&1
echo    ✓ Règles firewall supprimées

echo.
echo [4/8] Restauration des paramètres proxy par défaut...
:: Désactiver le proxy système
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f >nul 2>&1
:: Supprimer l'adresse du proxy
reg delete "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyServer /f >nul 2>&1
:: Supprimer les exceptions proxy
reg delete "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyOverride /f >nul 2>&1

:: Réinitialiser WinHTTP proxy
netsh winhttp reset proxy >nul 2>&1
echo    ✓ Paramètres proxy restaurés

echo.
echo [5/8] Suppression du répertoire d'installation...
:: Supprimer le répertoire Program Files
if exist "C:\Program Files\CalmWeb" (
    rmdir /s /q "C:\Program Files\CalmWeb" >nul 2>&1
    echo    ✓ Répertoire Program Files supprimé
) else (
    echo    ⚠ Répertoire Program Files introuvable
)

echo.
echo [6/8] Suppression complète des fichiers utilisateur...
:: Supprimer les fichiers de configuration dans AppData Roaming
if exist "%APPDATA%\CalmWeb" (
    rmdir /s /q "%APPDATA%\CalmWeb" >nul 2>&1
    echo    ✓ AppData\Roaming\CalmWeb supprimé
) else (
    echo    ⚠ AppData\Roaming\CalmWeb introuvable
)

:: Supprimer les fichiers dans AppData Local
if exist "%LOCALAPPDATA%\CalmWeb" (
    rmdir /s /q "%LOCALAPPDATA%\CalmWeb" >nul 2>&1
    echo    ✓ AppData\Local\CalmWeb supprimé
) else (
    echo    ⚠ AppData\Local\CalmWeb introuvable
)

:: Supprimer les éventuels fichiers dans ProgramData
if exist "%PROGRAMDATA%\CalmWeb" (
    rmdir /s /q "%PROGRAMDATA%\CalmWeb" >nul 2>&1
    echo    ✓ ProgramData\CalmWeb supprimé
) else (
    echo    ⚠ ProgramData\CalmWeb introuvable
)

:: Supprimer les éventuels logs dans Documents
if exist "%USERPROFILE%\Documents\CalmWeb*" (
    del /q "%USERPROFILE%\Documents\CalmWeb*" >nul 2>&1
    echo    ✓ Logs Documents supprimés
)

:: Supprimer les éventuels fichiers desktop
if exist "%USERPROFILE%\Desktop\CalmWeb*" (
    del /q "%USERPROFILE%\Desktop\CalmWeb*" >nul 2>&1
    echo    ✓ Fichiers Desktop supprimés
)

echo.
echo [7/8] Nettoyage approfondi des fichiers temporaires...
:: Supprimer les éventuels fichiers temporaires utilisateur
del /q "%TEMP%\CalmWeb*" >nul 2>&1
del /q "%TEMP%\calmweb*" >nul 2>&1
del /q "%TEMP%\*CalmWeb*" >nul 2>&1

:: Supprimer les fichiers temporaires système
del /q "C:\Windows\Temp\CalmWeb*" >nul 2>&1
del /q "C:\Windows\Temp\calmweb*" >nul 2>&1

:: Supprimer les éventuels fichiers de crash/dump
del /q "%LOCALAPPDATA%\CrashDumps\CalmWeb*" >nul 2>&1

:: Nettoyer le registre des traces résiduelles
reg delete "HKEY_CURRENT_USER\Software\CalmWeb" /f >nul 2>&1
reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\CalmWeb" /f >nul 2>&1
reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\CalmWeb" /f >nul 2>&1

echo    ✓ Nettoyage approfondi terminé

echo.
echo [8/8] Actualisation des paramètres réseau...
:: Forcer l'actualisation des paramètres Internet
RunDll32.exe InetCpl.cpl,ClearMyTracksByProcess 8 >nul 2>&1
:: Vider le cache DNS
ipconfig /flushdns >nul 2>&1
echo    ✓ Paramètres réseau actualisés

echo.
echo ========================================
echo    DÉSINSTALLATION TERMINÉE AVEC SUCCÈS
echo ========================================
echo.
echo Tous les composants de CalmWeb ont été supprimés :
echo  ✓ Processus arrêtés
echo  ✓ Démarrage automatique désactivé
echo  ✓ Règles firewall supprimées
echo  ✓ Proxy système restauré
echo  ✓ Fichiers d'installation supprimés
echo  ✓ Configuration utilisateur supprimée
echo  ✓ Fichiers temporaires nettoyés
echo  ✓ Paramètres réseau actualisés
echo.
echo Il est recommandé de redémarrer votre ordinateur
echo pour finaliser la désinstallation.
echo.
pause