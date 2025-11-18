@echo off
REM 🖨️ Script d'installation de l'Agent d'Impression sur Windows (SmartPOS)
REM Exécuter en tant qu'Administrateur

echo ============================================
echo 🖨️ INSTALLATION AGENT D'IMPRESSION
echo ERP FEE MAISON - SmartPOS Windows
echo ============================================
echo.

REM Vérifier les privilèges administrateur
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Ce script doit être exécuté en tant qu'Administrateur
    echo 💡 Clic droit -^> Exécuter en tant qu'administrateur
    pause
    exit /b 1
)

REM Vérifier Python
echo 🔍 Vérification de Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Python n'est pas installé ou pas dans le PATH
    echo 💡 Téléchargez Python depuis https://www.python.org/downloads/
    echo 💡 IMPORTANT: Cochez "Add Python to PATH" lors de l'installation
    pause
    exit /b 1
)

python --version
echo ✅ Python détecté
echo.

REM Vérifier pip
echo 🔍 Vérification de pip...
pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ pip n'est pas disponible
    pause
    exit /b 1
)

echo ✅ pip détecté
echo.

REM Vérifier que nous sommes dans le bon répertoire
if not exist "app\services\printer_agent.py" (
    echo ❌ Ce script doit être exécuté depuis la racine du projet
    echo 💡 Naviguez vers le dossier du projet ERP
    pause
    exit /b 1
)

REM Créer l'environnement virtuel s'il n'existe pas
if not exist "venv" (
    echo 📦 Création de l'environnement virtuel...
    python -m venv venv
    if %errorLevel% neq 0 (
        echo ❌ Erreur lors de la création de l'environnement virtuel
        pause
        exit /b 1
    )
    echo ✅ Environnement virtuel créé
) else (
    echo ✅ Environnement virtuel existant détecté
)
echo.

REM Activer l'environnement virtuel
echo 🐍 Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
echo.

REM Installer les dépendances
echo 📦 Installation des dépendances...
pip install --upgrade pip
pip install flask requests pyusb
if %errorLevel% neq 0 (
    echo ❌ Erreur lors de l'installation des dépendances
    pause
    exit /b 1
)
echo ✅ Dépendances installées
echo.

REM Créer le fichier .env s'il n'existe pas
if not exist ".env" (
    echo ⚙️ Création du fichier .env...
    (
        echo # Configuration Agent d'Impression SmartPOS
        echo PRINTER_ENABLED=true
        echo PRINTER_VENDOR_ID=0471
        echo PRINTER_PRODUCT_ID=0055
        echo PRINTER_INTERFACE=0
        echo PRINTER_TIMEOUT=5000
        echo.
        echo # Agent HTTP
        echo PRINTER_AGENT_HOST=0.0.0.0
        echo PRINTER_AGENT_PORT=8080
        echo.
        echo # Token d'authentification - CHANGEZ-MOI !
        echo PRINTER_AGENT_TOKEN=default_token_change_me
        echo.
        echo PRINTER_LOG_LEVEL=INFO
    ) > .env
    echo ✅ Fichier .env créé
    echo.
    echo ⚠️  IMPORTANT: Modifiez PRINTER_AGENT_TOKEN dans .env avec un token sécurisé
    echo 💡 Utilisez: python -c "import secrets; print(secrets.token_urlsafe(32))"
    echo.
) else (
    echo ✅ Fichier .env existant détecté
)
echo.

REM Configurer le firewall Windows
echo 🔥 Configuration du firewall Windows...
netsh advfirewall firewall delete rule name="ERP Printer Agent" >nul 2>&1
netsh advfirewall firewall add rule name="ERP Printer Agent" dir=in action=allow protocol=TCP localport=8080
if %errorLevel% neq 0 (
    echo ⚠️  Erreur lors de la configuration du firewall
    echo 💡 Configurez manuellement le port 8080
) else (
    echo ✅ Port 8080 autorisé dans le firewall
)
echo.

REM Afficher l'adresse IP
echo 📍 Adresse IP du SmartPOS:
ipconfig | findstr /i "IPv4"
echo.

REM Test de détection imprimante
echo 🔍 Test de détection imprimante...
python -c "import usb.core; dev = usb.core.find(idVendor=0x0471, idProduct=0x0055); print('✅ Imprimante détectée' if dev else '⚠️ Imprimante non détectée')" 2>nul
echo.

echo ============================================
echo ✅ INSTALLATION TERMINÉE
echo ============================================
echo.
echo 📋 Prochaines étapes:
echo.
echo 1. Modifiez le fichier .env avec un token sécurisé
echo 2. Testez l'agent: python -m app.services.printer_agent --host 0.0.0.0 --port 8080 --token YOUR_TOKEN
echo 3. Configurez le VPS avec les mêmes paramètres
echo 4. (Optionnel) Créez un service Windows avec NSSM pour démarrage automatique
echo.
echo 💡 Consultez documentation/INSTALLATION_SMARTPOS_WINDOWS.md pour plus de détails
echo.
pause

