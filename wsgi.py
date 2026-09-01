# wsgi.py - Punto de entrada para Vercel
import sys
import os
import logging

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# Verificar variables de entorno (solo lectura, sin crear contexto)
for var in ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'SECRET_KEY']:
    value = os.getenv(var)
    if value:
        logging.info(f"✅ {var} configurada")
    else:
        logging.error(f"❌ {var} NO configurada")

# Crear la aplicación - esto debe estar a nivel global
try:
    from app import create_app
    app = create_app('production')
    application = app
    logging.info("🚀 Aplicación creada exitosamente")
except Exception as e:
    logging.exception("💥 Error creando la app:")
    raise