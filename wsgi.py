# wsgi.py - con prueba de conexión a Supabase
import sys
import os
import logging
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# Verificar variables
for var in ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'SECRET_KEY']:
    val = os.getenv(var)
    logging.info(f"{var}: {'✅ configurada' if val else '❌ FALTA'}")

# Probar conexión a Supabase
try:
    from app.utils.supabase_client import get_supabase
    supabase = get_supabase()
    # Intenta contar productos (consulta ligera)
    result = supabase.table('producto').select('*', count='exact').limit(1).execute()
    logging.info(f"✅ Conexión a Supabase exitosa. Productos encontrados: {result.count}")
except Exception as e:
    logging.exception("💥 Error conectando a Supabase:")
    raise  # Esto hará que Vercel muestre el error

# Crear app
from app import create_app
app = create_app('production')
application = app
logging.info("🚀 App iniciada correctamente")