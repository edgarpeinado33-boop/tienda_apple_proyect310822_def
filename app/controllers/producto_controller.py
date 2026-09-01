"""
Controlador de Productos
"""
from flask import Blueprint, render_template, request, jsonify, abort, flash, redirect, url_for
from app.models.producto import Producto, VarianteProducto
from app.models.categoria import Categoria
from app.utils.supabase_client import get_supabase
import logging
import traceback

logger = logging.getLogger(__name__)

producto_bp = Blueprint('producto', __name__)


@producto_bp.route('/')
def index():
    """Página principal de productos"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    search = request.args.get('search', '')
    categoria = request.args.get('categoria', '')
    
    try:
        categorias = Categoria.get_raices()
        result = Producto.search(
            query=search,
            categoria=categoria,
            page=page,
            per_page=per_page,
            solo_activos=True
        )
        
        # Cargar variantes para cada producto
        for producto in result['productos']:
            producto.get_variantes()
        
        return render_template('productos/index.html',
                             productos=result['productos'],
                             categorias=categorias,
                             page=page,
                             search=search,
                             selected_categoria=categoria,
                             total=result['total'],
                             total_pages=result['total_pages'])
    except Exception as e:
        logger.error(f'Error cargando productos: {str(e)}')
        logger.error(traceback.format_exc())
        # Lanza la excepción para que Vercel la muestre en logs (en lugar de renderizar vacío)
        raise


# ============================================
# RUTAS ESPECÍFICAS (ANTES DE LAS DINÁMICAS)
# ============================================

@producto_bp.route('/categoria/<slug>')
def por_categoria(slug):
    """Productos por categoría"""
    try:
        supabase = get_supabase()
        
        categoria = supabase.table('categoria').select('*').eq('slug', slug).execute()
        if not categoria.data:
            flash('Categoría no encontrada', 'warning')
            return redirect(url_for('producto.index'))
        
        cat = categoria.data[0]
        
        prod_cat = supabase.table('producto_categoria')\
            .select('producto(*)')\
            .eq('id_categoria', cat['id_categoria'])\
            .execute()
        
        productos = []
        for item in prod_cat.data:
            if item.get('producto'):
                p = item['producto']
                if p.get('estado') == 'activo':
                    producto_obj = Producto(p)
                    producto_obj.get_variantes()
                    productos.append(producto_obj)
        
        return render_template('productos/categoria.html',
                             categoria=cat,
                             productos=productos)
    except Exception as e:
        logger.error(f'Error cargando productos por categoría: {str(e)}')
        logger.error(traceback.format_exc())
        flash('Error cargando productos', 'danger')
        return redirect(url_for('producto.index'))


@producto_bp.route('/buscar')
def buscar():
    """Búsqueda de productos (API)"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    
    if not query or len(query) < 2:
        return jsonify({'productos': []})
    
    try:
        result = Producto.search(query, page=1, per_page=limit)
        
        productos_data = []
        for producto in result['productos']:
            productos_data.append({
                'id_producto': producto.id,
                'nombre': producto.nombre,
                'precio_base': producto.precio_base,
                'imagen_url': producto.imagen_url,
                'url': url_for('producto.detalle', producto_id=producto.id)
            })
        
        return jsonify({'productos': productos_data})
    except Exception as e:
        logger.error(f'Error en búsqueda: {str(e)}')
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@producto_bp.route('/variante/<variante_id>')
def variante_detalle(variante_id):
    """Obtener detalles de una variante (API)"""
    try:
        variante = VarianteProducto.find_by_id(variante_id)
        if not variante:
            return jsonify({'error': 'Variante no encontrada'}), 404
        
        return jsonify({
            'id_variante': variante.id,
            'color': variante.color,
            'capacidad': variante.capacidad,
            'precio_extra': variante.precio_extra,
            'precio_total': variante.precio_total,
            'stock_disponible': variante.stock_disponible,
            'imagenes': variante.get_imagenes()
        })
    except Exception as e:
        logger.error(f'Error obteniendo variante: {str(e)}')
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# ============================================
# RUTA PARA OBTENER VARIANTE POR PRODUCTO
# ============================================

@producto_bp.route('/<producto_id>/variante')
def get_variante(producto_id):
    """Obtener una variante del producto (API)"""
    try:
        supabase = get_supabase()
        result = supabase.table('variante_producto')\
            .select('id_variante')\
            .eq('id_producto', producto_id)\
            .eq('activo', True)\
            .limit(1)\
            .execute()
        
        if result.data:
            return jsonify({'id_variante': result.data[0]['id_variante']})
        return jsonify({'id_variante': None}), 404
    except Exception as e:
        logger.error(f'Error obteniendo variante: {str(e)}')
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# ============================================
# RUTA DE DIAGNÓSTICO (DEBUG)
# ============================================

@producto_bp.route('/debug')
def debug():
    """Ruta de diagnóstico para verificar conexión y tablas"""
    try:
        supabase = get_supabase()
        
        # Probar tabla producto
        prod_result = supabase.table('producto').select('*').limit(1).execute()
        producto = prod_result.data[0] if prod_result.data else None
        
        # Probar tabla categoria
        cat_result = supabase.table('categoria').select('*').limit(1).execute()
        categoria = cat_result.data[0] if cat_result.data else None
        
        return jsonify({
            'status': 'ok',
            'producto': producto,
            'categoria': categoria,
            'producto_count': prod_result.count,
            'categoria_count': cat_result.count
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================
# RUTA DINÁMICA (SIEMPRE AL FINAL)
# ============================================

@producto_bp.route('/<producto_id>')
def detalle(producto_id):
    """Detalle de producto"""
    try:
        supabase = get_supabase()
        
        result = supabase.table('producto')\
            .select('*, variante_producto(*, imagen_producto(*))')\
            .eq('id_producto', producto_id)\
            .execute()
        
        if not result.data:
            abort(404)
        
        producto_data = result.data[0]
        producto = Producto(producto_data)
        
        categorias = supabase.table('producto_categoria')\
            .select('categoria(*)')\
            .eq('id_producto', producto_id)\
            .execute()
        
        producto.categorias = [item['categoria'] for item in categorias.data if item.get('categoria')]
        
        reseñas = producto.get_resenas()
        
        relacionados = []
        if producto.categorias:
            cat_id = producto.categorias[0]['id_categoria']
            relacionados_result = supabase.table('producto_categoria')\
                .select('producto(*)')\
                .eq('id_categoria', cat_id)\
                .neq('producto.id_producto', producto_id)\
                .limit(4)\
                .execute()
            
            relacionados = [Producto(item['producto']) for item in relacionados_result.data if item.get('producto')]
        
        return render_template('productos/detalle.html',
                             producto=producto,
                             variantes=producto.variantes,
                             categorias=producto.categorias,
                             reseñas=reseñas,
                             relacionados=relacionados)
    except Exception as e:
        logger.error(f'Error cargando detalle de producto: {str(e)}')
        logger.error(traceback.format_exc())
        abort(404)