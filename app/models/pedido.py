"""
Modelo de Pedido
"""
from app.utils.supabase_client import get_supabase
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Pedido:
    """Modelo de Pedido"""
    
    def __init__(self, data=None):
        if data:
            self.id = data.get('id_pedido')
            self.id_usuario = data.get('id_usuario')
            self.id_direccion_envio = data.get('id_direccion_envio')
            self.fecha_pedido = data.get('fecha_pedido')
            self.estado = data.get('estado', 'pendiente')
            self.subtotal = float(data.get('subtotal', 0))
            self.impuestos = float(data.get('impuestos', 0))
            self.gastos_envio = float(data.get('gastos_envio', 0))
            self.descuento_total = float(data.get('descuento_total', 0))
            self.total = float(data.get('total', 0))
            self.direccion_envio_texto = data.get('direccion_envio_texto')
            self.notas = data.get('notas')
            self.metodo_pedido = data.get('metodo_pedido')
            self.id_cupon_aplicado = data.get('id_cupon_aplicado')
            self.fecha_procesamiento = data.get('fecha_procesamiento')
            self.fecha_envio_real = data.get('fecha_envio_real')
            self.fecha_entrega_estimada = data.get('fecha_entrega_estimada')
            self.fecha_cancelacion = data.get('fecha_cancelacion')
            self.motivo_cancelacion = data.get('motivo_cancelacion')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
            self.lineas = []
            self.envio = None
            self.factura = None
            self.usuario = data.get('usuario') if data else None
            self.direccion_envio = data.get('direccion_envio') if data else None
    
    def get_lineas(self):
        if self.lineas:
            return self.lineas
        try:
            supabase = get_supabase()
            result = supabase.table('linea_pedido')\
                .select('*, variante_producto(*, producto(*))')\
                .eq('id_pedido', self.id)\
                .execute()
            self.lineas = []
            for item in result.data:
                linea = LineaPedido(item)
                if 'variante_producto' in item and item['variante_producto']:
                    from app.models.producto import VarianteProducto, Producto
                    variante_data = item['variante_producto']
                    if 'producto' in variante_data and variante_data['producto']:
                        producto_obj = Producto(variante_data['producto'])
                        variante_obj = VarianteProducto(variante_data)
                        variante_obj._producto = producto_obj
                        linea.variante = variante_obj
                    else:
                        linea.variante = VarianteProducto(variante_data)
                self.lineas.append(linea)
            return self.lineas
        except Exception as e:
            logger.error(f'Error obteniendo líneas del pedido: {str(e)}')
            self.lineas = []
            return self.lineas
    
    def get_envio(self):
        if self.envio:
            return self.envio
        try:
            supabase = get_supabase()
            result = supabase.table('envio')\
                .select('*')\
                .eq('id_pedido', self.id)\
                .execute()
            if result.data:
                self.envio = result.data[0]
                return self.envio
            return None
        except Exception as e:
            logger.error(f'Error obteniendo envío: {str(e)}')
            return None
    
    def get_factura(self):
        if self.factura:
            return self.factura
        try:
            supabase = get_supabase()
            result = supabase.table('factura')\
                .select('*')\
                .eq('id_pedido', self.id)\
                .execute()
            if result.data:
                self.factura = result.data[0]
                return self.factura
            return None
        except Exception as e:
            logger.error(f'Error obteniendo factura: {str(e)}')
            return None
    
    def get_transacciones(self):
        try:
            supabase = get_supabase()
            result = supabase.table('transaccion_pago')\
                .select('*')\
                .eq('id_pedido', self.id)\
                .order('fecha_transaccion', desc=True)\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f'Error obteniendo transacciones: {str(e)}')
            return []
    
    def puede_cancelar(self):
        return self.estado in ['pendiente', 'confirmado']
    
    def puede_modificar(self):
        return self.estado == 'pendiente'
    
    def get_estado_class(self):
        clases = {
            'pendiente': 'warning',
            'confirmado': 'info',
            'procesando': 'primary',
            'enviado': 'info',
            'entregado': 'success',
            'cancelado': 'danger',
            'devuelto': 'secondary'
        }
        return clases.get(self.estado, 'secondary')
    
    def to_dict(self):
        return {
            'id_pedido': self.id,
            'fecha_pedido': self.fecha_pedido,
            'estado': self.estado,
            'subtotal': self.subtotal,
            'impuestos': self.impuestos,
            'gastos_envio': self.gastos_envio,
            'descuento_total': self.descuento_total,
            'total': self.total,
            'estado_class': self.get_estado_class()
        }
    
    @staticmethod
    def find_by_id(pedido_id):
        try:
            supabase = get_supabase()
            result = supabase.table('pedido')\
                .select('*')\
                .eq('id_pedido', pedido_id)\
                .execute()
            if result.data and len(result.data) > 0:
                return Pedido(result.data[0])
            return None
        except Exception as e:
            logger.error(f'Error buscando pedido: {str(e)}')
            return None
    
    @staticmethod
    def find_by_usuario(user_id, limit=50, offset=0):
        try:
            supabase = get_supabase()
            result = supabase.table('pedido')\
                .select('*, factura(*)')\
                .eq('id_usuario', user_id)\
                .order('fecha_pedido', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            return [Pedido(item) for item in result.data]
        except Exception as e:
            logger.error(f'Error buscando pedidos del usuario: {str(e)}')
            return []
    
    @staticmethod
    def create_from_cart(user_id, direccion_id, carrito, cupon=None, metodo_pago='tarjeta', notas=''):
        try:
            supabase = get_supabase()
            impuestos = carrito.subtotal * 0.21
            gastos_envio = 0
            total = carrito.subtotal + impuestos + gastos_envio - carrito.descuentos
            direccion_texto = f"Dirección ID: {direccion_id}"
            pedido_data = {
                'id_usuario': user_id,
                'id_direccion_envio': direccion_id,
                'subtotal': carrito.subtotal,
                'impuestos': impuestos,
                'gastos_envio': gastos_envio,
                'descuento_total': carrito.descuentos,
                'total': total,
                'estado': 'pendiente',
                'direccion_envio_texto': direccion_texto,
                'metodo_pedido': metodo_pago,
                'notas': notas
            }
            if cupon:
                pedido_data['id_cupon_aplicado'] = cupon['id_cupon']
            result = supabase.table('pedido')\
                .insert(pedido_data)\
                .execute()
            if not result.data:
                raise Exception('Error creando pedido')
            pedido = Pedido(result.data[0])
            for linea in carrito.lineas:
                linea_pedido = {
                    'id_pedido': pedido.id,
                    'id_variante': linea['id_variante'],
                    'cantidad': linea['cantidad'],
                    'precio_unitario': linea['precio_unitario'],
                    'descuento_aplicado': linea.get('descuento_aplicado', 0),
                    'total_linea': linea['cantidad'] * linea['precio_unitario']
                }
                supabase.table('linea_pedido')\
                    .insert(linea_pedido)\
                    .execute()
            return pedido
        except Exception as e:
            logger.error(f'Error creando pedido desde carrito: {str(e)}')
            raise
    
    @staticmethod
    def get_estadisticas():
        try:
            supabase = get_supabase()
            total = supabase.table('pedido').select('*', count='exact').execute()
            estados = ['pendiente', 'confirmado', 'procesando', 'enviado', 'entregado', 'cancelado']
            stats = {}
            for estado in estados:
                result = supabase.table('pedido')\
                    .select('*', count='exact')\
                    .eq('estado', estado)\
                    .execute()
                stats[estado] = result.count
            ventas = supabase.table('pedido')\
                .select('total')\
                .not_.eq('estado', 'cancelado')\
                .execute()
            total_ventas = sum(float(p['total']) for p in ventas.data)
            ventas_mensuales = {}
            for pedido in ventas.data:
                fecha = pedido.get('fecha_pedido', '')
                if fecha:
                    mes = fecha[:7]
                    if mes not in ventas_mensuales:
                        ventas_mensuales[mes] = 0
                    ventas_mensuales[mes] += float(pedido['total'])
            return {
                'total': total.count,
                'por_estado': stats,
                'total_ventas': total_ventas,
                'ventas_mensuales': ventas_mensuales
            }
        except Exception as e:
            logger.error(f'Error obteniendo estadísticas: {str(e)}')
            return {}

class LineaPedido:
    def __init__(self, data=None):
        if data:
            self.id = data.get('id_linea')
            self.id_pedido = data.get('id_pedido')
            self.id_variante = data.get('id_variante')
            self.cantidad = int(data.get('cantidad', 0))
            self.precio_unitario = float(data.get('precio_unitario', 0))
            self.id_financiacion_seleccionada = data.get('id_financiacion_seleccionada')
            self.descuento_aplicado = float(data.get('descuento_aplicado', 0))
            self.estado_linea = data.get('estado_linea', 'pendiente')
            self.impuesto_linea = float(data.get('impuesto_linea', 0))
            self.total_linea = float(data.get('total_linea', 0))
            self.numero_serie_asignado = data.get('numero_serie_asignado')
            self.variante = None
    
    def get_variante(self):
        if self.variante:
            return self.variante
        try:
            from app.models.producto import VarianteProducto
            self.variante = VarianteProducto.find_by_id(self.id_variante)
            return self.variante
        except Exception as e:
            logger.error(f'Error obteniendo variante: {str(e)}')
            return None
    
    def get_producto(self):
        if self.variante:
            return self.variante.get_producto()
        self.get_variante()
        if self.variante:
            return self.variante.get_producto()
        return None
    
    def to_dict(self):
        return {
            'id_linea': self.id,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'descuento_aplicado': self.descuento_aplicado,
            'total_linea': self.total_linea,
            'estado_linea': self.estado_linea
        }