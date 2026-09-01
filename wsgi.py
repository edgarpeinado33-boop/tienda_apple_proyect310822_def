# wsgi.py - Punto de entrada para Vercel (sin verificación global)
import sys
import os
import logging

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# Verificar variables de entorno (solo informativo)
logging.info("=== VARIABLES DE ENTORNO ===")
for var in ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'SECRET_KEY']:
    val = os.getenv(var)
    if val:
        masked = val[:8] + '...' if len(val) > 8 else '***'
        logging.info(f"✅ {var} = {masked}")
    else:
        logging.error(f"❌ {var} NO DEFINIDA")

# Crear la aplicación (esto sí debe estar en global)
from app import create_app
app = create_app('production')
application = app

# Opcional: probar Supabase dentro del contexto de la aplicación
# pero solo para logging, no es necesario para el funcionamiento
with app.app_context():
    try:
        from app.utils.supabase_client import get_supabase
        supabase = get_supabase()
        # Hacer una consulta ligera para probar
        result = supabase.table('producto').select('*').limit(1).execute()
        logging.info(f"✅ Conexión a Supabase OK. Productos: {result.count}")
    except Exception as e:
        logging.error(f"⚠️ Supabase connection test failed: {str(e)}")
        # No lanzamos excepción para que la app arranque igual

logging.info("🚀 Aplicación iniciada correctamente")