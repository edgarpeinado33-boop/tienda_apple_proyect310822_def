"""
Controlador de Administración - VERSIÓN COMPLETA
Panel de administración con estadísticas, gestión de productos, usuarios y pedidos
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.utils.supabase_client import get_supabase, get_supabase_service
from datetime import datetime, timedelta
import logging
import json
import os
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

# Configuración de subida de archivos
UPLOAD_FOLDER = 'app/views/static/img/productos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================
# DASHBOARD
# ============================================

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Panel de administración principal"""
    try:
        supabase = get_supabase_service()
        
        stats = {}
        
        # Total de usuarios
        usuarios = supabase.table('usuario').select('*', count='exact').execute()
        stats['total_usuarios'] = usuarios.count
        
        # Usuarios activos (últimos 30 días)
        fecha_limite = (datetime.now() - timedelta(days=30)).isoformat()
        usuarios_activos = supabase.table('usuario')\
            .select('*', count='exact')\
            .gte('ultimo_acceso', fecha_limite)\
            .execute()
        stats['usuarios_activos'] = usuarios_activos.count
        
        # Total de productos
        productos = supabase.table('producto').select('*', count='exact').execute()
        stats['total_productos'] = productos.count
        
        # Productos activos
        productos_activos = supabase.table('producto')\
            .select('*', count='exact')\
            .eq('estado', 'activo')\
            .execute()
        stats['productos_activos'] = productos_activos.count
        
        # Total de pedidos
        pedidos = supabase.table('pedido').select('*', count='exact').execute()
        stats['total_pedidos'] = pedidos.count
        
        # Pedidos pendientes
        pendientes = supabase.table('pedido')\
            .select('*', count='exact')\
            .eq('estado', 'pendiente')\
            .execute()
        stats['pedidos_pendientes'] = pendientes.count
        
        # Ventas del día
        hoy = datetime.now().date().isoformat()
        ventas_hoy = supabase.table('pedido')\
            .select('total')\
            .gte('fecha_pedido', hoy)\
            .not_.eq('estado', 'cancelado')\
            .execute()
        
        total_ventas_hoy = sum(float(p['total']) for p in ventas_hoy.data)
        stats['ventas_hoy'] = total_ventas_hoy
        stats['pedidos_hoy'] = len(ventas_hoy.data)
        
        # Ventas del mes
        inicio_mes = datetime.now().replace(day=1).date().isoformat()
        ventas_mes = supabase.table('pedido')\
            .select('total')\
            .gte('fecha_pedido', inicio_mes)\
            .not_.eq('estado', 'cancelado')\
            .execute()
        
        stats['ventas_mes'] = sum(float(p['total']) for p in ventas_mes.data)
        
        # Ventas totales
        ventas_totales = supabase.table('pedido')\
            .select('total')\
            .not_.eq('estado', 'cancelado')\
            .execute()
        
        stats['ventas_totales'] = sum(float(p['total']) for p in ventas_totales.data)
        
        # Últimos pedidos
        ultimos_pedidos = supabase.table('pedido')\
            .select('*, usuario(nombre_completo, email)')\
            .order('fecha_pedido', desc=True)\
            .limit(10)\
            .execute()
        
        # Productos con bajo stock
        try:
            todas_variantes = supabase.table('variante_producto')\
                .select('*, producto(nombre)')\
                .eq('activo', True)\
                .execute()
            
            bajo_stock = []
            for item in todas_variantes.data:
                stock = item.get('stock_disponible', 0)
                minimo = item.get('stock_minimo', 0)
                if stock < minimo:
                    bajo_stock.append(item)
        except Exception as e:
            logger.error(f'Error obteniendo bajo stock: {str(e)}')
            bajo_stock = []
        
        # Productos más vendidos (corregido: usar fecha_pedido en lugar de created_at)
        try:
            # Obtener pedidos de los últimos 30 días
            fecha_limite_str = (datetime.now() - timedelta(days=30)).date().isoformat()
            pedidos_recientes = supabase.table('pedido')\
                .select('id_pedido')\
                .gte('fecha_pedido', fecha_limite_str)\
                .execute()
            
            pedidos_ids = [p['id_pedido'] for p in pedidos_recientes.data]
            
            if pedidos_ids:
                productos_vendidos = supabase.table('linea_pedido')\
                    .select('id_variante, cantidad')\
                    .in_('id_pedido', pedidos_ids)\
                    .execute()
                
                ventas_por_variante = {}
                for item in productos_vendidos.data:
                    variante_id = item['id_variante']
                    ventas_por_variante[variante_id] = ventas_por_variante.get(variante_id, 0) + item['cantidad']
                
                top_variantes = sorted(ventas_por_variante.items(), key=lambda x: x[1], reverse=True)[:5]
                top_productos = []
                for variante_id, cantidad in top_variantes:
                    variante = supabase.table('variante_producto')\
                        .select('*, producto(nombre)')\
                        .eq('id_variante', variante_id)\
                        .execute()
                    if variante.data:
                        top_productos.append({
                            'nombre': variante.data[0]['producto']['nombre'],
                            'variante': variante.data[0]['color'] or variante.data[0]['capacidad'] or '',
                            'cantidad': cantidad
                        })
            else:
                top_productos = []
        except Exception as e:
            logger.error(f'Error obteniendo top productos: {str(e)}')
            top_productos = []
        
        return render_template('admin/dashboard.html',
                             stats=stats,
                             ultimos_pedidos=ultimos_pedidos.data,
                             bajo_stock=bajo_stock,
                             top_productos=top_productos,
                             now=datetime.now())
    except Exception as e:
        logger.error(f'Error cargando dashboard: {str(e)}')
        flash('Error cargando el dashboard', 'danger')
        return render_template('admin/dashboard.html', stats={}, now=datetime.now())


