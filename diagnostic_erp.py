#!/usr/bin/env python3
"""
Script de Diagnostic ERP Fée Maison
Teste tous les composants critiques avant le déploiement
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_success(msg):
    print(f"✅ {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def print_warning(msg):
    print(f"⚠️  {msg}")

def print_info(msg):
    print(f"ℹ️  {msg}")

def test_python_version():
    """Test de la version Python"""
    print_header("VERSION PYTHON")
    version = sys.version_info
    print_info(f"Version Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print_success("Version Python compatible")
        return True
    else:
        print_error("Version Python trop ancienne (minimum 3.8)")
        return False

def test_dependencies():
    """Test des dépendances Python"""
    print_header("DÉPENDANCES PYTHON")
    
    required_packages = [
        'flask', 'sqlalchemy', 'flask_sqlalchemy', 'flask_migrate',
        'flask_login', 'flask_wtf', 'psycopg2', 'gunicorn'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print_success(f"{package} installé")
        except ImportError:
            print_error(f"{package} manquant")
            missing_packages.append(package)
    
    if missing_packages:
        print_warning(f"Packages manquants: {', '.join(missing_packages)}")
        return False
    else:
        print_success("Toutes les dépendances sont installées")
        return True

def test_environment_variables():
    """Test des variables d'environnement"""
    print_header("VARIABLES D'ENVIRONNEMENT")
    
    required_vars = [
        'FLASK_ENV', 'SECRET_KEY', 'POSTGRES_USER', 'POSTGRES_PASSWORD',
        'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB_NAME'
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            if 'PASSWORD' in var:
                print_success(f"{var}: {'*' * len(value)}")
            else:
                print_success(f"{var}: {value}")
        else:
            print_error(f"{var}: non définie")
            missing_vars.append(var)
    
    if missing_vars:
        print_warning(f"Variables manquantes: {', '.join(missing_vars)}")
        return False
    else:
        print_success("Toutes les variables d'environnement sont définies")
        return True

def test_database_connection():
    """Test de connexion à la base de données"""
    print_header("CONNEXION BASE DE DONNÉES")
    
    try:
        from app import create_app
        from extensions import db
        
        app = create_app('production')
        
        with app.app_context():
            # Test de connexion avec la nouvelle syntaxe SQLAlchemy
            with db.engine.connect() as connection:
                result = connection.execute(db.text("SELECT 1"))
                result.fetchone()
            print_success("Connexion à la base de données réussie")
            
            # Test des tables
            from models import User
            user_count = User.query.count()
            print_success(f"Table User accessible ({user_count} utilisateurs)")
            
            return True
            
    except Exception as e:
        print_error(f"Erreur de connexion à la base: {e}")
        return False

def test_flask_app():
    """Test de l'application Flask"""
    print_header("APPLICATION FLASK")
    
    try:
        from app import create_app
        
        app = create_app('production')
        
        # Test des blueprints
        blueprints = list(app.blueprints.keys())
        print_success(f"Blueprints chargés: {', '.join(blueprints)}")
        
        # Test des routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(rule.endpoint)
        
        print_success(f"Nombre de routes: {len(routes)}")
        
        # Test des templates
        template_count = len(app.jinja_env.list_templates())
        print_success(f"Nombre de templates: {template_count}")
        
        return True
        
    except Exception as e:
        print_error(f"Erreur application Flask: {e}")
        return False

def test_wsgi():
    """Test du fichier WSGI"""
    print_header("FICHIER WSGI")
    
    try:
        from wsgi import app
        
        print_success("Fichier wsgi.py chargé avec succès")
        print_success(f"Type d'application: {type(app).__name__}")
        
        # Test de création de contexte
        with app.app_context():
            print_success("Contexte d'application créé")
        
        return True
        
    except Exception as e:
        print_error(f"Erreur fichier WSGI: {e}")
        return False

def test_gunicorn():
    """Test de Gunicorn"""
    print_header("GUNICORN")
    
    try:
        result = subprocess.run(['gunicorn', '--version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print_success(f"Gunicorn installé: {version}")
            return True
        else:
            print_error("Gunicorn non installé ou erreur")
            return False
            
    except FileNotFoundError:
        print_error("Gunicorn non trouvé")
        return False
    except Exception as e:
        print_error(f"Erreur test Gunicorn: {e}")
        return False

def test_file_structure():
    """Test de la structure des fichiers"""
    print_header("STRUCTURE DES FICHIERS")
    
    required_files = [
        'wsgi.py', 'app/__init__.py', 'config.py', 'requirements.txt',
        'models.py', 'extensions.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"{file_path} existe")
        else:
            print_error(f"{file_path} manquant")
            missing_files.append(file_path)
    
    if missing_files:
        print_warning(f"Fichiers manquants: {', '.join(missing_files)}")
        return False
    else:
        print_success("Structure des fichiers correcte")
        return True

def test_permissions():
    """Test des permissions"""
    print_header("PERMISSIONS")
    
    try:
        # Test d'écriture dans le répertoire courant
        test_file = Path('test_permissions.tmp')
        test_file.write_text('test')
        test_file.unlink()
        print_success("Permissions d'écriture OK")
        
        return True
        
    except Exception as e:
        print_error(f"Erreur permissions: {e}")
        return False

def main():
    """Fonction principale de diagnostic"""
    print_header("DIAGNOSTIC ERP FÉE MAISON")
    
    tests = [
        ("Version Python", test_python_version),
        ("Structure des fichiers", test_file_structure),
        ("Dépendances Python", test_dependencies),
        ("Variables d'environnement", test_environment_variables),
        ("Permissions", test_permissions),
        ("Application Flask", test_flask_app),
        ("Fichier WSGI", test_wsgi),
        ("Gunicorn", test_gunicorn),
        ("Connexion base de données", test_database_connection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Erreur lors du test {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé final
    print_header("RÉSUMÉ DU DIAGNOSTIC")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print_info(f"Tests réussis: {passed}/{total}")
    
    if passed == total:
        print_success("🎉 Tous les tests sont passés ! L'ERP est prêt pour le déploiement.")
    else:
        print_warning("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        
        failed_tests = [name for name, result in results if not result]
        print_warning(f"Tests échoués: {', '.join(failed_tests)}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 