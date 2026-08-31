"""
Modelo de Carrito de Compras
"""
from app.utils.supabase_client import get_supabase
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Carrito:
    """Modelo de Carrito de Compras"""
    
    def __init__(self, data=None):
        if data:
            self.id = data.get('id_carrito')
            self.id_usuario = data.get('id_usuario')
            self.fecha_creacion = data.get('fecha_creacion')
            self.fecha_actualizacion = data.get('fecha_actualizacion')
            self.estado = data.get('estado', 'activo')
            self.session_id = data.get('session_id')
            self.subtotal = float(data.get('subtotal', 0))
            self.descuentos = float(data.get('descuentos', 0))
            self.codigo_cupon = data.get('codigo_cupon')
            self.total = float(data.get('total', 0))
            self.fecha_expiracion = data.get('fecha_expiracion')
            self.lineas = []
            self.total_items = 0
    
    def cargar_lineas(self):
        """Cargar líneas del carrito y recalcular totales"""
        try:
            supabase = get_supabase()
            
            # Cargar líneas con relaciones
            result = supabase.table('linea_carrito')\
                .select('*, variante_producto(*, producto(*))')\
                .eq('id_carrito', self.id)\
                .execute()
            
            self.lineas = result.data
            self.total_items = sum(linea.get('cantidad', 0) for linea in self.lineas)
            
            # Recalcular subtotal desde las líneas
            subtotal = 0
            for linea in self.lineas:
                subtotal += float(linea.get('cantidad', 0)) * float(linea.get('precio_unitario', 0))
            
            # Actualizar siempre los valores en el objeto
            self.subtotal = subtotal
            self.total = subtotal - self.descuentos
            
            # Intentar actualizar la base de datos (si falla, no importa, los valores en memoria son correctos)
            try:
                if abs(subtotal - self.subtotal) > 0.01 or (subtotal - self.descuentos) != self.total:
                    supabase.table('carrito')\
                        .update({
                            'subtotal': subtotal,
                            'total': self.total
                        })\
                        .eq('id_carrito', self.id)\
                        .execute()
            except Exception as e:
                logger.warning(f'Error actualizando base de datos en cargar_lineas: {str(e)}')
            
            return self.lineas
        except Exception as e:
            logger.error(f'Error cargando líneas del carrito: {str(e)}')
            return []
    
    def agregar_producto(self, variante_id, cantidad=1):
        """Agregar producto al carrito"""
        try:
            supabase = get_supabase()
            
            # Verificar si ya existe
            existing = supabase.table('linea_carrito')\
                .select('*')\
                .eq('id_carrito', self.id)\
                .eq('id_variante', variante_id)\
                .execute()
            
            # Obtener precio del producto
            variante = supabase.table('variante_producto')\
                .select('*, producto(precio_base)')\
                .eq('id_variante', variante_id)\
                .execute()
            
            if not variante.data:
                raise Exception('Producto no encontrado')
            
            precio = float(variante.data[0]['producto']['precio_base']) + float(variante.data[0].get('precio_extra', 0))
            
            if existing.data:
                # Actualizar cantidad
                nueva_cantidad = existing.data[0]['cantidad'] + cantidad
                result = supabase.table('linea_carrito')\
                    .update({
                        'cantidad': nueva_cantidad,
                        'precio_unitario': precio
                    })\
                    .eq('id_linea_carrito', existing.data[0]['id_linea_carrito'])\
                    .execute()
                linea_result = result.data[0] if result.data else None
            else:
                # Crear nueva línea
                line_data = {
                    'id_carrito': self.id,
                    'id_variante': variante_id,
                    'cantidad': cantidad,
                    'precio_unitario': precio,
                    'descuento_aplicado': 0
                }
                
                result = supabase.table('linea_carrito')\
                    .insert(line_data)\
                    .execute()
                linea_result = result.data[0] if result.data else None
            
            # Forzar recálculo y actualización en memoria y base de datos
            self.recalcular_totales()
            
            # Recargar líneas
            self.cargar_lineas()
            
            return linea_result
        except Exception as e:
            logger.error(f'Error agregando producto al carrito: {str(e)}')
            raise
    
    def actualizar_cantidad(self, linea_id, cantidad):
        """Actualizar cantidad de un producto en el carrito"""
        try:
            supabase = get_supabase()
            
            if cantidad <= 0:
                return self.eliminar_producto(linea_id)
            
            result = supabase.table('linea_carrito')\
                .update({'cantidad': cantidad})\
                .eq('id_linea_carrito', linea_id)\
                .eq('id_carrito', self.id)\
                .execute()
            
            if result.data:
                self.recalcular_totales()
                self.cargar_lineas()
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f'Error actualizando cantidad: {str(e)}')
            raise
    
    def eliminar_producto(self, linea_id):
        """Eliminar producto del carrito"""
        try:
            supabase = get_supabase()
            
            result = supabase.table('linea_carrito')\
                .delete()\
                .eq('id_linea_carrito', linea_id)\
                .eq('id_carrito', self.id)\
                .execute()
            
            if result.data:
                self.recalcular_totales()
                self.cargar_lineas()
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f'Error eliminando producto: {str(e)}')
            raise
    
    def vaciar(self):
        """Vaciar el carrito completamente"""
        try:
            supabase = get_supabase()
            
            # Eliminar todas las líneas
            supabase.table('linea_carrito')\
                .delete()\
                .eq('id_carrito', self.id)\
                .execute()
            
            # Resetear totales en memoria
            self.subtotal = 0
            self.descuentos = 0
            self.total = 0
            self.codigo_cupon = None
            self.lineas = []
            self.total_items = 0
            
            # Intentar actualizar la base de datos
            try:
                supabase.table('carrito')\
                    .update({
                        'subtotal': 0,
                        'descuentos': 0,
                        'total': 0,
                        'codigo_cupon': None
                    })\
                    .eq('id_carrito', self.id)\
                    .execute()
            except Exception as e:
                logger.warning(f'Error actualizando base de datos en vaciar: {str(e)}')
            
            return True
        except Exception as e:
            logger.error(f'Error vaciando carrito: {str(e)}')
            raise
    
    def recalcular_totales(self):
        """Recalcular subtotal y total del carrito y actualizar en memoria y base de datos"""
        try:
            supabase = get_supabase()
            
            # Obtener todas las líneas
            lineas = supabase.table('linea_carrito')\
                .select('*')\
                .eq('id_carrito', self.id)\
                .execute()
            
            subtotal = 0
            for linea in lineas.data:
                subtotal += float(linea.get('cantidad', 0)) * float(linea.get('precio_unitario', 0))
            
            # Calcular total
            total = subtotal - self.descuentos
            
            # Actualizar siempre los valores en el objeto
            self.subtotal = subtotal
            self.total = total
            self.total_items = sum(linea.get('cantidad', 0) for linea in lineas.data)
            
            # Intentar actualizar la base de datos (si falla, los valores en memoria ya están correctos)
            try:
                supabase.table('carrito')\
                    .update({
                        'subtotal': subtotal,
                        'total': total
                    })\
                    .eq('id_carrito', self.id)\
                    .execute()
            except Exception as e:
                logger.warning(f'Error actualizando base de datos en recalcular_totales: {str(e)}')
            
            logger.info(f'Carrito actualizado - Subtotal: {subtotal}, Total: {total}, Items: {self.total_items}')
            
            return {
                'subtotal': self.subtotal,
                'total': self.total,
                'total_items': self.total_items
            }
        except Exception as e:
            logger.error(f'Error recalculando totales: {str(e)}')
            return {
                'subtotal': self.subtotal,
                'total': self.total,
                'total_items': self.total_items
            }
    
    def aplicar_cupon(self, codigo):
        """Aplicar cupón de descuento"""
        try:
            supabase = get_supabase()
            
            # Verificar cupón
            cupon = supabase.table('cupon_descuento')\
                .select('*')\
                .eq('codigo', codigo)\
                .eq('activo', True)\
                .execute()
            
            if not cupon.data:
                raise Exception('Cupón inválido')
            
            cupon_data = cupon.data[0]
            
            # Verificar vigencia
            hoy = datetime.now().date()
            if cupon_data.get('fecha_validez_inicio'):
                fecha_inicio = datetime.strptime(cupon_data['fecha_validez_inicio'], '%Y-%m-%d').date()
                if hoy < fecha_inicio:
                    raise Exception('Cupón no vigente')
            
            if cupon_data.get('fecha_validez_fin'):
                fecha_fin = datetime.strptime(cupon_data['fecha_validez_fin'], '%Y-%m-%d').date()
                if hoy > fecha_fin:
                    raise Exception('Cupón expirado')
            
            # Verificar uso máximo
            if cupon_data.get('uso_maximo') and cupon_data.get('usos_actuales', 0) >= cupon_data['uso_maximo']:
                raise Exception('Cupón agotado')
            
            # Verificar monto mínimo
            if cupon_data.get('monto_minimo_compra') and self.subtotal < cupon_data['monto_minimo_compra']:
                raise Exception(f'El monto mínimo de compra es ${cupon_data["monto_minimo_compra"]}')
            
            # Calcular descuento
            descuento = 0
            if cupon_data.get('porcentaje_descuento'):
                descuento = self.subtotal * (float(cupon_data['porcentaje_descuento']) / 100)
            elif cupon_data.get('monto_fijo_descuento'):
                descuento = float(cupon_data['monto_fijo_descuento'])
            
            if descuento > self.subtotal:
                descuento = self.subtotal
            
            # Actualizar en memoria
            self.descuentos = descuento
            self.total = self.subtotal - descuento
            self.codigo_cupon = codigo
            
            # Intentar actualizar la base de datos
            try:
                supabase.table('carrito')\
                    .update({
                        'descuentos': descuento,
                        'total': self.total,
                        'codigo_cupon': codigo
                    })\
                    .eq('id_carrito', self.id)\
                    .execute()
            except Exception as e:
                logger.warning(f'Error actualizando base de datos en aplicar_cupon: {str(e)}')
            
            # Incrementar uso del cupón
            try:
                supabase.table('cupon_descuento')\
                    .update({'usos_actuales': cupon_data.get('usos_actuales', 0) + 1})\
                    .eq('id_cupon', cupon_data['id_cupon'])\
                    .execute()
            except Exception as e:
                logger.warning(f'Error actualizando uso del cupón: {str(e)}')
            
            return {
                'descuento': descuento,
                'total': self.total,
                'codigo': codigo
            }
        except Exception as e:
            logger.error(f'Error aplicando cupón: {str(e)}')
            raise
    
    def eliminar_cupon(self):
        """Eliminar cupón aplicado"""
        try:
            # Actualizar en memoria
            self.descuentos = 0
            self.total = self.subtotal
            self.codigo_cupon = None
            
            # Intentar actualizar la base de datos
            try:
                supabase = get_supabase()
                supabase.table('carrito')\
                    .update({
                        'descuentos': 0,
                        'total': self.subtotal,
                        'codigo_cupon': None
                    })\
                    .eq('id_carrito', self.id)\
                    .execute()
            except Exception as e:
                logger.warning(f'Error actualizando base de datos en eliminar_cupon: {str(e)}')
            
            return True
        except Exception as e:
            logger.error(f'Error eliminando cupón: {str(e)}')
            raise
    
    @staticmethod
    def get_or_create_cart(user_id):
        """Obtener carrito activo o crear uno nuevo"""
        try:
            supabase = get_supabase()
            
            # Buscar carrito activo
            result = supabase.table('carrito')\
                .select('*')\
                .eq('id_usuario', user_id)\
                .eq('estado', 'activo')\
                .execute()
            
            if result.data and len(result.data) > 0:
                carrito = Carrito(result.data[0])
                carrito.cargar_lineas()
                return carrito
            
            # Crear nuevo carrito
            cart_data = {
                'id_usuario': user_id,
                'estado': 'activo',
                'subtotal': 0,
                'descuentos': 0,
                'total': 0
            }
            
            result = supabase.table('carrito')\
                .insert(cart_data)\
                .execute()
            
            if result.data:
                carrito = Carrito(result.data[0])
                carrito.cargar_lineas()
                return carrito
            
            raise Exception('Error creando carrito')
        except Exception as e:
            logger.error(f'Error obteniendo carrito: {str(e)}')
            raise
    
    @staticmethod
    def get_session_cart(session_id):
        """Obtener carrito por session ID (para usuarios no logueados)"""
        try:
            supabase = get_supabase()
            
            result = supabase.table('carrito')\
                .select('*')\
                .eq('session_id', session_id)\
                .eq('estado', 'activo')\
                .execute()
            
            if result.data and len(result.data) > 0:
                carrito = Carrito(result.data[0])
                carrito.cargar_lineas()
                return carrito
            
            return None
        except Exception as e:
            logger.error(f'Error obteniendo carrito por session: {str(e)}')
            return None
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id_carrito': self.id,
            'subtotal': self.subtotal,
            'descuentos': self.descuentos,
            'total': self.total,
            'total_items': self.total_items,
            'lineas': self.lineas,
            'codigo_cupon': self.codigo_cupon
        }


class LineaCarrito:
    """Modelo de Línea de Carrito"""
    
    def __init__(self, data=None):
        if data:
            self.id = data.get('id_linea_carrito')
            self.id_carrito = data.get('id_carrito')
            self.id_variante = data.get('id_variante')
            self.cantidad = int(data.get('cantidad', 0))
            self.fecha_agregado = data.get('fecha_agregado')
            self.precio_unitario = float(data.get('precio_unitario', 0))
            self.descuento_aplicado = float(data.get('descuento_aplicado', 0))
            self.variante = None
            self.total = self.cantidad * self.precio_unitario - self.descuento_aplicado
    
    def get_variante(self):
        """Obtener variante del producto"""
        if self.variante:
            return self.variante
        
        try:
            from app.models.producto import VarianteProducto
            self.variante = VarianteProducto.find_by_id(self.id_variante)
            return self.variante
        except Exception as e:
            logger.error(f'Error obteniendo variante: {str(e)}')
            return None
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id_linea_carrito': self.id,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'descuento_aplicado': self.descuento_aplicado,
            'total': self.total,
            'variante': self.variante.to_dict() if self.variante else None
        }