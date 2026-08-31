"""
Servicio de Producto
Maneja toda la lógica de negocio relacionada con productos
"""
from app.utils.supabase_client import get_supabase, get_supabase_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ProductoService:
    """Servicio para operaciones con productos"""
    
    @staticmethod
    def get_all(page=1, per_page=12, search=None, categoria=None, solo_activos=True):
        """Obtener todos los productos con paginación y filtros"""
        try:
            supabase = get_supabase()
            start = (page - 1) * per_page
            
            query = supabase.table('PRODUCTO').select('*')
            
            if solo_activos:
                query = query.eq('estado', 'activo')
            
            if search:
                query = query.ilike('nombre', f'%{search}%')
            
            if categoria:
                # Buscar por categoría (subconsulta)
                categoria_result = supabase.table('CATEGORIA')\
                    .select('id_categoria')\
                    .eq('slug', categoria)\
                    .execute()
                
                if categoria_result.data:
                    cat_id = categoria_result.data[0]['id_categoria']
                    prod_cat = supabase.table('PRODUCTO_CATEGORIA')\
                        .select('id_producto')\
                        .eq('id_categoria', cat_id)\
                        .execute()
                    
                    if prod_cat.data:
                        prod_ids = [p['id_producto'] for p in prod_cat.data]
                        query = query.in_('id_producto', prod_ids)
            
            query = query.range(start, start + per_page - 1).order('created_at', desc=True)
            result = query.execute()
            
            # Contar total
            count_query = supabase.table('PRODUCTO').select('*', count='exact')
            if solo_activos:
                count_query = count_query.eq('estado', 'activo')
            if search:
                count_query = count_query.ilike('nombre', f'%{search}%')
            if categoria:
                # Aplicar mismo filtro de categoría
                pass
            
            count_result = count_query.execute()
            
            return {
                'productos': result.data,
                'total': count_result.count,
                'page': page,
                'per_page': per_page,
                'total_pages': (count_result.count + per_page - 1) // per_page
            }
        except Exception as e:
            logger.error(f'Error obteniendo productos: {str(e)}')
            raise
    
    @staticmethod
    def get_by_id(producto_id):
        """Obtener producto por ID con sus variantes y categorías"""
        try:
            supabase = get_supabase()
            
            # Obtener producto
            result = supabase.table('PRODUCTO')\
                .select('*, VARIANTE_PRODUCTO(*)')\
                .eq('id_producto', producto_id)\
                .execute()
            
            if not result.data:
                return None
            
            producto = result.data[0]
            
            # Obtener categorías
            categorias = supabase.table('PRODUCTO_CATEGORIA')\
                .select('CATEGORIA(*)')\
                .eq('id_producto', producto_id)\
                .execute()
            
            producto['categorias'] = [item['CATEGORIA'] for item in categorias.data if item.get('CATEGORIA')]
            
            return producto
        except Exception as e:
            logger.error(f'Error obteniendo producto: {str(e)}')
            raise
    
    @staticmethod
    def get_by_slug(slug):
        """Buscar producto por slug"""
        try:
            supabase = get_supabase()
            result = supabase.table('PRODUCTO')\
                .select('*')\
                .ilike('nombre', slug.replace('-', ' '))\
                .execute()
            
            if result.data:
                return ProductoService.get_by_id(result.data[0]['id_producto'])
            return None
        except Exception as e:
            logger.error(f'Error buscando producto por slug: {str(e)}')
            raise
    
    @staticmethod
    def create(data):
        """Crear nuevo producto"""
        try:
            supabase = get_supabase_service()
            
            # Limpiar datos
            clean_data = {
                'nombre': data.get('nombre', '').strip(),
                'descripcion': data.get('descripcion', '').strip(),
                'precio_base': float(data.get('precio_base', 0)),
                'imagen_url': data.get('imagen_url', '').strip(),
                'familia': data.get('familia', '').strip(),
                'marca': data.get('marca', 'Apple'),
                'estado': data.get('estado', 'activo'),
                'proveedor': data.get('proveedor', '').strip(),
                'codigo_fabricante': data.get('codigo_fabricante', '').strip()
            }
            
            if data.get('peso_kg'):
                clean_data['peso_kg'] = float(data['peso_kg'])
            if data.get('dimensiones'):
                clean_data['dimensiones'] = data['dimensiones'].strip()
            
            result = supabase.table('PRODUCTO')\
                .insert(clean_data)\
                .execute()
            
            if result.data:
                producto_id = result.data[0]['id_producto']
                
                # Asignar categorías
                categorias = data.get('categorias', [])
                for cat_id in categorias:
                    if cat_id:
                        supabase.table('PRODUCTO_CATEGORIA').insert({
                            'id_producto': producto_id,
                            'id_categoria': cat_id
                        }).execute()
                
                # Crear variantes
                colores = data.get('colores', [])
                capacidades = data.get('capacidades', [])
                precios_extra = data.get('precios_extra', [])
                stocks = data.get('stocks', [])
                skus = data.get('skus', [])
                
                for i in range(len(colores)):
                    if colores[i] and skus[i]:
                        variante_data = {
                            'id_producto': producto_id,
                            'color': colores[i],
                            'capacidad': capacidades[i] if i < len(capacidades) else None,
                            'precio_extra': float(precios_extra[i]) if i < len(precios_extra) and precios_extra[i] else 0,
                            'stock_disponible': int(stocks[i]) if i < len(stocks) and stocks[i] else 0,
                            'sku': skus[i],
                            'activo': True
                        }
                        supabase.table('VARIANTE_PRODUCTO')\
                            .insert(variante_data)\
                            .execute()
                
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f'Error creando producto: {str(e)}')
            raise
    
    @staticmethod
    def update(producto_id, data):
        """Actualizar producto"""
        try:
            supabase = get_supabase_service()
            
            # Limpiar datos
            clean_data = {}
            for key, value in data.items():
                if value is not None:
                    if key in ['nombre', 'descripcion', 'imagen_url', 'familia', 'proveedor', 'codigo_fabricante', 'dimensiones']:
                        clean_data[key] = value.strip() if value else ''
                    elif key in ['precio_base', 'peso_kg']:
                        clean_data[key] = float(value) if value else 0
                    elif key in ['marca', 'estado']:
                        clean_data[key] = value
            
            result = supabase.table('PRODUCTO')\
                .update(clean_data)\
                .eq('id_producto', producto_id)\
                .execute()
            
            if result.data:
                # Actualizar categorías
                if 'categorias' in data:
                    supabase.table('PRODUCTO_CATEGORIA')\
                        .delete()\
                        .eq('id_producto', producto_id)\
                        .execute()
                    
                    for cat_id in data['categorias']:
                        if cat_id:
                            supabase.table('PRODUCTO_CATEGORIA').insert({
                                'id_producto': producto_id,
                                'id_categoria': cat_id
                            }).execute()
                
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f'Error actualizando producto: {str(e)}')
            raise
    
    @staticmethod
    def delete(producto_id):
        """Eliminar producto (desactivar)"""
        try:
            supabase = get_supabase_service()
            
            result = supabase.table('PRODUCTO')\
                .update({'estado': 'discontinuado'})\
                .eq('id_producto', producto_id)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f'Error eliminando producto: {str(e)}')
            raise
    
    @staticmethod
    def get_variantes(producto_id):
        """Obtener variantes de un producto"""
        try:
            supabase = get_supabase()
            result = supabase.table('VARIANTE_PRODUCTO')\
                .select('*')\
                .eq('id_producto', producto_id)\
                .eq('activo', True)\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f'Error obteniendo variantes: {str(e)}')
            raise
    
    @staticmethod
    def get_variante_by_id(variante_id):
        """Obtener variante por ID"""
        try:
            supabase = get_supabase()
            result = supabase.table('VARIANTE_PRODUCTO')\
                .select('*, PRODUCTO(*)')\
                .eq('id_variante', variante_id)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f'Error obteniendo variante: {str(e)}')
            raise
    
    @staticmethod
    def actualizar_stock(variante_id, cantidad):
        """Actualizar stock de una variante"""
        try:
            supabase = get_supabase_service()
            
            # Obtener stock actual
            variante = ProductoService.get_variante_by_id(variante_id)
            if not variante:
                raise Exception('Variante no encontrada')
            
            nuevo_stock = variante['stock_disponible'] + cantidad
            
            if nuevo_stock < 0:
                raise Exception('Stock insuficiente')
            
            result = supabase.table('VARIANTE_PRODUCTO')\
                .update({'stock_disponible': nuevo_stock})\
                .eq('id_variante', variante_id)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f'Error actualizando stock: {str(e)}')
            raise
    
    @staticmethod
    def get_categorias():
        """Obtener todas las categorías"""
        try:
            supabase = get_supabase()
            result = supabase.table('CATEGORIA')\
                .select('*')\
                .eq('activo', True)\
                .order('nombre')\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f'Error obteniendo categorías: {str(e)}')
            raise
    
    @staticmethod
    def get_categoria_raices():
        """Obtener categorías raíz"""
        try:
            supabase = get_supabase()
            result = supabase.table('CATEGORIA')\
                .select('*')\
                .is_('id_categoria_padre', None)\
                .eq('activo', True)\
                .order('orden')\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f'Error obteniendo categorías raíz: {str(e)}')
            raise
    
    @staticmethod
    def get_estadisticas():
        """Obtener estadísticas de productos"""
        try:
            supabase = get_supabase_service()
            
            # Total productos
            total = supabase.table('PRODUCTO').select('*', count='exact').execute()
            
            # Productos activos
            activos = supabase.table('PRODUCTO')\
                .select('*', count='exact')\
                .eq('estado', 'activo')\
                .execute()
            
            # Productos sin stock
            sin_stock = supabase.table('VARIANTE_PRODUCTO')\
                .select('*', count='exact')\
                .eq('stock_disponible', 0)\
                .execute()
            
            # Productos con bajo stock
            bajo_stock = supabase.table('VARIANTE_PRODUCTO')\
                .select('*', count='exact')\
                .lt('stock_disponible', 'stock_minimo')\
                .execute()
            
            return {
                'total': total.count,
                'activos': activos.count,
                'sin_stock': sin_stock.count,
                'bajo_stock': bajo_stock.count
            }
        except Exception as e:
            logger.error(f'Error obteniendo estadísticas: {str(e)}')
            raise