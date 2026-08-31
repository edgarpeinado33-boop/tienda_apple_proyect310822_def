"""
Script para cargar datos de prueba en Supabase
USANDO SERVICE KEY (sin RLS)
"""
import os
from dotenv import load_dotenv
from supabase import create_client
import bcrypt
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Usar SERVICE KEY para evitar RLS
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')  # <--- CAMBIADO A SERVICE KEY

if not url or not key:
    print("❌ Error: Credenciales no configuradas")
    exit(1)

supabase = create_client(url, key)

print("=" * 70)
print("🍎 CARGANDO DATOS DE PRUEBA EN SUPABASE (CON SERVICE KEY)")
print("=" * 70)

def hash_password(password):
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# ============================================
# 1. USUARIOS
# ============================================
print("\n👤 1. Creando usuarios...")

usuarios = [
    {'nombre_completo': 'Administrador', 'email': 'admin@tiendaapple.com', 'contrasena_hash': hash_password('Admin123!'), 'salt': 'dummy', 'telefono': '+34 600 000 001', 'fecha_registro': datetime.now().date().isoformat(), 'email_verificado': True, 'activo': True},
    {'nombre_completo': 'Juan Pérez', 'email': 'juan@email.com', 'contrasena_hash': hash_password('Cliente123!'), 'salt': 'dummy', 'telefono': '+34 600 000 002', 'fecha_registro': datetime.now().date().isoformat(), 'email_verificado': True, 'activo': True},
    {'nombre_completo': 'María García', 'email': 'maria@email.com', 'contrasena_hash': hash_password('Cliente123!'), 'salt': 'dummy', 'telefono': '+34 600 000 003', 'fecha_registro': datetime.now().date().isoformat(), 'email_verificado': True, 'activo': True},
    {'nombre_completo': 'Carlos López', 'email': 'carlos@email.com', 'contrasena_hash': hash_password('Cliente123!'), 'salt': 'dummy', 'telefono': '+34 600 000 004', 'fecha_registro': datetime.now().date().isoformat(), 'email_verificado': True, 'activo': True},
]

