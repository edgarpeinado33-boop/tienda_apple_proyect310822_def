#!/usr/bin/env python
"""
Archivo principal para ejecutar la aplicación Tienda Apple
"""
import os
import sys
from app import create_app

def main():
    """Función principal"""
    # Obtener entorno
    env = os.getenv('FLASK_ENV', 'development')
    
    # Crear aplicación
    app = create_app(env)
    
    # Configurar host y puerto
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = True  # <--- CAMBIAR A TRUE
    
    # Mostrar información de inicio
    print("=" * 60)
    print("🍎 TIENDA APPLE - Sistema de Gestión")
    print("=" * 60)
    print(f"📦 Entorno: {env}")
    print(f"🔗 URL: http://{host}:{port}")
    print(f"🐛 Debug: {debug}")
    print("=" * 60)
    
    # Ejecutar aplicación
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()