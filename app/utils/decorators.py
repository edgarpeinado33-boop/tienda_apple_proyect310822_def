"""
Decoradores personalizados para la aplicación
"""
from functools import wraps
from flask import jsonify, request, abort, flash, redirect, url_for, session, current_app
from flask_login import current_user, login_required
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ============================================
# DECORADORES DE AUTENTICACIÓN
# ============================================

def login_required_api(f):
    """
    Decorador para API que requiere autenticación
    Retorna JSON en lugar de redirigir
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Autenticación requerida'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorador para rutas que solo admins pueden acceder
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para acceder', 'warning')
            return redirect(url_for('auth.login'))
        
        if not (current_user.has_role('SUPER_ADMIN') or 
                current_user.has_role('ADMIN_TIENDA')):
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def require_roles(*roles):
    """
    Decorador para verificar roles específicos.
    Permite acceso si el usuario es administrador (is_admin=True)
    o si su email es el del administrador principal.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Por favor inicia sesión para acceder', 'warning')
                return redirect(url_for('auth.login'))
            
            # Verificar si el usuario es el administrador principal por email
            if hasattr(current_user, 'email') and current_user.email == 'admin@tiendaapple.com':
                return f(*args, **kwargs)
            
            # Verificar si el usuario tiene la propiedad is_admin = True
            if hasattr(current_user, 'is_admin') and current_user.is_admin:
                return f(*args, **kwargs)
            
            # Verificar roles específicos
            user_roles = current_user.get_roles()
            if not any(role in user_roles for role in roles):
                # Log para depuración
                logger.warning(f'Acceso denegado a {current_user.email} - Roles: {user_roles} - Requeridos: {roles}')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def roles_required(*roles):
    """
    Decorador para verificar roles específicos (alias de require_roles)
    """
    return require_roles(*roles)

def permission_required(permission):
    """
    Decorador para verificar permisos específicos
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Por favor inicia sesión para acceder', 'warning')
                return redirect(url_for('auth.login'))
            
            # Verificar permiso
            if not current_user.has_permission(permission):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================
# DECORADORES DE RATE LIMITING
# ============================================

def rate_limit_api(max_attempts: int = 60, window: int = 60):
    """
    Rate limiting para APIs
    max_attempts: número máximo de intentos en la ventana
    window: ventana de tiempo en segundos
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Crear clave única para el rate limit
            key = f"{request.endpoint}:{request.remote_addr}"
            
            # Inicializar sesión de rate limit
            if 'rate_limit_api' not in session:
                session['rate_limit_api'] = {}
            
            now = datetime.utcnow().timestamp()
            
            # Verificar límite
            if key in session['rate_limit_api']:
                attempts, first_attempt = session['rate_limit_api'][key]
                
                # Reiniciar si la ventana expiró
                if now - first_attempt > window:
                    session['rate_limit_api'][key] = [1, now]
                elif attempts >= max_attempts:
                    logger.warning(f'API Rate limit excedido para {key}')
                    return jsonify({
                        'error': 'Demasiadas peticiones. Por favor espera.',
                        'retry_after': int(window - (now - first_attempt))
                    }), 429
                else:
                    session['rate_limit_api'][key] = [attempts + 1, first_attempt]
            else:
                session['rate_limit_api'][key] = [1, now]
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================
# DECORADORES DE VALIDACIÓN
# ============================================

def validate_json(schema=None):
    """
    Validar que el request contenga JSON válido y opcionalmente un esquema
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Se esperaba Content-Type: application/json'}), 400
            
            data = request.get_json()
            
            if schema:
                # Validación básica de campos requeridos
                required_fields = schema.get('required', [])
                for field in required_fields:
                    if field not in data:
                        return jsonify({'error': f'Campo requerido: {field}'}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_params(*params):
    """
    Validar que los parámetros de URL estén presentes
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            for param in params:
                if param not in request.args:
                    return jsonify({'error': f'Parámetro requerido: {param}'}), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================
# DECORADORES DE LOGGING
# ============================================

def log_request(f):
    """
    Decorador para registrar peticiones
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Registrar inicio de petición
        logger.info(f'Request: {request.method} {request.path} - IP: {request.remote_addr}')
        
        # Ejecutar función
        try:
            result = f(*args, **kwargs)
            logger.info(f'Response: {request.method} {request.path} - Status: 200')
            return result
        except Exception as e:
            logger.error(f'Error en {request.method} {request.path}: {str(e)}')
            raise
    
    return decorated_function

def log_time(f):
    """
    Decorador para medir tiempo de ejecución
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import time
        start = time.time()
        result = f(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f'Tiempo de ejecución: {elapsed:.4f}s - {request.path}')
        return result
    return decorated_function

# ============================================
# DECORADORES DE CACHE
# ============================================

def cache_response(timeout: int = 300):
    """
    Cachear respuesta HTTP
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import make_response
            response = make_response(f(*args, **kwargs))
            
            # Agregar headers de cache
            response.headers['Cache-Control'] = f'public, max-age={timeout}'
            response.headers['Expires'] = (datetime.utcnow() + timedelta(seconds=timeout)).strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            return response
        return decorated_function
    return decorator

# ============================================
# DECORADORES DE COMPRESIÓN
# ============================================

def compress_response(f):
    """
    Comprimir respuesta si el cliente lo soporta
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Verificar si el cliente acepta gzip
        if 'gzip' in request.headers.get('Accept-Encoding', ''):
            from flask import make_response
            import gzip
            from io import BytesIO
            
            response = make_response(response)
            
            # Comprimir respuesta
            gzip_buffer = BytesIO()
            with gzip.GzipFile(mode='wb', fileobj=gzip_buffer) as gzip_file:
                gzip_file.write(response.data)
            
            response.data = gzip_buffer.getvalue()
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Length'] = str(len(response.data))
            response.headers['Vary'] = 'Accept-Encoding'
        
        return response
    return decorated_function

# ============================================
# DECORADORES DE TRANSACCIÓN
# ============================================

def transactional(f):
    """
    Decorador para operaciones que deben ser transaccionales
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f'Error en transacción: {str(e)}')
            raise
    return decorated_function