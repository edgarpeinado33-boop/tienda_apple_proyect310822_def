"""
Controlador de Pedidos
Maneja la creación, visualización y gestión de pedidos
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.pedido import Pedido, LineaPedido
from app.models.carrito import Carrito
from app.utils.supabase_client import get_supabase
from app.utils.decorators import require_roles
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

pedido_bp = Blueprint('pedido', __name__)


@pedido_bp.route('/')
@login_required
def index():
    try:
        supabase = get_supabase()
        estado = request.args.get('estado', '')
        query = supabase.table('pedido')\
            .select('*, factura(*), envio(*)')\
            .eq('id_usuario', current_user.id)
        if estado:
            query = query.eq('estado', estado)
        result = query.order('fecha_pedido', desc=True).execute()
        pedidos = [Pedido(item) for item in result.data]
        estados_count = {}
        for p in pedidos:
            estados_count[p.estado] = estados_count.get(p.estado, 0) + 1
        return render_template('pedidos/index.html', 
                             pedidos=pedidos,
                             estado_seleccionado=estado,
                             estados_count=estados_count)
    except Exception as e:
        logger.error(f'Error cargando pedidos: {str(e)}')
        flash('Error cargando tus pedidos', 'danger')
        return render_template('pedidos/index.html', 
                             pedidos=[], 
                             estado_seleccionado='',
                             estados_count={})


@pedido_bp.route('/detalle/<pedido_id>')
@login_required
def detalle(pedido_id):
    try:
        supabase = get_supabase()
        result = supabase.table('pedido')\
            .select('*, usuario(*), direccion_envio(*)')\
            .eq('id_pedido', pedido_id)\
            .execute()
        if not result.data:
            flash('Pedido no encontrado', 'warning')
            return redirect(url_for('pedido.index'))
        pedido_data = result.data[0]
        if pedido_data['id_usuario'] != current_user.id and not current_user.is_admin:
            flash('No tienes permiso para ver este pedido', 'danger')
            return redirect(url_for('pedido.index'))
        pedido = Pedido(pedido_data)
        pedido.get_lineas()
        return render_template('pedidos/detalle.html', pedido=pedido)
    except Exception as e:
        logger.error(f'Error cargando detalle del pedido: {str(e)}')
        flash('Error cargando el detalle del pedido', 'danger')
        return redirect(url_for('pedido.index'))


@pedido_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    try:
        supabase = get_supabase()
        carrito = Carrito.get_or_create_cart(current_user.id)
        carrito.cargar_lineas()
        carrito.recalcular_totales()
        if not carrito.lineas or carrito.total_items == 0:
            flash('El carrito está vacío', 'warning')
            return redirect(url_for('carrito.ver_carrito'))
        direcciones = supabase.table('direccion_envio')\
            .select('*')\
            .eq('id_usuario', current_user.id)\
            .eq('activa', True)\
            .order('predeterminada', desc=True)\
            .execute()
        if not direcciones.data:
            flash('Debes agregar una dirección de envío primero', 'warning')
            return redirect(url_for('auth.profile'))
        if request.method == 'POST':
            direccion_id = request.form.get('direccion_id')
            metodo_pago = request.form.get('metodo_pago', 'tarjeta')
            notas = request.form.get('notas', '')
            if not direccion_id:
                flash('Selecciona una dirección de envío', 'warning')
                return render_template('pedidos/crear.html', 
                                     carrito=carrito, 
                                     direcciones=direcciones.data)
            direccion = next((d for d in direcciones.data if d['id_direccion'] == direccion_id), None)
            if not direccion:
                flash('Dirección no válida', 'warning')
                return render_template('pedidos/crear.html', 
                                     carrito=carrito, 
                                     direcciones=direcciones.data)
            try:
                pedido = Pedido.create_from_cart(
                    user_id=current_user.id,
                    direccion_id=direccion_id,
                    carrito=carrito,
                    metodo_pago=metodo_pago,
                    notas=notas
                )
            except Exception as e:
                error_msg = str(e)
                if 'updated_at' in error_msg:
                    flash('Error en la base de datos: el administrador debe agregar la columna "updated_at" o eliminar los triggers.', 'danger')
                else:
                    flash(f'Error al crear el pedido: {error_msg}', 'danger')
                return render_template('pedidos/crear.html', 
                                     carrito=carrito, 
                                     direcciones=direcciones.data)
            if pedido:
                supabase.table('carrito')\
                    .update({'estado': 'convertido'})\
                    .eq('id_carrito', carrito.id)\
                    .execute()
                flash('¡Pedido creado exitosamente!', 'success')
                return redirect(url_for('pedido.detalle', pedido_id=pedido.id))
            else:
                flash('Error al crear el pedido', 'danger')
        return render_template('pedidos/crear.html', 
                             carrito=carrito, 
                             direcciones=direcciones.data)
    except Exception as e:
        logger.error(f'Error creando pedido: {str(e)}')
        flash('Error al procesar el pedido', 'danger')
        return redirect(url_for('carrito.ver_carrito'))


@pedido_bp.route('/cancelar/<pedido_id>', methods=['POST'])
@login_required
def cancelar(pedido_id):
    try:
        supabase = get_supabase()
        pedido = supabase.table('pedido')\
            .select('*')\
            .eq('id_pedido', pedido_id)\
            .eq('id_usuario', current_user.id)\
            .execute()
        if not pedido.data:
            flash('Pedido no encontrado', 'warning')
            return redirect(url_for('pedido.index'))
        pedido_data = pedido.data[0]
        if pedido_data['estado'] not in ['pendiente', 'confirmado']:
            flash('No se puede cancelar este pedido', 'warning')
            return redirect(url_for('pedido.detalle', pedido_id=pedido_id))
        motivo = request.form.get('motivo', 'Cancelado por el usuario')
        supabase.table('pedido')\
            .update({
                'estado': 'cancelado',
                'fecha_cancelacion': datetime.now().isoformat(),
                'motivo_cancelacion': motivo
            })\
            .eq('id_pedido', pedido_id)\
            .execute()
        supabase.table('bitacora_auditoria').insert({
            'id_usuario': current_user.id,
            'accion': 'CANCELAR_PEDIDO',
            'tabla_afectada': 'pedido',
            'registro_afectado': pedido_id,
            'valor_nuevo': 'cancelado',
            'modulo': 'pedidos'
        }).execute()
        flash('Pedido cancelado correctamente', 'info')
        return redirect(url_for('pedido.detalle', pedido_id=pedido_id))
    except Exception as e:
        logger.error(f'Error cancelando pedido: {str(e)}')
        flash('Error cancelando el pedido', 'danger')
        return redirect(url_for('pedido.index'))


@pedido_bp.route('/confirmar-recibido/<pedido_id>', methods=['POST'])
@login_required
def confirmar_recibido(pedido_id):
    try:
        supabase = get_supabase()
        pedido = supabase.table('pedido')\
            .select('*')\
            .eq('id_pedido', pedido_id)\
            .eq('id_usuario', current_user.id)\
            .execute()
        if not pedido.data:
            flash('Pedido no encontrado', 'warning')
            return redirect(url_for('pedido.index'))
        pedido_data = pedido.data[0]
        if pedido_data['estado'] != 'enviado':
            flash('El pedido no está en estado de envío', 'warning')
            return redirect(url_for('pedido.detalle', pedido_id=pedido_id))
        supabase.table('pedido')\
            .update({'estado': 'entregado'})\
            .eq('id_pedido', pedido_id)\
            .execute()
        flash('¡Pedido confirmado como recibido!', 'success')
        return redirect(url_for('pedido.detalle', pedido_id=pedido_id))
    except Exception as e:
        logger.error(f'Error confirmando pedido: {str(e)}')
        flash('Error confirmando el pedido', 'danger')
        return redirect(url_for('pedido.index'))


# --- ADMIN ---

@pedido_bp.route('/admin')
@login_required
@require_roles('SUPER_ADMIN', 'ADMIN_PEDIDOS', 'ADMIN_TIENDA')
def admin_index():
    try:
        supabase = get_supabase()
        estado = request.args.get('estado', '')
        page = request.args.get('page', 1, type=int)
        per_page = 20
        query = supabase.table('pedido')\
            .select('*, usuario(nombre_completo, email)')\
            .order('fecha_pedido', desc=True)
        if estado:
            query = query.eq('estado', estado)
        start = (page - 1) * per_page
        query = query.range(start, start + per_page - 1)
        result = query.execute()
        count_query = supabase.table('pedido').select('*', count='exact')
        if estado:
            count_query = count_query.eq('estado', estado)
        count_result = count_query.execute()
        return render_template('pedidos/admin_index.html',
                             pedidos=result.data,
                             estado_seleccionado=estado,
                             page=page,
                             total=count_result.count,
                             per_page=per_page)
    except Exception as e:
        logger.error(f'Error cargando administración de pedidos: {str(e)}')
        flash('Error cargando la administración de pedidos', 'danger')
        return render_template('pedidos/admin_index.html', pedidos=[])


@pedido_bp.route('/admin/actualizar-estado/<pedido_id>', methods=['POST'])
@login_required
@require_roles('SUPER_ADMIN', 'ADMIN_PEDIDOS', 'ADMIN_TIENDA')
def admin_actualizar_estado(pedido_id):
    try:
        supabase = get_supabase()
        nuevo_estado = request.form.get('estado')
        if not nuevo_estado:
            flash('Estado no especificado', 'warning')
            return redirect(request.referrer or url_for('pedido.admin_index'))
        estados_validos = ['pendiente', 'confirmado', 'procesando', 'enviado', 'entregado', 'cancelado', 'devuelto']
        if nuevo_estado not in estados_validos:
            flash('Estado inválido', 'danger')
            return redirect(request.referrer or url_for('pedido.admin_index'))
        supabase.table('pedido')\
            .update({'estado': nuevo_estado})\
            .eq('id_pedido', pedido_id)\
            .execute()
        supabase.table('bitacora_auditoria').insert({
            'id_usuario': current_user.id,
            'accion': 'ACTUALIZAR_ESTADO_PEDIDO',
            'tabla_afectada': 'pedido',
            'registro_afectado': pedido_id,
            'valor_nuevo': nuevo_estado,
            'modulo': 'pedidos'
        }).execute()
        flash('Estado del pedido actualizado', 'success')
    except Exception as e:
        logger.error(f'Error actualizando estado del pedido: {str(e)}')
        flash('Error actualizando el estado del pedido', 'danger')
    return redirect(request.referrer or url_for('pedido.admin_index'))


# ============= CONFIRMAR Y FACTURA =============

@pedido_bp.route('/admin/confirmar/<pedido_id>', methods=['POST'])
@login_required
@require_roles('SUPER_ADMIN', 'ADMIN_PEDIDOS', 'ADMIN_TIENDA')
def admin_confirmar_pedido(pedido_id):
    try:
        supabase = get_supabase()
        pedido = supabase.table('pedido')\
            .select('*, usuario(nombre_completo, email, telefono), direccion_envio(*)')\
            .eq('id_pedido', pedido_id)\
            .execute()
        if not pedido.data:
            flash('Pedido no encontrado', 'danger')
            return redirect(url_for('pedido.admin_index'))
        pedido_data = pedido.data[0]
        if pedido_data['estado'] != 'pendiente':
            flash('Este pedido ya no está pendiente', 'warning')
            return redirect(url_for('pedido.detalle', pedido_id=pedido_id))
        supabase.table('pedido')\
            .update({
                'estado': 'confirmado',
                'fecha_procesamiento': datetime.now().isoformat()
            })\
            .eq('id_pedido', pedido_id)\
            .execute()
        supabase.table('bitacora_auditoria').insert({
            'id_usuario': current_user.id,
            'accion': 'CONFIRMAR_PEDIDO',
            'tabla_afectada': 'pedido',
            'registro_afectado': pedido_id,
            'valor_nuevo': 'confirmado',
            'modulo': 'pedidos'
        }).execute()
        flash('Pedido confirmado exitosamente', 'success')
        return redirect(url_for('pedido.factura', pedido_id=pedido_id))
    except Exception as e:
        logger.error(f'Error confirmando pedido: {str(e)}')
        flash('Error al confirmar el pedido', 'danger')
        return redirect(url_for('pedido.admin_index'))


@pedido_bp.route('/factura/<pedido_id>')
@login_required
def factura(pedido_id):
    try:
        supabase = get_supabase()
        result = supabase.table('pedido')\
            .select('*, usuario(*), direccion_envio(*), linea_pedido(*, variante_producto(*, producto(*)))')\
            .eq('id_pedido', pedido_id)\
            .execute()
        if not result.data:
            flash('Pedido no encontrado', 'danger')
            return redirect(url_for('pedido.index'))
        pedido_data = result.data[0]
        if pedido_data['id_usuario'] != current_user.id and not current_user.is_admin:
            flash('No tienes permiso para ver esta factura', 'danger')
            return redirect(url_for('pedido.index'))
        pedido = Pedido(pedido_data)
        pedido.get_lineas()
        empresa = {
            'nombre': 'Tienda Apple',
            'direccion': 'Calle Principal 1, 28001 Madrid',
            'telefono': '+34 900 123 456',
            'email': 'info@tiendaapple.com',
            'cif': 'B-12345678'
        }
        return render_template('pedidos/factura.html', 
                             pedido=pedido, 
                             empresa=empresa,
                             now=datetime.now())
    except Exception as e:
        logger.error(f'Error cargando factura: {str(e)}')
        flash('Error al cargar la factura', 'danger')
        return redirect(url_for('pedido.index'))