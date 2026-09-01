"""
Modelo de Categoría
"""
from app.utils.supabase_client import get_supabase
import logging

logger = logging.getLogger(__name__)

class Categoria:
    """Modelo de Categoría de Productos"""
    
    def __init__(self, data=None):
        if data:
            self.id = data.get('id_categoria')
            self.nombre = data.get('nombre')
            self.descripcion = data.get('descripcion')
            self.id_categoria_padre = data.get('id_categoria_padre')
            self.slug = data.get('slug')
            self.icono_url = data.get('icono_url')
            self.orden = int(data.get('orden', 0))
            self.activo = data.get('activo', True)
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
            self.subcategorias = []
            self.categoria_padre = None
    
    def get_subcategorias(self):
        """Obtener subcategorías"""
        if self.subcategorias:
            return self.subcategorias
        
        try:
            supabase = get_supabase()
            result = supabase.table('categoria')\
                .select('*')\
                .eq('id_categoria_padre', self.id)\
                .eq('activo', True)\
                .order('orden')\
                .execute()
            
            self.subcategorias = [Categoria(item) for item in result.data]
            return self.subcategorias
        except Exception as e:
            logger.error(f'Error obteniendo subcategorías: {str(e)}')
            return []
    
    def get_categoria_padre(self):
        """Obtener categoría padre"""
        if self.categoria_padre:
            return self.categoria_padre
        
        if not self.id_categoria_padre:
            return None
        
        try:
            supabase = get_supabase()
            result = supabase.table('categoria')\
                .select('*')\
                .eq('id_categoria', self.id_categoria_padre)\
                .execute()
            
            if result.data:
                self.categoria_padre = Categoria(result.data[0])
                return self.categoria_padre
            return None
        except Exception as e:
            logger.error(f'Error obteniendo categoría padre: {str(e)}')
            return None
    
    def get_productos(self, limit=None, solo_activos=True):
        """Obtener productos de esta categoría"""
        try:
            supabase = get_supabase()
            
            query = supabase.table('producto_categoria')\
                .select('producto(*)')\
                .eq('id_categoria', self.id)
            
            if solo_activos:
                query = query.eq('producto.estado', 'activo')
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            
            from app.models.producto import Producto
            productos = [Producto(item['producto']) for item in result.data if item.get('producto')]
            return productos
        except Exception as e:
            logger.error(f'Error obteniendo productos de la categoría: {str(e)}')
            return []
    
    def get_nivel(self):
        """Obtener nivel de profundidad de la categoría"""
        nivel = 0
        actual = self
        while actual.id_categoria_padre:
            nivel += 1
            actual = actual.get_categoria_padre()
            if not actual:
                break
        return nivel
    
    def es_raiz(self):
        """Verificar si es categoría raíz"""
        return self.id_categoria_padre is None
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id_categoria': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'slug': self.slug,
            'icono_url': self.icono_url,
            'orden': self.orden,
            'activo': self.activo,
            'es_raiz': self.es_raiz(),
            'nivel': self.get_nivel()
        }
    
    @staticmethod
    def find_by_id(categoria_id):
        """Buscar categoría por ID"""
        try:
            supabase = get_supabase()
            result = supabase.table('categoria')\
                .select('*')\
                .eq('id_categoria', categoria_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                return Categoria(result.data[0])
            return None
        except Exception as e:
            logger.error(f'Error buscando categoría: {str(e)}')
            return None
    
    @staticmethod
    def find_by_slug(slug):
        """Buscar categoría por slug"""
        try:
            supabase = get_supabase()
            result = supabase.table('categoria')\
                .select('*')\
                .eq('slug', slug)\
                .execute()
            
            if result.data and len(result.data) > 0:
                return Categoria(result.data[0])
            return None
        except Exception as e:
            logger.error(f'Error buscando categoría por slug: {str(e)}')
            return None
    
    @staticmethod
    def get_raices():
        """Obtener categorías raíz"""
        try:
            supabase = get_supabase()
            result = supabase.table('categoria')\
                .select('*')\
                .is_('id_categoria_padre', None)\
                .eq('activo', True)\
                .order('orden')\
                .execute()
            
            return [Categoria(item) for item in result.data]
        except Exception as e:
            logger.error(f'Error obteniendo categorías raíz: {str(e)}')
            return []