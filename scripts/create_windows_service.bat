@echo off
REM 🖨️ Script de création du Service Windows pour l'Agent d'Impression
REM Nécessite NSSM (Non-Sucking Service Manager)
REM Télécharger depuis: https://nssm.cc/download

echo ============================================
echo 🖨️ CRÉATION SERVICE WINDOWS
echo Agent d'Impression ERP Fée Maison
echo ============================================
echo.

REM Vérifier les privilèges administrateur
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Ce script doit être exécuté en tant qu'Administrateur
    pause
    exit /b 1
)

REM Vérifier NSSM
set NSSM_PATH=
if exist "C:\nssm\win64\nssm.exe" (
    set NSSM_PATH=C:\nssm\win64\nssm.exe
) else if exist "C:\Program Files\nssm\nssm.exe" (
    set NSSM_PATH=C:\Program Files\nssm\nssm.exe
) else (
    echo ❌ NSSM non trouvé
    echo.
    echo 💡 Téléchargez NSSM depuis https://nssm.cc/download
    echo 💡 Extrayez dans C:\nssm\ ou installez-le
    echo.
    pause
    exit /b 1
)

echo ✅ NSSM trouvé: %NSSM_PATH%
echo.

REM Vérifier le répertoire du projet
if not exist "app\services\printer_agent.py" (
    echo ❌ Ce script doit être exécuté depuis la racine du projet
    pause
    exit /b 1
)

set PROJECT_DIR=%~dp0
set PROJECT_DIR=%PROJECT_DIR:~0,-1%

REM Lire le token depuis .env
set TOKEN=default_token_change_me
if exist ".env" (
    for /f "tokens=2 delims==" %%a in ('findstr "PRINTER_AGENT_TOKEN" .env') do set TOKEN=%%a
)

echo 📋 Configuration:
echo    Projet: %PROJECT_DIR%
echo    Python: %PROJECT_DIR%\venv\Scripts\python.exe
echo    Token: %TOKEN%
echo.

REM Arrêter le service s'il existe déjà
echo 🔄 Arrêt du service existant (si présent)...
"%NSSM_PATH%" stop PrinterAgent >nul 2>&1
"%NSSM_PATH%" remove PrinterAgent confirm >nul 2>&1
echo.

REM Créer le service
echo 📦 Création du service...
"%NSSM_PATH%" install PrinterAgent "%PROJECT_DIR%\venv\Scripts\python.exe" "-m app.services.printer_agent --host 0.0.0.0 --port 8080 --token %TOKEN%"

if %errorLevel% neq 0 (
    echo ❌ Erreur lors de la création du service
    pause
    exit /b 1
)

REM Configurer le répertoire de travail
"%NSSM_PATH%" set PrinterAgent AppDirectory "%PROJECT_DIR%"

REM Configurer le démarrage automatique
"%NSSM_PATH%" set PrinterAgent Start SERVICE_AUTO_START

REM Configurer la description
"%NSSM_PATH%" set PrinterAgent Description "Agent d'impression ERP Fée Maison - Gère l'imprimante et le tiroir-caisse"

REM Configurer les logs
"%NSSM_PATH%" set PrinterAgent AppStdout "%PROJECT_DIR%\logs\printer-agent.log"
"%NSSM_PATH%" set PrinterAgent AppStderr "%PROJECT_DIR%\logs\printer-agent-error.log"

REM Créer le dossier logs s'il n'existe pas
if not exist "logs" mkdir logs

echo ✅ Service créé
echo.

REM Démarrer le service
echo 🚀 Démarrage du service...
"%NSSM_PATH%" start PrinterAgent

if %errorLevel% neq 0 (
    echo ❌ Erreur lors du démarrage du service
    pause
    exit /b 1
)

echo ✅ Service démarré
echo.

REM Vérifier le statut
echo 📊 Statut du service:
"%NSSM_PATH%" status PrinterAgent
echo.

echo ============================================
echo ✅ SERVICE CRÉÉ ET DÉMARRÉ
echo ============================================
echo.
echo 📋 Commandes utiles:
echo    Démarrer: nssm start PrinterAgent
echo    Arrêter: nssm stop PrinterAgent
echo    Redémarrer: nssm restart PrinterAgent
echo    Statut: nssm status PrinterAgent
echo    Supprimer: nssm remove PrinterAgent confirm
echo.
echo 📝 Logs:
echo    %PROJECT_DIR%\logs\printer-agent.log
echo    %PROJECT_DIR%\logs\printer-agent-error.log
echo.
pause