# ============================================
# GESTIÓN DE PRODUCTOS
# ============================================

@admin_bp.route('/productos')
@login_required
def gestion_productos():
    """Gestión de productos"""
    try:
        supabase = get_supabase_service()
        
        page = request.args.get('page', 1, type=int)
        per_page = 20
        search = request.args.get('search', '')
        
        start = (page - 1) * per_page
        
        query = supabase.table('producto')\
            .select('*')\
            .order('created_at', desc=True)
        
        if search:
            query = query.ilike('nombre', f'%{search}%')
        
        query = query.range(start, start + per_page - 1)
        result = query.execute()
        
        count_query = supabase.table('producto').select('*', count='exact')
        if search:
            count_query = count_query.ilike('nombre', f'%{search}%')
        count_result = count_query.execute()
        
        return render_template('admin/productos.html',
                             productos=result.data,
                             page=page,
                             total=count_result.count,
                             per_page=per_page,
                             search=search)
    except Exception as e:
        logger.error(f'Error cargando gestión de productos: {str(e)}')
        flash('Error cargando la gestión de productos', 'danger')
        return render_template('admin/productos.html', productos=[])


# ============================================
# CREAR PRODUCTO
# ============================================

@admin_bp.route('/productos/crear', methods=['GET', 'POST'])
@login_required
def crear_producto():
    """Crear nuevo producto"""
    if request.method == 'POST':
        try:
            supabase = get_supabase_service()
            
            producto_data = {
                'nombre': request.form.get('nombre', '').strip(),
                'descripcion': request.form.get('descripcion', '').strip(),
                'precio_base': float(request.form.get('precio_base', 0)),
                'familia': request.form.get('familia', '').strip(),
                'marca': request.form.get('marca', 'Apple'),
                'estado': request.form.get('estado', 'activo'),
                'proveedor': request.form.get('proveedor', '').strip(),
                'codigo_fabricante': request.form.get('codigo_fabricante', '').strip(),
                'peso_kg': float(request.form.get('peso_kg', 0)) if request.form.get('peso_kg') else None,
                'dimensiones': request.form.get('dimensiones', '').strip()
            }
            
            if not producto_data['nombre']:
                flash('El nombre del producto es requerido', 'warning')
                return render_template('admin/crear_producto.html')
            
            if producto_data['precio_base'] <= 0:
                flash('El precio debe ser mayor a 0', 'warning')
                return render_template('admin/crear_producto.html')
            
            result = supabase.table('producto')\
                .insert(producto_data)\
                .execute()
            
            if result.data:
                producto_id = result.data[0]['id_producto']
                
                # Asignar categorías
                categorias_ids = request.form.getlist('categorias')
                for cat_id in categorias_ids:
                    if cat_id:
                        supabase.table('producto_categoria').insert({
                            'id_producto': producto_id,
                            'id_categoria': cat_id
                        }).execute()
                
                flash('Producto creado exitosamente', 'success')
                return redirect(url_for('admin.gestion_productos'))
            else:
                flash('Error creando el producto', 'danger')
        except Exception as e:
            logger.error(f'Error creando producto: {str(e)}')
            flash('Error creando el producto', 'danger')
    
    try:
        supabase = get_supabase_service()
        categorias = supabase.table('categoria')\
            .select('*')\
            .eq('activo', True)\
            .order('nombre')\
            .execute()
        
        return render_template('admin/crear_producto.html', categorias=categorias.data)
    except Exception as e:
        logger.error(f'Error cargando formulario de creación: {str(e)}')
        flash('Error cargando el formulario', 'danger')
        return redirect(url_for('admin.gestion_productos'))


