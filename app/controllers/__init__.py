"""
Módulo de controladores de la aplicación
"""
from .auth_controller import auth_bp
from .producto_controller import producto_bp
from .pedido_controller import pedido_bp
from .carrito_controller import carrito_bp
from .admin_controller import admin_bp

__all__ = [
    'auth_bp',
    'producto_bp', 
    'pedido_bp',
    'carrito_bp',
    'admin_bp'
]