#!/usr/bin/env python3
"""
Configuration pour les scripts de mise à jour de la documentation ERP Fée Maison
"""

# Configuration des chemins
PATHS = {
    'project_root': '.',
    'app_dir': 'app',
    'docs_dir': 'documentation',
    'backup_dir': 'documentation_backup'
}

# Configuration des fichiers à mettre à jour
FILES_TO_UPDATE = {
    'architecture': 'ARCHITECTURE_TECHNIQUE.md',
    'questions': 'QUESTIONS_TEST_IA.md',
    'corrections': 'CORRECTIONS_DOCUMENTATION.md'
}

# Configuration des sections à mettre à jour
SECTIONS = {
    'blueprints': {
        'start_marker': '### **Blueprints Enregistrés (RÉEL)**',
        'end_marker': '### **URLs Réelles par Module**'
    },
    'urls': {
        'start_marker': '### **URLs Réelles par Module**',
        'end_marker': '### **'
    }
}

# Configuration des icônes pour les modules
MODULE_ICONS = {
    'main': '🏠',
    'auth': '🔐',
    'products': '📦',
    'orders': '📋',
    'recipes': '🏭',
    'stock': '📦',
    'purchases': '🛒',
    'employees': '👥',
    'deliverymen': '🚚',
    'sales': '💰',
    'dashboards': '📊',
    'accounting': '🧮',
    'zkteco': '⏰',
    'admin': '⚙️'
}

# Configuration des patterns regex
PATTERNS = {
    'blueprint_definition': r'(\w+)\s*=\s*Blueprint\([\'"]([^\'"]+)[\'"][^)]*\)',
    'blueprint_registration': r'app\.register_blueprint\((\w+_blueprint)(?:,\s*url_prefix=[\'"]([^\'"]+)[\'"])?\)',
    'route_decorator': r'@(\w+)\.route\([\'"]([^\'"]+)[\'"][^)]*\)',
    'import_blueprint': r'from\s+([^.]+\.[^.]+\.[^.]*)\s+import\s+(\w+)\s+as\s+(\w+)_blueprint'
}

# Configuration des exclusions
EXCLUSIONS = {
    'files': [
        '__pycache__',
        '.git',
        'venv',
        'node_modules',
        '*.pyc',
        '*.pyo'
    ],
    'routes': [
        '/static/',
        '/favicon.ico',
        '/robots.txt'
    ]
}

# Configuration des limites
LIMITS = {
    'routes_per_module': 8,
    'backup_files': 5,
    'report_files': 10
}

# Configuration des messages
MESSAGES = {
    'start': '🚀 Début de la mise à jour des URLs...',
    'success': '✅ Mise à jour terminée !',
    'error': '❌ Erreur lors de la mise à jour',
    'backup_created': '✅ Sauvegarde créée : {backup_name}',
    'file_updated': '✅ {file} mis à jour (backup: {backup})',
    'report_generated': '✅ Rapport généré : {report_name}'
}

# Configuration des rapports
REPORT_CONFIG = {
    'include_timestamp': True,
    'include_summary': True,
    'include_details': True,
    'max_routes_display': 5
}

# Configuration de validation
VALIDATION = {
    'check_file_exists': True,
    'check_backup_created': True,
    'check_content_changed': True,
    'min_routes_expected': 50,
    'min_blueprints_expected': 5
}

# Configuration des tests IA
IA_TEST_CONFIG = {
    'questions_to_update': [
        'Quel est l\'URL pour créer une nouvelle commande ?',
        'Quel est le préfixe pour les dashboards ?',
        'Comment accéder au dashboard des ventes ?'
    ],
    'expected_improvement': 10  # Points d'amélioration attendus
}

# Configuration de sécurité
SECURITY = {
    'create_backup': True,
    'restore_on_error': True,
    'max_backup_size_mb': 100,
    'backup_retention_days': 30
}

# Configuration de performance
PERFORMANCE = {
    'parallel_processing': False,
    'max_file_size_mb': 10,
    'timeout_seconds': 30,
    'memory_limit_mb': 512
}

# Configuration des logs
LOGGING = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'file': 'docs_update.log',
    'max_size_mb': 10,
    'backup_count': 5
}

# Configuration des notifications
NOTIFICATIONS = {
    'email_on_error': False,
    'email_on_success': False,
    'slack_webhook': None,
    'discord_webhook': None
}

# Configuration de l'intégration CI/CD
CI_CD = {
    'auto_commit': False,
    'commit_message': 'docs: mise à jour automatique URLs et endpoints',
    'branch': 'main',
    'push_changes': False
}

# Configuration des métriques
METRICS = {
    'track_execution_time': True,
    'track_file_changes': True,
    'track_route_count': True,
    'generate_metrics_report': True
}

# Configuration des exports
EXPORTS = {
    'json_report': True,
    'csv_report': False,
    'html_report': False,
    'pdf_report': False
}

# Configuration des plugins (pour extensions futures)
PLUGINS = {
    'enabled': [],
    'config': {},
    'custom_validators': [],
    'custom_generators': []
}

# Configuration de l'environnement
ENVIRONMENT = {
    'development': {
        'debug': True,
        'verbose': True,
        'dry_run': False
    },
    'production': {
        'debug': False,
        'verbose': False,
        'dry_run': False
    },
    'testing': {
        'debug': True,
        'verbose': True,
        'dry_run': True
    }
}

# Configuration par défaut
DEFAULT_CONFIG = {
    'environment': 'development',
    'create_backup': True,
    'update_architecture': True,
    'update_questions': True,
    'generate_report': True,
    'validate_results': True
}

def get_config(environment='development'):
    """Retourne la configuration pour un environnement donné"""
    config = DEFAULT_CONFIG.copy()
    config.update(ENVIRONMENT.get(environment, {}))
    return config

def validate_config():
    """Valide la configuration"""
    errors = []
    
    # Vérifier les chemins
    for key, path in PATHS.items():
        if not path:
            errors.append(f"Chemin manquant pour {key}")
    
    # Vérifier les patterns regex
    import re
    for key, pattern in PATTERNS.items():
        try:
            re.compile(pattern)
        except re.error as e:
            errors.append(f"Pattern regex invalide pour {key}: {e}")
    
    # Vérifier les limites
    for key, limit in LIMITS.items():
        if limit < 0:
            errors.append(f"Limite négative pour {key}: {limit}")
    
    if errors:
        raise ValueError(f"Configuration invalide:\n" + "\n".join(errors))
    
    return True

if __name__ == "__main__":
    # Test de validation
    try:
        validate_config()
        print("✅ Configuration valide")
    except ValueError as e:
        print(f"❌ {e}") 