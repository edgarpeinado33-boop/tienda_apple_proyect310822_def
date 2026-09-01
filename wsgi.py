# wsgi.py - Punto de entrada para Vercel (CORREGIDO)
import sys
import os
import logging

# Configurar logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# 1. Verificar variables de entorno (esto no necesita contexto)
logging.info("=== VARIABLES DE ENTORNO ===")
for var in ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'SECRET_KEY']:
    val = os.getenv(var)
    if val:
        masked = val[:8] + '...' if len(val) > 8 else '***'
        logging.info(f"✅ {var} = {masked}")
    else:
        logging.error(f"❌ {var} NO DEFINIDA")

# 2. Crear la aplicación
from app import create_app
app = create_app('production')

# 3. Ahora, dentro del contexto de la aplicación, probar Supabase
try:
    with app.app_context():
        from app.utils.supabase_client import get_supabase
        supabase = get_supabase()
        # Consulta simple para verificar conexión
        result = supabase.table('producto').select('*').limit(1).execute()
        logging.info(f"✅ Conexión a Supabase exitosa. Primer producto: {result.data[0] if result.data else 'ninguno'}")
except Exception as e:
    logging.exception("⚠️ Error al conectar a Supabase (la app seguirá arrancando):")

# Vercel espera 'application'
application = app

logging.info("🚀 Aplicación iniciada correctamente")