# ============================================
# EDITAR PRODUCTO
# ============================================

@admin_bp.route('/productos/editar/<producto_id>', methods=['GET', 'POST'])
@login_required
def editar_producto(producto_id):
    """Editar producto"""
    try:
        supabase = get_supabase_service()
        
        if request.method == 'POST':
            producto_data = {
                'nombre': request.form.get('nombre', '').strip(),
                'descripcion': request.form.get('descripcion', '').strip(),
                'precio_base': float(request.form.get('precio_base', 0)),
                'familia': request.form.get('familia', '').strip(),
                'marca': request.form.get('marca', 'Apple'),
                'estado': request.form.get('estado', 'activo'),
                'proveedor': request.form.get('proveedor', '').strip(),
                'codigo_fabricante': request.form.get('codigo_fabricante', '').strip(),
                'peso_kg': float(request.form.get('peso_kg', 0)) if request.form.get('peso_kg') else None,
                'dimensiones': request.form.get('dimensiones', '').strip()
            }
            
            supabase.table('producto')\
                .update(producto_data)\
                .eq('id_producto', producto_id)\
                .execute()
            
            flash('Producto actualizado exitosamente', 'success')
            return redirect(url_for('admin.gestion_productos'))
        
        producto = supabase.table('producto')\
            .select('*')\
            .eq('id_producto', producto_id)\
            .execute()
        
        if not producto.data:
            flash('Producto no encontrado', 'warning')
            return redirect(url_for('admin.gestion_productos'))
        
        return render_template('admin/editar_producto.html', producto=producto.data[0])
    except Exception as e:
        logger.error(f'Error editando producto: {str(e)}')
        flash('Error editando el producto', 'danger')
        return redirect(url_for('admin.gestion_productos'))


# ============================================
# SUBIR IMAGEN
# ============================================

