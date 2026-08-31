# app.py - Punto de entrada para Vercel
import sys
import logging
import os
from app import create_app

# Configurar logging para Vercel (se verá en los logs de la función)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    logger.info("🚀 Iniciando aplicación en Vercel...")
    
    # Verificar variables de entorno críticas
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'SECRET_KEY', 'JWT_SECRET_KEY']
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        logger.error(f"❌ Faltan variables de entorno: {missing}")
        raise RuntimeError(f"Faltan variables de entorno: {missing}")
    
    # Crear la app en modo producción (puedes cambiar a 'development' si lo prefieres)
    app = create_app('production')
    
    logger.info("✅ Aplicación creada correctamente")
    
except Exception as e:
    logger.error(f"❌ Error al crear la aplicación: {str(e)}", exc_info=True)
    # Re-lanzar la excepción para que Vercel la capture y la muestre en los logs
    raise

# Vercel espera una variable llamada 'app'
# Si usas 'application', también funciona, pero 'app' es más común