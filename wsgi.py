# wsgi.py - Punto de entrada para Vercel (versión robusta)
import os
import sys
import logging

# Configurar logging para que salga a stderr (logs de Vercel)
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# 1. Definir app como None para que Vercel vea la variable
app = None
application = None

# 2. Verificar variables de entorno (y mostrarlas en logs)
logging.info("=== VARIABLES DE ENTORNO ===")
required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'SECRET_KEY']
for var in required_vars:
    val = os.getenv(var)
    if val:
        logging.info(f"✅ {var} configurada (primeros 8 caracteres: {val[:8]}...)")
    else:
        logging.error(f"❌ {var} NO configurada")

# 3. Intentar importar y crear la app
try:
    from app import create_app
    logging.info("✅ create_app importada correctamente")
    
    # Crear la app en producción
    app = create_app('production')
    application = app
    logging.info("🚀 App creada correctamente")
    logging.info(f"   Tipo de app: {type(app)}")
    
except Exception as e:
    logging.exception("💥 ERROR al crear la app:")
    # No lanzamos excepción para que el despliegue no falle en la construcción,
    # pero la app será None y las peticiones fallarán con error 500.
    # Esto permitirá ver el error en los logs de Vercel.

# 4. Mostrar estado final de app
if app:
    logging.info("✅ app está definida correctamente")
else:
    logging.error("❌ app sigue siendo None después del intento de creación")

# Si la app se creó bien, añadir una ruta de prueba directa
if app:
    @app.route('/ping')
    def ping():
        return 'OK'