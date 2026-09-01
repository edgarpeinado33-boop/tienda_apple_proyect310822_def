# wsgi.py - Punto de entrada para Vercel
import sys
import os
import traceback

print("🔍 Iniciando wsgi.py...")

try:
    # Verificar variables de entorno críticas
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        print(f"❌ Faltan variables de entorno: {missing}")
    
    print("📦 Importando create_app desde app...")
    from app import create_app
    print("✅ create_app importado correctamente")
    
    print("🏗️ Creando la aplicación en modo producción...")
    app = create_app('production')
    print("✅ Aplicación creada correctamente")
    
except Exception as e:
    print("❌ ERROR:", str(e))
    traceback.print_exc(file=sys.stdout)
    raise

# Vercel espera 'app'