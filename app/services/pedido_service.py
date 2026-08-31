"""
Servicio de Pedido
Maneja toda la lógica de negocio relacionada con pedidos
"""
from app.utils.supabase_client import get_supabase, get_supabase_service
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PedidoService:
    """Servicio para operaciones con pedidos"""
    
    @staticmethod
    def get_by_id(pedido_id):
        """Obtener pedido por ID con todos sus detalles"""
        try:
            supabase = get_supabase()
            result = supabase.table('PEDIDO')\
                .select('*, LINEA_PEDIDO(*, VARIANTE_PRODUCTO(*, PRODUCTO(*))), ENVIO(*), FACTURA(*), TRANSACCION_PAGO(*)')\
                .eq('id_pedido', pedido_id)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f'Error obteniendo pedido: {str(e)}')
            raise
    
    @staticmethod
    def get_by_usuario(user_id, estado=None, page=1, per_page=10):
        """Obtener pedidos de un usuario con paginación"""
        try:
            supabase = get_supabase()
            start = (page - 1) * per_page
            
            query = supabase.table('PEDIDO')\
                .select('*, FACTURA(*), ENVIO(*)')\
                .eq('id_usuario', user_id)
            
            if estado:
                query = query.eq('estado', estado)
            
            query = query.range(start, start + per_page - 1).order('fecha_pedido', desc=True)
            result = query.execute()
            
            # Contar total
            count_query = supabase.table('PEDIDO').select('*', count='exact').eq('id_usuario', user_id)
            if estado:
                count_query = count_query.eq('estado', estado)
            count_result = count_query.execute()
            
            return {
                'pedidos': result.data,
                'total': count_result.count,
                'page': page,
                'per_page': per_page,
                'total_pages': (count_result.count + per_page - 1) // per_page
            }
        except Exception as e:
            logger.error(f'Error obteniendo pedidos del usuario: {str(e)}')
            raise
    
    @staticmethod
    def get_all(estado=None, page=1, per_page=20, search=None):
        """Obtener todos los pedidos (admin) con paginación y filtros"""
        try:
            supabase = get_supabase_service()
            start = (page - 1) * per_page
            
            query = supabase.table('PEDIDO')\
                .select('*, USUARIO(nombre_completo, email)')
            
            if estado:
                query = query.eq('estado', estado)
            
            if search:
                # Buscar por nombre de usuario o email
                query = query.or_(f"USUARIO.nombre_completo.ilike.%{search}%,USUARIO.email.ilike.%{search}%")
            
            query = query.range(start, start + per_page - 1).order('fecha_pedido', desc=True)
            result = query.execute()
            
            # Contar total
            count_query = supabase.table('PEDIDO').select('*', count='exact')
            if estado:
                count_query = count_query.eq('estado', estado)
            count_result = count_query.execute()
            
            return {
                'pedidos': result.data,
                'total': count_result.count,
                'page': page,
                'per_page': per_page,
                'total_pages': (count_result.count + per_page - 1) // per_page
            }
        except Exception as e:
            logger.error(f'Error obteniendo todos los pedidos: {str(e)}')
            raise
    
    @staticmethod
    def create_from_cart(user_id, direccion_id, carrito, notas=None, cupon_id=None):
        """Crear pedido desde el carrito"""
        try:
            supabase = get_supabase()
            
            # Calcular impuestos (21% IVA)
            impuestos = carrito['subtotal'] * 0.21
            gastos_envio = 0  # Calcular según ubicación
            
            total = carrito['subtotal'] + impuestos + gastos_envio - carrito['descuentos']
            
            # Crear pedido
            pedido_data = {
                'id_usuario': user_id,
                'id_direccion_envio': direccion_id,
                'subtotal': carrito['subtotal'],
                'impuestos': impuestos,
                'gastos_envio': gastos_envio,
                'descuento_total': carrito['descuentos'],
                'total': total,
                'estado': 'pendiente',
                'notas': notas or ''
            }
            
            if cupon_id:
                pedido_data['id_cupon_aplicado'] = cupon_id
            
            result = supabase.table('PEDIDO')\
                .insert(pedido_data)\
                .execute()
            
            if not result.data:
                raise Exception('Error creando pedido')
            
            pedido_id = result.data[0]['id_pedido']
            
            # Crear líneas del pedido desde el carrito
            for linea in carrito['lineas']:
                linea_pedido = {
                    'id_pedido': pedido_id,
                    'id_variante': linea['id_variante'],
                    'cantidad': linea['cantidad'],
                    'precio_unitario': linea['precio_unitario'],
                    'descuento_aplicado': linea.get('descuento_aplicado', 0),
                    'total_linea': linea['cantidad'] * linea['precio_unitario']
                }
                supabase.table('LINEA_PEDIDO')\
                    .insert(linea_pedido)\
                    .execute()
                
                # Actualizar stock
                PedidoService.actualizar_stock_linea(linea['id_variante'], -linea['cantidad'])
            
            return PedidoService.get_by_id(pedido_id)
        except Exception as e:
            logger.error(f'Error creando pedido desde carrito: {str(e)}')
            raise
    
    @staticmethod
    def actualizar_stock_linea(variante_id, cantidad):
        """Actualizar stock de una variante"""
        try:
            supabase = get_supabase_service()
            
            result = supabase.table('VARIANTE_PRODUCTO')\
                .update({'stock_disponible': supabase.raw(f'stock_disponible + {cantidad}')})\
                .eq('id_variante', variante_id)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f'Error actualizando stock: {str(e)}')
            raise
    
    @staticmethod
    def update_status(pedido_id, nuevo_estado, motivo=None):
        """Actualizar estado del pedido"""
        try:
            supabase = get_supabase_service()
            
            # Obtener pedido actual
            pedido = PedidoService.get_by_id(pedido_id)
            if not pedido:
                raise Exception('Pedido no encontrado')
            
            # Validar transición de estado
            transiciones_validas = {
                'pendiente': ['confirmado', 'cancelado'],
                'confirmado': ['procesando', 'cancelado'],
                'procesando': ['enviado', 'cancelado'],
                'enviado': ['entregado', 'devuelto'],
                'entregado': ['devuelto'],
                'cancelado': [],
                'devuelto': []
            }
            
            estado_actual = pedido['estado']
            if nuevo_estado not in transiciones_validas.get(estado_actual, []):
                raise Exception(f'No se puede cambiar de {estado_actual} a {nuevo_estado}')
            
            # Actualizar estado
            update_data = {
                'estado': nuevo_estado,
                'updated_at': datetime.now().isoformat()
            }
            
            if nuevo_estado == 'cancelado' and motivo:
                update_data['fecha_cancelacion'] = datetime.now().isoformat()
                update_data['motivo_cancelacion'] = motivo
            
            if nuevo_estado == 'enviado':
                update_data['fecha_envio_real'] = datetime.now().isoformat()
            
            if nuevo_estado == 'entregado':
                update_data['fecha_entrega_estimada'] = datetime.now().date().isoformat()
            
            result = supabase.table('PEDIDO')\
                .update(update_data)\
                .eq('id_pedido', pedido_id)\
                .execute()
            
            if result.data:
                # Registrar en auditoría
                PedidoService.registrar_auditoria(pedido_id, estado_actual, nuevo_estado)
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f'Error actualizando estado del pedido: {str(e)}')
            raise
    
    @staticmethod
    def cancelar(pedido_id, motivo, usuario_id):
        """Cancelar pedido"""
        try:
            # Verificar que se puede cancelar
            pedido = PedidoService.get_by_id(pedido_id)
            if not pedido:
                raise Exception('Pedido no encontrado')
            
            if pedido['estado'] not in ['pendiente', 'confirmado']:
                raise Exception('No se puede cancelar este pedido')
            
            # Actualizar estado
            return PedidoService.update_status(pedido_id, 'cancelado', motivo)
        except Exception as e:
            logger.error(f'Error cancelando pedido: {str(e)}')
            raise
    
    @staticmethod
    def registrar_auditoria(pedido_id, estado_anterior, estado_nuevo):
        """Registrar cambio de estado en auditoría"""
        try:
            supabase = get_supabase_service()
            
            supabase.table('BITACORA_AUDITORIA').insert({
                'tabla_afectada': 'PEDIDO',
                'registro_afectado': pedido_id,
                'accion': 'CAMBIO_ESTADO',
                'valor_anterior': estado_anterior,
                'valor_nuevo': estado_nuevo,
                'modulo': 'pedidos',
                'severidad': 'info'
            }).execute()
            
            return True
        except Exception as e:
            logger.error(f'Error registrando auditoría: {str(e)}')
            return False
    
    @staticmethod
    def get_estadisticas():
        """Obtener estadísticas de pedidos"""
        try:
            supabase = get_supabase_service()
            
            # Total pedidos
            total = supabase.table('PEDIDO').select('*', count='exact').execute()
            
            # Por estado
            estados = ['pendiente', 'confirmado', 'procesando', 'enviado', 'entregado', 'cancelado', 'devuelto']
            stats = {}
            
            for estado in estados:
                result = supabase.table('PEDIDO')\
                    .select('*', count='exact')\
                    .eq('estado', estado)\
                    .execute()
                stats[estado] = result.count
            
            # Ventas totales
            ventas = supabase.table('PEDIDO')\
                .select('total')\
                .not_.eq('estado', 'cancelado')\
                .execute()
            
            total_ventas = sum(float(p['total']) for p in ventas.data)
            
            # Ventas del día
            hoy = datetime.now().date().isoformat()
            ventas_hoy = supabase.table('PEDIDO')\
                .select('total')\
                .gte('fecha_pedido', hoy)\
                .not_.eq('estado', 'cancelado')\
                .execute()
            
            total_ventas_hoy = sum(float(p['total']) for p in ventas_hoy.data)
            
            # Ventas del mes
            inicio_mes = datetime.now().replace(day=1).date().isoformat()
            ventas_mes = supabase.table('PEDIDO')\
                .select('total')\
                .gte('fecha_pedido', inicio_mes)\
                .not_.eq('estado', 'cancelado')\
                .execute()
            
            total_ventas_mes = sum(float(p['total']) for p in ventas_mes.data)
            
            # Pedidos pendientes (urgentes - más de 3 días)
            fecha_limite = (datetime.now() - timedelta(days=3)).isoformat()
            urgentes = supabase.table('PEDIDO')\
                .select('*', count='exact')\
                .eq('estado', 'pendiente')\
                .lt('fecha_pedido', fecha_limite)\
                .execute()
            
            return {
                'total': total.count,
                'por_estado': stats,
                'total_ventas': total_ventas,
                'ventas_hoy': total_ventas_hoy,
                'ventas_mes': total_ventas_mes,
                'pedidos_urgentes': urgentes.count,
                'ventas_promedio': total_ventas / max(total.count, 1)
            }
        except Exception as e:
            logger.error(f'Error obteniendo estadísticas: {str(e)}')
            raise
    
    @staticmethod
    def get_productos_mas_vendidos(limit=5, dias=30):
        """Obtener productos más vendidos en los últimos días"""
        try:
            supabase = get_supabase_service()
            
            fecha_limite = (datetime.now() - timedelta(days=dias)).isoformat()
            
            # Obtener líneas de pedido
            result = supabase.table('LINEA_PEDIDO')\
                .select('id_variante, cantidad')\
                .gte('created_at', fecha_limite)\
                .execute()
            
            # Contar por variante
            ventas_por_variante = {}
            for item in result.data:
                variante_id = item['id_variante']
                ventas_por_variante[variante_id] = ventas_por_variante.get(variante_id, 0) + item['cantidad']
            
            # Ordenar y obtener top
            top_variantes = sorted(ventas_por_variante.items(), key=lambda x: x[1], reverse=True)[:limit]
            
            productos = []
            for variante_id, cantidad in top_variantes:
                variante = supabase.table('VARIANTE_PRODUCTO')\
                    .select('*, PRODUCTO(nombre)')\
                    .eq('id_variante', variante_id)\
                    .execute()
                
                if variante.data:
                    productos.append({
                        'variante_id': variante_id,
                        'nombre': variante.data[0]['PRODUCTO']['nombre'],
                        'variante': variante.data[0].get('color') or variante.data[0].get('capacidad') or '',
                        'cantidad': cantidad
                    })
            
            return productos
        except Exception as e:
            logger.error(f'Error obteniendo productos más vendidos: {str(e)}')
            raise