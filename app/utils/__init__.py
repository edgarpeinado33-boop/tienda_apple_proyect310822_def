"""
Módulo de utilidades de la aplicación
"""
from .supabase_client import get_supabase, get_supabase_service, init_supabase
from .security import (
    hash_password, verify_password, generate_token, verify_token,
    generate_salt, sanitize_input, rate_limit, require_roles,
    get_user_roles, init_security
)
from .decorators import (
    login_required_api, admin_required, roles_required,
    permission_required, rate_limit_api
)

__all__ = [
    # Supabase
    'get_supabase',
    'get_supabase_service',
    'init_supabase',
    
    # Security
    'hash_password',
    'verify_password',
    'generate_token',
    'verify_token',
    'generate_salt',
    'sanitize_input',
    'rate_limit',
    'require_roles',
    'get_user_roles',
    'init_security',
    
    # Decorators
    'login_required_api',
    'admin_required',
    'roles_required',
    'permission_required',
    'rate_limit_api'
]