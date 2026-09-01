"""
Módulo de seguridad de la aplicación
Maneja hash de contraseñas, tokens JWT, sanitización y rate limiting
"""
import bcrypt
import secrets
import hashlib
import logging
from functools import wraps
from datetime import datetime, timedelta
import jwt
from flask import session, request, current_app, jsonify, abort, flash, redirect, url_for
from flask_login import current_user

logger = logging.getLogger(__name__)

# ============================================
# HASH DE CONTRASEÑAS
# ============================================

def hash_password(password: str) -> tuple:
    """
    Hashear contraseña con bcrypt
    Returns: (hash, salt)
    """
    try:
        rounds = current_app.config.get('BCRYPT_ROUNDS', 12)
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8'), salt.decode('utf-8')
    except Exception as e:
        logger.error(f'Error hashing password: {str(e)}')
        raise

def verify_password(password: str, hashed: str) -> bool:
    """
    Verificar contraseña contra hash
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        logger.error(f'Error verifying password: {str(e)}')
        return False

def generate_salt(length: int = 64) -> str:
    """
    Generar salt aleatorio para seguridad adicional
    """
    return secrets.token_hex(length // 2)

# ============================================
# TOKENS JWT
# ============================================

def generate_token(user_id: str, expires_in: int = None) -> str:
    """
    Generar JWT token para autenticación
    """
    try:
        if expires_in is None:
            expires_in = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)
        
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        
        secret = current_app.config.get('JWT_SECRET_KEY')
        if not secret:
            raise Exception('JWT_SECRET_KEY no configurada')
        
        return jwt.encode(payload, secret, algorithm='HS256')
    except Exception as e:
        logger.error(f'Error generando token: {str(e)}')
        raise

def verify_token(token: str) -> dict:
    """
    Verificar y decodificar JWT token
    """
    try:
        secret = current_app.config.get('JWT_SECRET_KEY')
        if not secret:
            raise Exception('JWT_SECRET_KEY no configurada')
        
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning('Token expirado')
        raise Exception('Token expirado')
    except jwt.InvalidTokenError as e:
        logger.warning(f'Token inválido: {str(e)}')
        raise Exception('Token inválido')
    except Exception as e:
        logger.error(f'Error verificando token: {str(e)}')
        raise

# ============================================
# SANITIZACIÓN
# ============================================

def sanitize_input(text: str) -> str:
    """
    Sanitizar entrada de usuario para prevenir XSS
    """
    if not text:
        return text
    
    import html
    import re
    
    # Escapar caracteres HTML
    text = html.escape(text)
    
    # Eliminar etiquetas HTML
    text = re.sub(r'<[^>]*>', '', text)
    
    # Eliminar caracteres de control
    text = re.sub(r'[\x00-\x1f\x7f]', '', text)
    
    return text.strip()

def sanitize_email(email: str) -> str:
    """
    Sanitizar email
    """
    if not email:
        return email
    
    # Eliminar espacios y convertir a minúsculas
    email = email.strip().lower()
    
    # Eliminar caracteres no permitidos
    import re
    email = re.sub(r'[^\w@\.\-]', '', email)
    
    return email

# ============================================
# RATE LIMITING
# ============================================

def rate_limit(max_attempts: int = 5, window: int = 300):
    """
    Decorador para limitar intentos de acceso
    max_attempts: número máximo de intentos
    window: ventana de tiempo en segundos
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Crear clave única para el rate limit
            key = f"{request.endpoint}:{request.remote_addr}"
            
            # Inicializar sesión de rate limit
            if 'rate_limit' not in session:
                session['rate_limit'] = {}
            
            now = datetime.utcnow().timestamp()
            
            # Verificar límite
            if key in session['rate_limit']:
                attempts, first_attempt = session['rate_limit'][key]
                
                # Reiniciar si la ventana expiró
                if now - first_attempt > window:
                    session['rate_limit'][key] = [1, now]
                elif attempts >= max_attempts:
                    logger.warning(f'Rate limit excedido para {key}')
                    return jsonify({
                        'error': 'Demasiados intentos. Por favor espera unos minutos.'
                    }), 429
                else:
                    session['rate_limit'][key] = [attempts + 1, first_attempt]
            else:
                session['rate_limit'][key] = [1, now]
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================
# ROLES Y PERMISOS
# ============================================

