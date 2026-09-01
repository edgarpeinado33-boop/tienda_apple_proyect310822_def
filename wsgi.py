# wsgi.py - Punto de entrada para Vercel (CORREGIDO)
import sys
import os
import logging

# Configurar logging básico (opcional, pero útil)
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# 1. Verificar variables de entorno (solo imprimir, sin ejecutar lógica)
logging.info("=== VARIABLES DE ENTORNO ===")
for var in ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'SECRET_KEY']:
    val = os.getenv(var)
    if val:
        masked = val[:8] + '...' if len(val) > 8 else '***'
        logging.info(f"✅ {var} = {masked}")
    else:
        logging.error(f"❌ {var} NO DEFINIDA")

# 2. Crear la aplicación (esto es lo único que debe hacer wsgi.py)
try:
    from app import create_app
    app = create_app('production')
    application = app  # Vercel espera 'application' o 'app'
    logging.info("🚀 Aplicación iniciada correctamente")
except Exception as e:
    logging.exception("💥 ERROR FATAL al crear la aplicación:")
    raise  # Vercel capturará la excepción y marcará el despliegue como fallido