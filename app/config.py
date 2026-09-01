"""
Configuración de la aplicación
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración base"""
    
    # Supabase - usar SERVICE KEY para evitar RLS
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')  # Usamos SERVICE KEY
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    
    # Flask - SECRET_KEY es OBLIGATORIA en producción
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    
    # Configuración de sesión (para Vercel usamos 'null')
    SESSION_TYPE = 'null'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_FILE_DIR = None
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # JWT
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    
    # Seguridad
    BCRYPT_ROUNDS = 12
    CSRF_ENABLED = True
    CSRF_TIME_LIMIT = 3600
    
    # Paginación
    ITEMS_PER_PAGE = 12
    ADMIN_ITEMS_PER_PAGE = 20
    
    # Archivos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Email
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')


class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'
    SESSION_COOKIE_SECURE = False
    
    # En desarrollo, podemos usar claves por defecto si no están en .env
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-123456789')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-dev-secret-456789')
    
    SUPABASE_URL = os.getenv('DEV_SUPABASE_URL', os.getenv('SUPABASE_URL'))
    SUPABASE_KEY = os.getenv('DEV_SUPABASE_SERVICE_KEY', os.getenv('SUPABASE_SERVICE_KEY'))
    
    SESSION_TYPE = 'filesystem'


class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'
    SESSION_COOKIE_SECURE = True
    
    # En producción, forzamos que las claves existan
    @classmethod
    def init_app(cls, app):
        if not app.config.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY no está configurada en producción")
        if not app.config.get('JWT_SECRET_KEY'):
            raise ValueError("JWT_SECRET_KEY no está configurada en producción")
        if not app.config.get('SUPABASE_URL'):
            raise ValueError("SUPABASE_URL no está configurada en producción")
        if not app.config.get('SUPABASE_SERVICE_KEY'):
            raise ValueError("SUPABASE_SERVICE_KEY no está configurada en producción")
    
    # Configuración adicional
    LOG_LEVEL = 'INFO'
    SSL_REDIRECT = True
    PERMANENT_SESSION_LIFETIME = 86400  # 24 horas


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    ENV = 'testing'
    SESSION_COOKIE_SECURE = False
    CSRF_ENABLED = False
    WTF_CSRF_ENABLED = False
    
    SECRET_KEY = 'test-secret-key'
    JWT_SECRET_KEY = 'test-jwt-secret'
    
    SUPABASE_URL = os.getenv('TEST_SUPABASE_URL', os.getenv('SUPABASE_URL'))
    SUPABASE_KEY = os.getenv('TEST_SUPABASE_SERVICE_KEY', os.getenv('SUPABASE_SERVICE_KEY'))


# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}