def get_user_roles(user_id: str) -> list:
    """
    Obtener roles del usuario desde Supabase
    """
    try:
        from app.utils.supabase_client import get_supabase
        
        supabase = get_supabase()
        result = supabase.table('usuario_rol')\
            .select('rol(nombre_rol)')\
            .eq('id_usuario', user_id)\
            .eq('activo', True)\
            .execute()
        
        roles = []
        for item in result.data:
            if item.get('rol'):
                roles.append(item['rol']['nombre_rol'])
        return roles
    except Exception as e:
        logger.error(f'Error obteniendo roles: {str(e)}')
        return []

def has_role(user_id: str, role_name: str) -> bool:
    """
    Verificar si un usuario tiene un rol específico
    """
    roles = get_user_roles(user_id)
    return role_name in roles

def has_permission(user_id: str, permission_name: str) -> bool:
    """
    Verificar si un usuario tiene un permiso específico
    """
    try:
        from app.utils.supabase_client import get_supabase
        
        supabase = get_supabase()
        result = supabase.table('usuario_rol')\
            .select('rol(permiso(nombre_permiso))')\
            .eq('id_usuario', user_id)\
            .eq('activo', True)\
            .execute()
        
        for item in result.data:
            if item.get('rol'):
                for permiso in item['rol'].get('permiso', []):
                    if permiso.get('nombre_permiso') == permission_name:
                        return True
        return False
    except Exception as e:
        logger.error(f'Error verificando permiso: {str(e)}')
        return False

def require_roles(*allowed_roles):
    """
    Decorador para verificar roles en rutas web
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Por favor inicia sesión para acceder', 'warning')
                return redirect(url_for('auth.login'))
            
            user_roles = current_user.get_roles()
            
            if not any(role in allowed_roles for role in user_roles):
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================
# INICIALIZACIÓN DE SEGURIDAD
# ============================================

def init_security(app):
    """
    Inicializar configuración de seguridad de la aplicación
    """
    
    @app.before_request
    def security_headers():
        """Agregar headers de seguridad (se ejecuta antes de la respuesta)"""
        pass
    
    @app.after_request
    def add_security_headers(response):
        """Agregar headers de seguridad a todas las respuestas"""
        # Headers de seguridad
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = "geolocation=(), microphone=(), camera=()"
        
        # CSP - Content Security Policy (ACTUALIZADO)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://code.jquery.com https://www.gstatic.com https://translate.google.com https://translate.googleapis.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://www.gstatic.com; "
            "img-src 'self' data: https://images.unsplash.com https://*.supabase.co; "
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "connect-src 'self' https://*.supabase.co; "
            "frame-src https://translate.google.com; "
            "frame-ancestors 'none'"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # HSTS - Solo en producción
        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response

# ============================================
# GENERACIÓN DE CÓDIGOS SEGUROS
# ============================================

def generate_secure_code(length: int = 8) -> str:
    """
    Generar código seguro aleatorio para cupones, confirmaciones, etc.
    """
    import string
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_random_password(length: int = 12) -> str:
    """
    Generar contraseña aleatoria segura
    """
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_confirmation_token() -> str:
    """
    Generar token de confirmación único
    """
    return secrets.token_urlsafe(32)

# ============================================
# VALIDACIÓN DE DATOS
# ============================================

def is_valid_email(email: str) -> bool:
    """
    Validar formato de email
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_phone(phone: str) -> bool:
    """
    Validar formato de teléfono
    """
    import re
    pattern = r'^\+?[\d\s\-()]{7,20}$'
    return bool(re.match(pattern, phone))

def is_valid_password(password: str, min_length: int = 8) -> bool:
    """
    Validar fortaleza de contraseña
    """
    if len(password) < min_length:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    return has_upper and has_lower and has_digit

def sanitize_filename(filename: str) -> str:
    """
    Sanitizar nombre de archivo
    """
    import re
    filename = re.sub(r'[^a-zA-Z0-9\-_.]', '', filename)
    return filename