@admin_bp.route('/productos/subir-imagen/<producto_id>', methods=['GET', 'POST'])
@login_required
def subir_imagen(producto_id):
    """Subir imagen para un producto"""
    try:
        supabase = get_supabase_service()
        
        producto = supabase.table('producto').select('*').eq('id_producto', producto_id).execute()
        if not producto.data:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('admin.gestion_productos'))
        
        if request.method == 'POST':
            if 'imagen' not in request.files:
                flash('No se seleccionó ningún archivo', 'warning')
                return redirect(request.url)
            
            file = request.files['imagen']
            
            if file.filename == '':
                flash('No se seleccionó ningún archivo', 'warning')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                nombre_archivo = f"{producto_id}.{ext}"
                
                upload_path = os.path.join(current_app.root_path, 'views', 'static', 'img', 'productos')
                os.makedirs(upload_path, exist_ok=True)
                
                file_path = os.path.join(upload_path, nombre_archivo)
                file.save(file_path)
                
                url_imagen = f"/static/img/productos/{nombre_archivo}"
                supabase.table('producto')\
                    .update({'imagen_url': url_imagen})\
                    .eq('id_producto', producto_id)\
                    .execute()
                
                flash('Imagen subida exitosamente', 'success')
                return redirect(url_for('admin.editar_producto', producto_id=producto_id))
            else:
                flash('Formato no permitido. Usa: PNG, JPG, JPEG, GIF, WEBP, SVG, BMP', 'danger')
        
        return render_template('admin/subir_imagen.html', producto=producto.data[0])
    except Exception as e:
        logger.error(f'Error subiendo imagen: {str(e)}')
        flash('Error subiendo la imagen', 'danger')
        return redirect(url_for('admin.gestion_productos'))


# ============================================
# ELIMINAR PRODUCTO
# ============================================

@admin_bp.route('/productos/eliminar/<producto_id>', methods=['POST'])
@login_required
def eliminar_producto(producto_id):
    """Eliminar producto (cambiar estado a discontinuado)"""
    try:
        supabase = get_supabase_service()
        
        supabase.table('producto')\
            .update({'estado': 'discontinuado'})\
            .eq('id_producto', producto_id)\
            .execute()
        
        return jsonify({'success': True, 'message': 'Producto eliminado exitosamente'})
    except Exception as e:
        logger.error(f'Error eliminando producto: {str(e)}')
        return jsonify({'error': str(e)}), 500


# ============================================
# GESTIÓN DE USUARIOS
# ============================================

@admin_bp.route('/usuarios')
@login_required
def gestion_usuarios():
    """Gestión de usuarios"""
    try:
        supabase = get_supabase_service()
        
        page = request.args.get('page', 1, type=int)
        per_page = 20
        search = request.args.get('search', '')
        
        start = (page - 1) * per_page
        
        query = supabase.table('usuario')\
            .select('*, usuario_rol(rol(nombre_rol))')\
            .order('fecha_registro', desc=True)
        
        if search:
            query = query.or_(f"nombre_completo.ilike.%{search}%,email.ilike.%{search}%")
        
        query = query.range(start, start + per_page - 1)
        result = query.execute()
        
        count_query = supabase.table('usuario').select('*', count='exact')
        if search:
            count_query = count_query.or_(f"nombre_completo.ilike.%{search}%,email.ilike.%{search}%")
        count_result = count_query.execute()
        
        return render_template('admin/usuarios.html',
                             usuarios=result.data,
                             page=page,
                             total=count_result.count,
                             per_page=per_page,
                             search=search)
    except Exception as e:
        logger.error(f'Error cargando gestión de usuarios: {str(e)}')
        flash('Error cargando la gestión de usuarios', 'danger')
        return render_template('admin/usuarios.html', usuarios=[])


@admin_bp.route('/usuarios/cambiar-estado/<usuario_id>', methods=['POST'])
@login_required
def cambiar_estado_usuario(usuario_id):
    """Activar/desactivar usuario"""
    try:
        supabase = get_supabase_service()
        
        if usuario_id == current_user.id:
            return jsonify({'error': 'No puedes desactivar tu propia cuenta'}), 400
        
        usuario = supabase.table('usuario')\
            .select('activo')\
            .eq('id_usuario', usuario_id)\
            .execute()
        
        if not usuario.data:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        nuevo_estado = not usuario.data[0]['activo']
        
        supabase.table('usuario')\
            .update({'activo': nuevo_estado})\
            .eq('id_usuario', usuario_id)\
            .execute()
        
        return jsonify({'success': True, 'activo': nuevo_estado})
    except Exception as e:
        logger.error(f'Error cambiando estado del usuario: {str(e)}')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/usuarios/cambiar-rol', methods=['POST'])
