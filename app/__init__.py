"""
Inicialización de la aplicación Flask
"""
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
import logging
import os
import sys

from app.config import config
from app.utils.supabase_client import init_supabase
from app.utils.security import init_security

# Inicializar extensiones
login_manager = LoginManager()
csrf = CSRFProtect()
server_session = Session()

# ============================================
# USER_LOADER para Flask-Login
# ============================================
@login_manager.user_loader
def load_user(user_id):
    """Cargar usuario para Flask-Login"""
    from app.models.usuario import Usuario
    try:
        return Usuario.find_by_id(user_id)
    except Exception as e:
        logging.error(f'Error cargando usuario: {str(e)}')
        return None

def create_app(config_name='default'):
    """Crear y configurar la aplicación Flask"""
    app = Flask(__name__, 
                template_folder='views/templates',
                static_folder='views/static')
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # ===== CONFIGURACIÓN PARA VERCEL =====
    # Si está en producción o Vercel, deshabilitar sesiones basadas en archivos
    if config_name == 'production' or os.environ.get('VERCEL'):
        app.config['SESSION_TYPE'] = 'null'
        app.config['SESSION_PERMANENT'] = False
        app.config['SESSION_USE_SIGNER'] = True
        app.config['SESSION_FILE_DIR'] = None
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Inicializar extensiones
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder'
    login_manager.login_message_category = 'warning'
    
    csrf.init_app(app)
    server_session.init_app(app)
    
    # Inicializar Supabase
    init_supabase(app)
    
    # Inicializar seguridad
    init_security(app)
    
    # Configurar logging
    setup_logging(app)
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Registrar filtros de plantilla
    register_template_filters(app)
    
    return app

def setup_logging(app):
    """Configurar sistema de logging"""
    # Si está en Vercel, logs a stdout
    if os.environ.get('VERCEL') or app.config.get('ENV') == 'production':
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('🍎 Tienda Apple iniciada en modo producción (Vercel)')
    else:
        # Desarrollo local: logs a archivo
        if not app.debug:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            from logging.handlers import RotatingFileHandler
            handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            handler.setLevel(logging.INFO)
            app.logger.addHandler(handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('🍎 Tienda Apple iniciada en modo desarrollo')

def register_blueprints(app):
    """Registrar todos los blueprints"""
    from app.controllers.auth_controller import auth_bp
    from app.controllers.producto_controller import producto_bp
    from app.controllers.pedido_controller import pedido_bp
    from app.controllers.carrito_controller import carrito_bp
    from app.controllers.admin_controller import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(producto_bp, url_prefix='/productos')
    app.register_blueprint(pedido_bp, url_prefix='/pedidos')
    app.register_blueprint(carrito_bp, url_prefix='/carrito')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Ruta principal
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('producto.index'))

def register_template_filters(app):
    """Registrar filtros personalizados para Jinja2"""
    @app.template_filter('format_currency')
    def format_currency(value):
        try:
            return f'${float(value):,.2f}'
        except:
            return f'${value}'
    
    @app.template_filter('truncate_text')
    def truncate_text(text, length=100):
        if not text:
            return ''
        if len(text) <= length:
            return text
        return text[:length] + '...'
    
    @app.template_filter('estado_pedido_class')
    def estado_pedido_class(estado):
        clases = {
            'pendiente': 'warning',
            'confirmado': 'info',
            'procesando': 'primary',
            'enviado': 'info',
            'entregado': 'success',
            'cancelado': 'danger',
            'devuelto': 'secondary'
        }
        return clases.get(estado, 'secondary')