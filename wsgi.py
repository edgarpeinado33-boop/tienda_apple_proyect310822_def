# wsgi.py - Punto de entrada para Vercel
import sys
import os
import logging

# Configurar logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# Verificar variables de entorno
logging.info("=== VARIABLES DE ENTORNO ===")
for var in ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'SECRET_KEY']:
    val = os.getenv(var)
    if val:
        masked = val[:8] + '...' if len(val) > 8 else '***'
        logging.info(f"✅ {var} = {masked}")
    else:
        logging.error(f"❌ {var} NO DEFINIDA")

# Crear la aplicación y asignarla a una variable de nivel superior
try:
    from app import create_app
    # Vercel busca 'app' o 'application' a nivel global
    app = create_app('production')
    # También asignamos a 'application' por compatibilidad
    application = app
    logging.info("🚀 Aplicación iniciada correctamente")
except Exception as e:
    logging.exception("💥 ERROR FATAL al crear la aplicación:")
    raise