for user in usuarios:
    try:
        result = supabase.table('usuario').insert(user).execute()
        if result.data:
            print(f"  ✅ Usuario creado: {user['email']}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

# ============================================
# 2. ASIGNAR ROLES
# ============================================
print("\n📝 2. Asignando roles...")

try:
    usuarios_db = supabase.table('usuario').select('*').execute()
    roles = supabase.table('rol').select('*').execute()
    roles_dict = {r['nombre_rol']: r['id_rol'] for r in roles.data}
    
    for user in usuarios_db.data:
        rol = 'SUPER_ADMIN' if user['email'] == 'admin@tiendaapple.com' else 'CLIENTE'
        if rol in roles_dict:
            existing = supabase.table('usuario_rol').select('*').eq('id_usuario', user['id_usuario']).eq('id_rol', roles_dict[rol]).execute()
            if not existing.data:
                supabase.table('usuario_rol').insert({
                    'id_usuario': user['id_usuario'],
                    'id_rol': roles_dict[rol],
                    'activo': True
                }).execute()
                print(f"  ✅ Rol {rol} asignado a {user['email']}")
except Exception as e:
    print(f"  ❌ Error asignando roles: {e}")

# ============================================
# 3. CATEGORÍAS
# ============================================
print("\n📂 3. Creando categorías...")

categorias = [
    {'nombre': 'iPhone', 'slug': 'iphone', 'descripcion': 'Teléfonos inteligentes Apple'},
    {'nombre': 'iPad', 'slug': 'ipad', 'descripcion': 'Tabletas Apple'},
    {'nombre': 'Mac', 'slug': 'mac', 'descripcion': 'Computadoras Apple'},
    {'nombre': 'Apple Watch', 'slug': 'apple-watch', 'descripcion': 'Relojes inteligentes Apple'},
    {'nombre': 'AirPods', 'slug': 'airpods', 'descripcion': 'Auriculares y audífonos Apple'},
    {'nombre': 'Apple TV', 'slug': 'apple-tv', 'descripcion': 'Dispositivos de streaming Apple'},
    {'nombre': 'Accesorios', 'slug': 'accesorios', 'descripcion': 'Accesorios para dispositivos Apple'},
]

for cat in categorias:
    try:
        result = supabase.table('categoria').insert(cat).execute()
        if result.data:
            print(f"  ✅ Categoría {cat['nombre']} creada")
    except Exception as e:
        print(f"  ❌ Error: {e}")

# ============================================
# 4. PRODUCTOS
# ============================================
print("\n📦 4. Creando productos...")

productos = [
    {'nombre': 'iPhone 15 Pro Max', 'descripcion': 'El iPhone más avanzado con titanio, chip A17 Pro y cámara de 48MP', 'precio_base': 1199.00, 'imagen_url': 'https://images.unsplash.com/photo-1510557880100-43aa80b5e834?w=400', 'familia': 'iPhone', 'marca': 'Apple', 'estado': 'activo'},
    {'nombre': 'iPhone 15 Pro', 'descripcion': 'iPhone 15 Pro con titanio, chip A17 Pro y cámara de 48MP', 'precio_base': 1099.00, 'imagen_url': 'https://images.unsplash.com/photo-1510557880100-43aa80b5e834?w=400', 'familia': 'iPhone', 'marca': 'Apple', 'estado': 'activo'},
    {'nombre': 'iPhone 15', 'descripcion': 'iPhone 15 con Dynamic Island y cámara de 48MP', 'precio_base': 799.00, 'imagen_url': 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=400', 'familia': 'iPhone', 'marca': 'Apple', 'estado': 'activo'},
    {'nombre': 'MacBook Air M2', 'descripcion': 'MacBook Air con chip M2, ligera y potente', 'precio_base': 1299.00, 'imagen_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400', 'familia': 'MacBook', 'marca': 'Apple', 'estado': 'activo'},
    {'nombre': 'MacBook Pro 14" M3', 'descripcion': 'MacBook Pro con chip M3, para profesionales', 'precio_base': 1999.00, 'imagen_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400', 'familia': 'MacBook', 'marca': 'Apple', 'estado': 'activo'},
    {'nombre': 'iPad Pro 12.9" M2', 'descripcion': 'iPad Pro con chip M2 y pantalla XDR de 12.9"', 'precio_base': 1099.00, 'imagen_url': 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400', 'familia': 'iPad', 'marca': 'Apple', 'estado': 'activo'},
    {'nombre': 'iPad Air 10.9" M1', 'descripcion': 'iPad Air con chip M1 y pantalla Liquid Retina de 10.9"', 'precio_base': 599.00, 'imagen_url': 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400', 'familia': 'iPad', 'marca': 'Apple', 'estado': 'activo'},
    {'nombre': 'Apple Watch Series 9', 'descripcion': 'Apple Watch Series 9 con pantalla siempre activa', 'precio_base': 399.00, 'imagen_url': 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=400', 'familia': 'Apple Watch', 'marca': 'Apple', 'estado': 'activo'},
    {'nombre': 'Apple Watch Ultra 2', 'descripcion': 'Apple Watch Ultra 2 con pantalla de 49mm y GPS+LTE', 'precio_base': 799.00, 'imagen_url': 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=400', 'familia': 'Apple Watch', 'marca': 'Apple', 'estado': 'activo'},
    {'nombre': 'AirPods Pro 2', 'descripcion': 'AirPods Pro con cancelación de ruido y audio espacial', 'precio_base': 249.00, 'imagen_url': 'https://images.unsplash.com/photo-1588423771073-b8903fbb85b5?w=400', 'familia': 'AirPods', 'marca': 'Apple', 'estado': 'activo'},
    {'nombre': 'AirPods Max', 'descripcion': 'AirPods Max con audio de alta fidelidad', 'precio_base': 549.00, 'imagen_url': 'https://images.unsplash.com/photo-1588423771073-b8903fbb85b5?w=400', 'familia': 'AirPods', 'marca': 'Apple', 'estado': 'activo'},
    {'nombre': 'Apple TV 4K', 'descripcion': 'Apple TV 4K con chip A15 Bionic', 'precio_base': 149.00, 'imagen_url': 'https://images.unsplash.com/photo-1581251917070-90de70bdc9e0?w=400', 'familia': 'Apple TV', 'marca': 'Apple', 'estado': 'activo'},
    {'nombre': 'HomePod Mini', 'descripcion': 'HomePod Mini con Siri y audio de alta calidad', 'precio_base': 99.00, 'imagen_url': 'https://images.unsplash.com/photo-1581251917070-90de70bdc9e0?w=400', 'familia': 'HomePod', 'marca': 'Apple', 'estado': 'activo'},
]

for producto in productos:
    try:
        result = supabase.table('producto').insert(producto).execute()
        if result.data:
            print(f"  ✅ Producto {producto['nombre']} creado")
    except Exception as e:
        print(f"  ❌ Error: {e}")

# ============================================
# 5. ASIGNAR PRODUCTOS A CATEGORÍAS
# ============================================
print("\n🔗 5. Asignando productos a categorías...")

try:
    productos_db = supabase.table('producto').select('*').execute()
    categorias_db = supabase.table('categoria').select('*').execute()
    
    prod_dict = {p['nombre']: p['id_producto'] for p in productos_db.data}
    cat_dict = {c['slug']: c['id_categoria'] for c in categorias_db.data}
    
    asignaciones = [
        ('iPhone 15 Pro Max', 'iphone'),
        ('iPhone 15 Pro', 'iphone'),
        ('iPhone 15', 'iphone'),
        ('MacBook Air M2', 'mac'),
        ('MacBook Pro 14" M3', 'mac'),
        ('iPad Pro 12.9" M2', 'ipad'),
        ('iPad Air 10.9" M1', 'ipad'),
        ('Apple Watch Series 9', 'apple-watch'),
        ('Apple Watch Ultra 2', 'apple-watch'),
        ('AirPods Pro 2', 'airpods'),
        ('AirPods Max', 'airpods'),
        ('Apple TV 4K', 'apple-tv'),
        ('HomePod Mini', 'accesorios'),
    ]
    
    for prod_nombre, cat_slug in asignaciones:
        if prod_nombre in prod_dict and cat_slug in cat_dict:
            existing = supabase.table('producto_categoria').select('*').eq('id_producto', prod_dict[prod_nombre]).eq('id_categoria', cat_dict[cat_slug]).execute()
            if not existing.data:
                supabase.table('producto_categoria').insert({
                    'id_producto': prod_dict[prod_nombre],
                    'id_categoria': cat_dict[cat_slug]
                }).execute()
                print(f"  ✅ {prod_nombre} → {cat_slug}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# ============================================
# 6. VERIFICAR RESULTADOS
# ============================================
print("\n" + "=" * 70)
print("📊 RESULTADO FINAL")
print("=" * 70)

try:
    total_usuarios = supabase.table('usuario').select('*', count='exact').execute()
    total_productos = supabase.table('producto').select('*', count='exact').execute()
    total_categorias = supabase.table('categoria').select('*', count='exact').execute()
    
    print(f"  ✅ Usuarios: {total_usuarios.count}")
    print(f"  ✅ Productos: {total_productos.count}")
    print(f"  ✅ Categorías: {total_categorias.count}")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "=" * 70)
print("🔑 CREDENCIALES DE ACCESO:")
print("  Admin: admin@tiendaapple.com / Admin123!")
print("  Cliente: juan@email.com / Cliente123!")
print("=" * 70)
print("\n🌐 Ejecuta: python test_conexion.py")
print("🌐 Abre: http://127.0.0.1:5000/productos/")
print("=" * 70)