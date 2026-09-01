# wsgi.py - Con verificación de Supabase
import sys
import os
import logging

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# 1. Verificar variables de entorno
logging.info("=== VARIABLES DE ENTORNO ===")
for var in ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'SECRET_KEY']:
    val = os.getenv(var)
    if val:
        masked = val[:8] + '...' if len(val) > 8 else '***'
        logging.info(f"✅ {var} = {masked}")
    else:
        logging.error(f"❌ {var} NO DEFINIDA")

# 2. Probar conexión a Supabase
try:
    from app.utils.supabase_client import get_supabase
    supabase = get_supabase()
    # Intenta obtener 1 producto (consulta ligera)
    result = supabase.table('producto').select('*').limit(1).execute()
    logging.info(f"✅ Conexión exitosa. Primer producto: {result.data[0] if result.data else 'ninguno'}")
except Exception as e:
    logging.exception("💥 ERROR al conectar a Supabase:")
    # No lanzamos excepción para que la app intente arrancar, pero el error quedará en logs
    # Si quieres detener el despliegue, usa raise

# 3. Crear la aplicación
from app import create_app
app = create_app('production')
application = app
logging.info("🚀 Aplicación iniciada")