@login_required
def cambiar_rol_usuario():
    """Cambiar rol de usuario"""
    try:
        supabase = get_supabase_service()
        
        usuario_id = request.form.get('usuario_id')
        rol_id = request.form.get('rol_id')
        
        if not usuario_id or not rol_id:
            flash('Datos incompletos', 'warning')
            return redirect(url_for('admin.gestion_usuarios'))
        
        if usuario_id == current_user.id:
            flash('No puedes cambiar tu propio rol', 'warning')
            return redirect(url_for('admin.gestion_usuarios'))
        
        supabase.table('usuario_rol')\
            .update({'activo': False})\
            .eq('id_usuario', usuario_id)\
            .execute()
        
        supabase.table('usuario_rol').insert({
            'id_usuario': usuario_id,
            'id_rol': rol_id,
            'activo': True
        }).execute()
        
        flash('Rol actualizado exitosamente', 'success')
    except Exception as e:
        logger.error(f'Error cambiando rol del usuario: {str(e)}')
        flash('Error cambiando el rol del usuario', 'danger')
    
    return redirect(url_for('admin.gestion_usuarios'))


# ============================================
# CONFIGURACIÓN
# ============================================

@admin_bp.route('/configuracion')
@login_required
def configuracion():
    """Configuración del sistema"""
    try:
        supabase = get_supabase_service()
        
        configuracion = supabase.table('configuracion').select('*').execute()
        
        if not configuracion.data:
            config_default = {
                'clave': 'configuracion_general',
                'valor': json.dumps({
                    'nombre_tienda': 'Tienda Apple',
                    'email_contacto': 'contacto@tiendaapple.com',
                    'telefono_contacto': '+34 900 123 456',
                    'direccion_tienda': 'Calle Principal 1, Madrid, España',
                    'iva_porcentaje': 21,
                    'gastos_envio_estandar': 5.99,
                    'gastos_envio_gratis_desde': 50,
                    'email_notificaciones': 'notificaciones@tiendaapple.com',
                    'moneda': 'EUR',
                    'idioma': 'es'
                })
            }
            supabase.table('configuracion')\
                .insert(config_default)\
                .execute()
            
            configuracion = supabase.table('configuracion').select('*').execute()
        
        config_data = json.loads(configuracion.data[0]['valor']) if configuracion.data else {}
        
        return render_template('admin/configuracion.html', config=config_data)
    except Exception as e:
        logger.error(f'Error cargando configuración: {str(e)}')
        flash('Error cargando la configuración', 'danger')
        return render_template('admin/configuracion.html', config={})


@admin_bp.route('/configuracion/guardar', methods=['POST'])
@login_required
def guardar_configuracion():
    """Guardar configuración"""
    try:
        supabase = get_supabase_service()
        
        config_data = {
            'nombre_tienda': request.form.get('nombre_tienda', 'Tienda Apple'),
            'email_contacto': request.form.get('email_contacto', ''),
            'telefono_contacto': request.form.get('telefono_contacto', ''),
            'direccion_tienda': request.form.get('direccion_tienda', ''),
            'iva_porcentaje': float(request.form.get('iva_porcentaje', 21)),
            'gastos_envio_estandar': float(request.form.get('gastos_envio_estandar', 5.99)),
            'gastos_envio_gratis_desde': float(request.form.get('gastos_envio_gratis_desde', 50)),
            'email_notificaciones': request.form.get('email_notificaciones', ''),
            'moneda': request.form.get('moneda', 'EUR'),
            'idioma': request.form.get('idioma', 'es')
        }
        
        supabase.table('configuracion')\
            .update({'valor': json.dumps(config_data)})\
            .eq('clave', 'configuracion_general')\
            .execute()
        
        flash('Configuración guardada exitosamente', 'success')
    except Exception as e:
        logger.error(f'Error guardando configuración: {str(e)}')
        flash('Error guardando la configuración', 'danger')
    
    return redirect(url_for('admin.configuracion'))