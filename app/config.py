"""
Configuración de la aplicación
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración base"""
    
    # Configuración Supabase - USAR SERVICE KEY PARA EVITAR RLS
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')  # <--- CAMBIADO: usa SERVICE KEY
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    
    # Configuración Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-123456789')
    SESSION_TYPE = os.getenv('SESSION_TYPE', 'filesystem')
    SESSION_PERMANENT = os.getenv('SESSION_PERMANENT', False)
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', True)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_FILE_DIR = './flask_session'
    
    # Configuración JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-456789')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    
    # Configuración de seguridad
    BCRYPT_ROUNDS = 12
    CSRF_ENABLED = True
    CSRF_TIME_LIMIT = 3600
    
    # Configuración de paginación
    ITEMS_PER_PAGE = 12
    ADMIN_ITEMS_PER_PAGE = 20
    
    # Configuración de archivos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Configuración de email
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Configuración de cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300

class DevelopmentConfig(Config):
    """Configuración de desarrollo"""
    DEBUG = True
    ENV = 'development'
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    
    # Supabase para desarrollo - usar SERVICE KEY
    SUPABASE_URL = os.getenv('DEV_SUPABASE_URL', os.getenv('SUPABASE_URL'))
    SUPABASE_KEY = os.getenv('DEV_SUPABASE_SERVICE_KEY', os.getenv('SUPABASE_SERVICE_KEY'))

class ProductionConfig(Config):
    """Configuración de producción"""
    DEBUG = False
    ENV = 'production'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Configuración de logging
    LOG_LEVEL = 'INFO'
    
    # Configuración de seguridad adicional
    SSL_REDIRECT = True
    PERMANENT_SESSION_LIFETIME = 86400  # 24 horas

class TestingConfig(Config):
    """Configuración de pruebas"""
    TESTING = True
    DEBUG = True
    ENV = 'testing'
    SESSION_COOKIE_SECURE = False
    
    # Base de datos de pruebas
    SUPABASE_URL = os.getenv('TEST_SUPABASE_URL', os.getenv('SUPABASE_URL'))
    SUPABASE_KEY = os.getenv('TEST_SUPABASE_SERVICE_KEY', os.getenv('SUPABASE_SERVICE_KEY'))
    
    # Deshabilitar CSRF para pruebas
    CSRF_ENABLED = False
    WTF_CSRF_ENABLED = False

# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}