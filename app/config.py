"""
Configuración de la aplicación
"""
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración base"""
    
    # Supabase - usar SERVICE KEY para evitar RLS
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')  # Usamos SERVICE KEY
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    
    # Flask - SECRET_KEY con fallback seguro
    # Si no está en variables de entorno, genera una clave aleatoria (solo para que arranque)
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        # En producción, esto debería estar configurado, pero como fallback generamos una
        SECRET_KEY = secrets.token_urlsafe(32)
        print(f"⚠️ SECRET_KEY no configurada en variables de entorno. Usando clave generada automáticamente.")
        print(f"   Esta clave es temporal. Para producción, configura SECRET_KEY en Vercel.")
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        JWT_SECRET_KEY = secrets.token_urlsafe(32)
        print(f"⚠️ JWT_SECRET_KEY no configurada. Usando clave generada automáticamente.")
    
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
    SESSION_TYPE = 'filesystem'
    
    # En desarrollo, podemos usar valores por defecto
    SUPABASE_URL = os.getenv('DEV_SUPABASE_URL', os.getenv('SUPABASE_URL'))
    SUPABASE_KEY = os.getenv('DEV_SUPABASE_SERVICE_KEY', os.getenv('SUPABASE_SERVICE_KEY'))


class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'
    SESSION_COOKIE_SECURE = True
    
    # En producción, forzamos que las claves existan, pero con fallback seguro
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        # Si no está, generamos una y lanzamos warning
        import secrets
        SECRET_KEY = secrets.token_urlsafe(32)
        import sys
        print("⚠️ ADVERTENCIA: SECRET_KEY no configurada en variables de entorno.", file=sys.stderr)
        print("   Usando clave generada automáticamente. Para producción, configura SECRET_KEY en Vercel.", file=sys.stderr)
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        import secrets
        JWT_SECRET_KEY = secrets.token_urlsafe(32)
        import sys
        print("⚠️ ADVERTENCIA: JWT_SECRET_KEY no configurada. Usando clave generada automáticamente.", file=sys.stderr)
    
    @classmethod
    def init_app(cls, app):
        """Validar configuración crítica al arrancar"""
        # Verificar Supabase
        if not app.config.get('SUPABASE_URL'):
            raise ValueError("SUPABASE_URL no está configurada en producción")
        if not app.config.get('SUPABASE_SERVICE_KEY'):
            raise ValueError("SUPABASE_SERVICE_KEY no está configurada en producción")
        
        # Verificar SECRET_KEY (si es generada automáticamente, solo advertimos)
        if app.config.get('SECRET_KEY') and 'token_urlsafe' in str(app.config['SECRET_KEY']):
            # Es generada automáticamente, no hay problema para arrancar, pero advertimos
            app.logger.warning("SECRET_KEY generada automáticamente. Configura una fija en producción.")
        else:
            app.logger.info("SECRET_KEY configurada correctamente.")


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