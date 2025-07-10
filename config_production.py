import os
from datetime import timedelta

class ProductionConfig:
    """Configuration de production pour l'ERP Fée Maison"""
    
    # Configuration Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'votre-clé-secrète-super-forte-2025'
    DEBUG = False
    TESTING = False
    
    # Configuration base de données PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://erp_user:erp_password_2025@localhost/fee_maison_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }
    
    # Configuration Redis (optionnel)
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Configuration session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True  # HTTPS uniquement
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configuration upload fichiers
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max
    UPLOAD_FOLDER = '/opt/erp/app/uploads'
    
    # Configuration mail (optionnel)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Configuration logs
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Configuration ZKTeco (à adapter selon votre pointeuse)
    ZKTECO_IP = os.environ.get('ZKTECO_IP', '192.168.1.100')
    ZKTECO_PORT = int(os.environ.get('ZKTECO_PORT', 4370))
    
    # Configuration sécurité
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 heure
    
    # Configuration cache
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300 