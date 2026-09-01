"""
Modelo de Producto
"""
from app.utils.supabase_client import get_supabase
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Producto:
    """Modelo de Producto"""
    
    def __init__(self, data=None):
        if data:
            self.id = data.get('id_producto')
            self.nombre = data.get('nombre')
            self.descripcion = data.get('descripcion')
            self.precio_base = float(data.get('precio_base', 0))
            self.imagen_url = data.get('imagen_url')
            self.familia = data.get('familia')
            self.marca = data.get('marca', 'Apple')
            self.fecha_lanzamiento = data.get('fecha_lanzamiento')
            self.estado = data.get('estado', 'activo')
            self.proveedor = data.get('proveedor')
            self.codigo_fabricante = data.get('codigo_fabricante')
            self.peso_kg = float(data.get('peso_kg', 0)) if data.get('peso_kg') else None
            self.dimensiones = data.get('dimensiones')
            self.requiere_autorizacion = data.get('requiere_autorizacion', False)
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
            self.variantes = []
            self.categorias = []
    
    def get_variantes(self):
        """Obtener variantes del producto"""
        if self.variantes:
            return self.variantes
        
        try:
            supabase = get_supabase()
            result = supabase.table('variante_producto')\
                .select('*')\
                .eq('id_producto', self.id)\
                .eq('activo', True)\
                .execute()
            
            self.variantes = [VarianteProducto(item) for item in result.data]
            return self.variantes
        except Exception as e:
            logger.error(f'Error obteniendo variantes: {str(e)}')
            return []
    
    def get_categorias(self):
        """Obtener categorías del producto"""
        if self.categorias:
            return self.categorias
        
        try:
            supabase = get_supabase()
            result = supabase.table('producto_categoria')\
                .select('categoria(*)')\
                .eq('id_producto', self.id)\
                .execute()
            
            self.categorias = [item['categoria'] for item in result.data if item.get('categoria')]
            return self.categorias
        except Exception as e:
            logger.error(f'Error obteniendo categorías: {str(e)}')
            return []
    
    def get_resenas(self, approved_only=True):
        """Obtener reseñas del producto"""
        try:
            supabase = get_supabase()
            
            # Obtener variantes primero
            variantes = self.get_variantes()
            if not variantes:
                return []
            
            variante_ids = [v.id for v in variantes]
            
            query = supabase.table('resena_producto')\
                .select('*, usuario(nombre_completo)')\
                .in_('id_variante', variante_ids)
            
            if approved_only:
                query = query.eq('aprobado', True)
            
            result = query.order('fecha_creacion', desc=True).execute()
            return result.data
        except Exception as e:
            logger.error(f'Error obteniendo reseñas: {str(e)}')
            return []
    
    def get_precio_minimo(self):
        """Obtener precio mínimo entre todas las variantes"""
        variantes = self.get_variantes()
        if not variantes:
            return self.precio_base
        
        precios = [v.precio_total for v in variantes]
        return min(precios)
    
    def get_precio_maximo(self):
        """Obtener precio máximo entre todas las variantes"""
        variantes = self.get_variantes()
        if not variantes:
            return self.precio_base
        
        precios = [v.precio_total for v in variantes]
        return max(precios)
    
    def get_stock_total(self):
        """Obtener stock total del producto"""
        variantes = self.get_variantes()
        if not variantes:
            return 0
        
        return sum(v.stock_disponible for v in variantes)
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id_producto': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'precio_base': self.precio_base,
            'imagen_url': self.imagen_url,
            'familia': self.familia,
            'marca': self.marca,
            'estado': self.estado,
            'categorias': self.categorias,
            'variantes_count': len(self.variantes)
        }
    
    @staticmethod
    def find_by_id(producto_id):
        """Buscar producto por ID"""
        try:
            supabase = get_supabase()
            result = supabase.table('producto')\
                .select('*')\
                .eq('id_producto', producto_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                return Producto(result.data[0])
            return None
        except Exception as e:
            logger.error(f'Error buscando producto: {str(e)}')
            return None
    
    @staticmethod
    def search(query=None, categoria=None, page=1, per_page=12, solo_activos=True):
        """Buscar productos con filtros"""
        try:
            supabase = get_supabase()
            
            # Query base - TRAER TODOS LOS PRODUCTOS
            db_query = supabase.table('producto').select('*')
            
            # Filtros
            if solo_activos:
                db_query = db_query.eq('estado', 'activo')
            
            if query:
                db_query = db_query.ilike('nombre', f'%{query}%')
            
            if categoria:
                # Buscar por categoría (subconsulta)
                categoria_result = supabase.table('categoria')\
                    .select('id_categoria')\
                    .eq('slug', categoria)\
                    .execute()
                
                if categoria_result.data:
                    cat_id = categoria_result.data[0]['id_categoria']
                    prod_cat = supabase.table('producto_categoria')\
                        .select('id_producto')\
                        .eq('id_categoria', cat_id)\
                        .execute()
                    
                    if prod_cat.data:
                        prod_ids = [p['id_producto'] for p in prod_cat.data]
                        db_query = db_query.in_('id_producto', prod_ids)
            
            # Paginación
            start = (page - 1) * per_page
            db_query = db_query.range(start, start + per_page - 1)
            
            # Ordenar
            db_query = db_query.order('created_at', desc=True)
            
            result = db_query.execute()
            
            # Obtener total
            count_query = supabase.table('producto').select('*', count='exact')
            if solo_activos:
                count_query = count_query.eq('estado', 'activo')
            if query:
                count_query = count_query.ilike('nombre', f'%{query}%')
            
            count_result = count_query.execute()
            
            return {
                'productos': [Producto(item) for item in result.data],
                'total': count_result.count,
                'page': page,
                'per_page': per_page,
                'total_pages': (count_result.count + per_page - 1) // per_page if count_result.count > 0 else 1
            }
        except Exception as e:
            logger.error(f'Error buscando productos: {str(e)}')
            import traceback
            traceback.print_exc()
            return {'productos': [], 'total': 0, 'page': page, 'per_page': per_page, 'total_pages': 1}


class VarianteProducto:
    """Modelo de Variante de Producto"""
    
    def __init__(self, data=None):
        if data:
            self.id = data.get('id_variante')
            self.id_producto = data.get('id_producto')
            self.color = data.get('color')
            self.capacidad = data.get('capacidad')
            self.tamaño = data.get('tamaño')
            self.material = data.get('material')
            self.talla_correa = data.get('talla_correa')
            self.precio_extra = float(data.get('precio_extra', 0))
            self.stock_disponible = int(data.get('stock_disponible', 0))
            self.sku = data.get('sku')
            self.activo = data.get('activo', True)
            self.codigo_barras = data.get('codigo_barras')
            self.stock_minimo = int(data.get('stock_minimo', 0))
            self.stock_umbral_alerta = int(data.get('stock_umbral_alerta', 5))
            self.peso_extra_kg = float(data.get('peso_extra_kg', 0))
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
            self._producto = None
    
    @property
    def precio_total(self):
        """Precio total (base + extra)"""
        if self._producto:
            return self._producto.precio_base + self.precio_extra
        return self.precio_extra
    
    def get_producto(self):
        """Obtener producto asociado"""
        if self._producto:
            return self._producto
        
        try:
            supabase = get_supabase()
            result = supabase.table('producto')\
                .select('*')\
                .eq('id_producto', self.id_producto)\
                .execute()
            
            if result.data:
                self._producto = Producto(result.data[0])
                return self._producto
            return None
        except Exception as e:
            logger.error(f'Error obteniendo producto: {str(e)}')
            return None
    
    def get_imagenes(self):
        """Obtener imágenes de la variante"""
        try:
            supabase = get_supabase()
            result = supabase.table('imagen_producto')\
                .select('*')\
                .eq('id_variante', self.id)\
                .order('orden')\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f'Error obteniendo imágenes: {str(e)}')
            return []
    
    def get_imagen_principal(self):
        """Obtener imagen principal"""
        imagenes = self.get_imagenes()
        for img in imagenes:
            if img.get('principal'):
                return img.get('url_imagen')
        return imagenes[0].get('url_imagen') if imagenes else None
    
    def has_stock(self, cantidad=1):
        """Verificar si hay stock disponible"""
        return self.stock_disponible >= cantidad
    
    def reducir_stock(self, cantidad):
        """Reducir stock"""
        try:
            supabase = get_supabase()
            
            if not self.has_stock(cantidad):
                raise Exception('Stock insuficiente')
            
            result = supabase.table('variante_producto')\
                .update({'stock_disponible': self.stock_disponible - cantidad})\
                .eq('id_variante', self.id)\
                .execute()
            
            if result.data:
                self.stock_disponible -= cantidad
                return True
            return False
        except Exception as e:
            logger.error(f'Error reduciendo stock: {str(e)}')
            raise
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id_variante': self.id,
            'color': self.color,
            'capacidad': self.capacidad,
            'tamaño': self.tamaño,
            'precio_extra': self.precio_extra,
            'precio_total': self.precio_total,
            'stock_disponible': self.stock_disponible,
            'sku': self.sku,
            'activo': self.activo
        }
    
    @staticmethod
    def find_by_sku(sku):
        """Buscar variante por SKU"""
        try:
            supabase = get_supabase()
            result = supabase.table('variante_producto')\
                .select('*')\
                .eq('sku', sku)\
                .execute()
            
            if result.data and len(result.data) > 0:
                return VarianteProducto(result.data[0])
            return None
        except Exception as e:
            logger.error(f'Error buscando variante por SKU: {str(e)}')
            return None
    
    @staticmethod
    def find_by_id(variante_id):
        """Buscar variante por ID"""
        try:
            supabase = get_supabase()
            result = supabase.table('variante_producto')\
                .select('*')\
                .eq('id_variante', variante_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                return VarianteProducto(result.data[0])
            return None
        except Exception as e:
            logger.error(f'Error buscando variante: {str(e)}')
            return None