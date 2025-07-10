#!/usr/bin/env python3
"""
WSGI Entry Point pour ERP Fée Maison
Fichier utilisé par Gunicorn en production
"""

import os
from app import create_app

# Créer l'application Flask
app = create_app(os.getenv('FLASK_ENV') or 'production')

# Exposer l'application pour Gunicorn
# Gunicorn cherchera 'app' dans ce fichier
application = app

if __name__ == "__main__":
    # Pour les tests locaux
    app.run(host='0.0.0.0', port=8080) 