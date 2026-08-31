"""
Controlador de Carrito de Compras
Maneja la gestión del carrito, agregar, eliminar, actualizar productos
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from flask_login import login_required, current_user
from app.models.carrito import Carrito
from app.models.producto import VarianteProducto
from app.utils.supabase_client import get_supabase
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

carrito_bp = Blueprint('carrito', __name__)


@carrito_bp.route('/')
@login_required
def ver_carrito():
    """Ver carrito de compras"""
    try:
        carrito = Carrito.get_or_create_cart(current_user.id)
        
        # Forzar recálculo y carga de líneas
        carrito.cargar_lineas()
        carrito.recalcular_totales()
        carrito.cargar_lineas()  # Recargar con los nuevos valores
        
        # Obtener direcciones del usuario para el checkout
        supabase = get_supabase()
        direcciones = supabase.table('direccion_envio')\
            .select('*')\
            .eq('id_usuario', current_user.id)\
            .eq('activa', True)\
            .order('predeterminada', desc=True)\
            .execute()
        
        return render_template('carrito/carrito.html', 
                             carrito=carrito,
                             direcciones=direcciones.data)
    except Exception as e:
        logger.error(f'Error cargando carrito: {str(e)}')
        flash('Error cargando el carrito', 'danger')
        return render_template('carrito/carrito.html', carrito=None)


@carrito_bp.route('/agregar', methods=['POST'])
@login_required
def agregar():
    """
    Agregar producto al carrito
    Tanto administradores como clientes pueden agregar productos
    """
    try:
        variante_id = request.form.get('variante_id')
        cantidad = int(request.form.get('cantidad', 1))
        producto_id = request.form.get('producto_id')
        
        # Si no hay variante, buscar la primera variante del producto
        if not variante_id and producto_id:
            supabase = get_supabase()
            variantes = supabase.table('variante_producto')\
                .select('id_variante')\
                .eq('id_producto', producto_id)\
                .eq('activo', True)\
                .limit(1)\
                .execute()
            if variantes.data:
                variante_id = variantes.data[0]['id_variante']
                logger.info(f'Variante encontrada para producto {producto_id}: {variante_id}')
        
        # Verificar que tenemos una variante
        if not variante_id:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Producto no disponible - No tiene variantes activas'}), 400
            flash('Producto no disponible', 'warning')
            return redirect(request.referrer or url_for('producto.index'))
        
        # Verificar stock
        variante = VarianteProducto.find_by_id(variante_id)
        if not variante:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Producto no encontrado'}), 404
            flash('Producto no encontrado', 'danger')
            return redirect(request.referrer or url_for('producto.index'))
        
        if not variante.has_stock(cantidad):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': f'Stock insuficiente. Disponible: {variante.stock_disponible}'}), 400
            flash(f'Stock insuficiente. Disponible: {variante.stock_disponible}', 'warning')
            return redirect(request.referrer or url_for('producto.index'))
        
        # Agregar al carrito
        carrito = Carrito.get_or_create_cart(current_user.id)
        linea = carrito.agregar_producto(variante_id, cantidad)
        
        logger.info(f'Producto agregado al carrito - Usuario: {current_user.id}, Variante: {variante_id}, Cantidad: {cantidad}')
        
        # Si es AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': 'Producto agregado al carrito',
                'carrito': {
                    'total_items': carrito.total_items,
                    'subtotal': float(carrito.subtotal),
                    'total': float(carrito.total)
                }
            })
        
        flash('Producto agregado al carrito', 'success')
        return redirect(request.referrer or url_for('carrito.ver_carrito'))
    
    except ValueError as e:
        logger.error(f'Error de valor: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Cantidad inválida'}), 400
        flash('Cantidad inválida', 'warning')
        return redirect(request.referrer or url_for('producto.index'))
    
    except Exception as e:
        logger.error(f'Error agregando al carrito: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': str(e)}), 400
        flash('Error agregando producto al carrito', 'danger')
        return redirect(request.referrer or url_for('producto.index'))


@carrito_bp.route('/actualizar/<linea_id>', methods=['POST'])
@login_required
def actualizar(linea_id):
    """Actualizar cantidad en el carrito"""
    try:
        cantidad = int(request.form.get('cantidad', 1))
        
        if cantidad <= 0:
            return eliminar(linea_id)
        
        carrito = Carrito.get_or_create_cart(current_user.id)
        resultado = carrito.actualizar_cantidad(linea_id, cantidad)
        
        if resultado:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'carrito': {
                        'total_items': carrito.total_items,
                        'subtotal': float(carrito.subtotal),
                        'descuentos': float(carrito.descuentos),
                        'total': float(carrito.total)
                    }
                })
            flash('Carrito actualizado', 'success')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Error actualizando carrito'}), 400
            flash('Error actualizando el carrito', 'danger')
        
        return redirect(url_for('carrito.ver_carrito'))
    except Exception as e:
        logger.error(f'Error actualizando carrito: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': str(e)}), 400
        flash('Error actualizando el carrito', 'danger')
        return redirect(url_for('carrito.ver_carrito'))


@carrito_bp.route('/eliminar/<linea_id>', methods=['POST'])
@login_required
def eliminar(linea_id):
    """Eliminar producto del carrito"""
    try:
        carrito = Carrito.get_or_create_cart(current_user.id)
        resultado = carrito.eliminar_producto(linea_id)
        
        if resultado:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'carrito': {
                        'total_items': carrito.total_items,
                        'subtotal': float(carrito.subtotal),
                        'descuentos': float(carrito.descuentos),
                        'total': float(carrito.total)
                    }
                })
            flash('Producto eliminado del carrito', 'success')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Error eliminando producto'}), 400
            flash('Error eliminando producto del carrito', 'danger')
        
        return redirect(url_for('carrito.ver_carrito'))
    except Exception as e:
        logger.error(f'Error eliminando del carrito: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': str(e)}), 400
        flash('Error eliminando producto del carrito', 'danger')
        return redirect(url_for('carrito.ver_carrito'))


@carrito_bp.route('/vaciar', methods=['POST'])
@login_required
def vaciar():
    """Vaciar carrito"""
    try:
        carrito = Carrito.get_or_create_cart(current_user.id)
        carrito.vaciar()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': 'Carrito vaciado'
            })
        
        flash('Carrito vaciado', 'info')
    except Exception as e:
        logger.error(f'Error vaciando carrito: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': str(e)}), 400
        flash('Error vaciando el carrito', 'danger')
    
    return redirect(url_for('carrito.ver_carrito'))


@carrito_bp.route('/aplicar-cupon', methods=['POST'])
@login_required
def aplicar_cupon():
    """Aplicar cupón de descuento"""
    try:
        codigo = request.form.get('codigo', '').strip().upper()
        
        if not codigo:
            flash('Ingresa un código de cupón', 'warning')
            return redirect(url_for('carrito.ver_carrito'))
        
        carrito = Carrito.get_or_create_cart(current_user.id)
        resultado = carrito.aplicar_cupon(codigo)
        
        if resultado:
            flash(f'¡Cupón aplicado! Descuento de ${resultado["descuento"]:.2f}', 'success')
        else:
            flash('Cupón inválido o expirado', 'danger')
    except Exception as e:
        logger.error(f'Error aplicando cupón: {str(e)}')
        flash(f'Error aplicando cupón: {str(e)}', 'danger')
    
    return redirect(url_for('carrito.ver_carrito'))


@carrito_bp.route('/quitar-cupon', methods=['POST'])
@login_required
def quitar_cupon():
    """Quitar cupón aplicado"""
    try:
        carrito = Carrito.get_or_create_cart(current_user.id)
        carrito.eliminar_cupon()
        
        flash('Cupón eliminado', 'info')
    except Exception as e:
        logger.error(f'Error eliminando cupón: {str(e)}')
        flash('Error eliminando cupón', 'danger')
    
    return redirect(url_for('carrito.ver_carrito'))


@carrito_bp.route('/contar')
@login_required
def contar():
    """Contar items en el carrito (API)"""
    try:
        carrito = Carrito.get_or_create_cart(current_user.id)
        return jsonify({
            'total_items': carrito.total_items,
            'subtotal': float(carrito.subtotal),
            'total': float(carrito.total)
        })
    except Exception as e:
        logger.error(f'Error contando items del carrito: {str(e)}')
        return jsonify({'total_items': 0, 'subtotal': 0, 'total': 0}), 500


@carrito_bp.route('/resumen')
@login_required
def resumen():
    """Obtener resumen del carrito (API)"""
    try:
        carrito = Carrito.get_or_create_cart(current_user.id)
        
        lineas = []
        for linea in carrito.lineas:
            variante = VarianteProducto.find_by_id(linea['id_variante'])
            producto_nombre = 'Producto'
            if variante:
                producto = variante.get_producto()
                if producto:
                    producto_nombre = producto.nombre
            
            lineas.append({
                'id_linea': linea['id_linea_carrito'],
                'nombre': producto_nombre,
                'cantidad': linea['cantidad'],
                'precio_unitario': float(linea['precio_unitario']),
                'total': float(linea['cantidad']) * float(linea['precio_unitario'])
            })
        
        return jsonify({
            'total_items': carrito.total_items,
            'subtotal': float(carrito.subtotal),
            'descuentos': float(carrito.descuentos),
            'total': float(carrito.total),
            'lineas': lineas
        })
    except Exception as e:
        logger.error(f'Error obteniendo resumen del carrito: {str(e)}')
        return jsonify({'error': str(e)}), 500