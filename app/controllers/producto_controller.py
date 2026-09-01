"""
Controlador de Productos
"""
from flask import Blueprint, render_template, request, jsonify, abort, flash, redirect, url_for
from app.models.producto import Producto, VarianteProducto
from app.models.categoria import Categoria
from app.utils.supabase_client import get_supabase_service
import logging

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
        # Usar clave de servicio en todas las consultas
        categorias = Categoria.get_raices(use_service=True)
        result = Producto.search(
            query=search,
            categoria=categoria,
            page=page,
            per_page=per_page,
            solo_activos=True,
            use_service=True
        )
        
        for producto in result['productos']:
            producto.get_variantes(use_service=True)
        
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
        flash('Error cargando productos', 'danger')
        return render_template('productos/index.html', 
                             productos=[], 
                             categorias=[],
                             page=1)


@producto_bp.route('/categoria/<slug>')
def por_categoria(slug):
    """Productos por categoría"""
    try:
        supabase = get_supabase_service()  # Usar clave de servicio
        
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
                    producto_obj.get_variantes(use_service=True)
                    productos.append(producto_obj)
        
        return render_template('productos/categoria.html',
                             categoria=cat,
                             productos=productos)
    except Exception as e:
        logger.error(f'Error cargando productos por categoría: {str(e)}')
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
        result = Producto.search(query, page=1, per_page=limit, use_service=True)
        
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
        return jsonify({'error': str(e)}), 500


@producto_bp.route('/variante/<variante_id>')
def variante_detalle(variante_id):
    """Obtener detalles de una variante (API)"""
    try:
        variante = VarianteProducto.find_by_id(variante_id, use_service=True)
        if not variante:
            return jsonify({'error': 'Variante no encontrada'}), 404
        
        return jsonify({
            'id_variante': variante.id,
            'color': variante.color,
            'capacidad': variante.capacidad,
            'precio_extra': variante.precio_extra,
            'precio_total': variante.precio_total,
            'stock_disponible': variante.stock_disponible,
            'imagenes': variante.get_imagenes(use_service=True)
        })
    except Exception as e:
        logger.error(f'Error obteniendo variante: {str(e)}')
        return jsonify({'error': str(e)}), 500


@producto_bp.route('/<producto_id>/variante')
def get_variante(producto_id):
    """Obtener una variante del producto (API)"""
    try:
        supabase = get_supabase_service()
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
        return jsonify({'error': str(e)}), 500


@producto_bp.route('/<producto_id>')
def detalle(producto_id):
    """Detalle de producto"""
    try:
        supabase = get_supabase_service()
        
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
        
        reseñas = producto.get_resenas(use_service=True)
        
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
        abort(404)