"""
Prueba de conexión a Supabase - USANDO SERVICE KEY
"""
import os
from dotenv import load_dotenv
from supabase import create_client

# Cargar variables de entorno
load_dotenv()

print("=" * 60)
print("🔍 PROBANDO CONEXIÓN A SUPABASE (CON SERVICE KEY)")
print("=" * 60)

# USAR SERVICE KEY PARA VER TODOS LOS DATOS
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')  # <--- CAMBIADO A SERVICE KEY

print(f"\n📌 URL: {url}")
print(f"📌 KEY: {key[:30]}..." if key else "KEY: No configurada")

if not url or not key:
    print("\n❌ ERROR: Credenciales no configuradas")
    exit(1)

print("\n✅ Credenciales cargadas")

# Conectar a Supabase
try:
    supabase = create_client(url, key)
    print("✅ Conexión establecida")
    
    # 1. Verificar productos
    print("\n📦 PRODUCTOS:")
    result = supabase.table('producto').select('*').execute()
    print(f"  Total: {len(result.data)}")
    
    if len(result.data) > 0:
        for p in result.data[:5]:
            print(f"  - {p.get('nombre')} (${p.get('precio_base')})")
    else:
        print("  ⚠️ No hay productos")
    
    # 2. Verificar categorías
    print("\n📂 CATEGORÍAS:")
    result = supabase.table('categoria').select('*').execute()
    print(f"  Total: {len(result.data)}")
    
    if len(result.data) > 0:
        for c in result.data[:5]:
            print(f"  - {c.get('nombre')} ({c.get('slug')})")
    else:
        print("  ⚠️ No hay categorías")
    
    # 3. Verificar usuarios
    print("\n👤 USUARIOS:")
    result = supabase.table('usuario').select('*').execute()
    print(f"  Total: {len(result.data)}")
    
    if len(result.data) > 0:
        for u in result.data[:3]:
            print(f"  - {u.get('email')} ({u.get('nombre_completo')})")
    else:
        print("  ⚠️ No hay usuarios")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)