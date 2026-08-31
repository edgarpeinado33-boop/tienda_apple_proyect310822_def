"""
Cliente de Supabase para la aplicación
Maneja la conexión y operaciones con Supabase
"""
from supabase import create_client, Client
from flask import current_app, g, session
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def init_supabase(app):
    """Inicializar cliente Supabase"""
    app.supabase = None
    
    @app.before_request
    def before_request():
        """Crear cliente Supabase para cada request"""
        try:
            url = current_app.config.get('SUPABASE_URL')
            key = current_app.config.get('SUPABASE_KEY')
            
            if url and key:
                g.supabase = create_client(url, key)
                logger.debug('Conexión Supabase establecida')
            else:
                logger.error('Credenciales Supabase no configuradas')
                g.supabase = None
                
        except Exception as e:
            logger.error(f'Error conectando a Supabase: {str(e)}')
            g.supabase = None
    
    @app.teardown_appcontext
    def teardown_appcontext(exception=None):
        """Limpiar recursos al finalizar la request"""
        if hasattr(g, 'supabase'):
            g.supabase = None

def get_supabase():
    """Obtener cliente Supabase del contexto actual"""
    if not hasattr(g, 'supabase') or g.supabase is None:
        # Intentar crear uno nuevo
        try:
            url = current_app.config.get('SUPABASE_URL')
            key = current_app.config.get('SUPABASE_KEY')
            if url and key:
                g.supabase = create_client(url, key)
                return g.supabase
        except Exception as e:
            logger.error(f'Error creando cliente Supabase: {str(e)}')
            raise Exception('Cliente Supabase no disponible')
        
        raise Exception('Cliente Supabase no disponible')
    return g.supabase

def get_supabase_service():
    """Obtener cliente Supabase con clave de servicio (para operaciones admin)"""
    try:
        url = current_app.config.get('SUPABASE_URL')
        key = current_app.config.get('SUPABASE_SERVICE_KEY')
        
        if not url or not key:
            raise Exception('Credenciales de servicio no configuradas')
        
        return create_client(url, key)
    except Exception as e:
        logger.error(f'Error obteniendo cliente Supabase Service: {str(e)}')
        raise

def supabase_required(f):
    """Decorador para verificar que Supabase está disponible"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            get_supabase()
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f'Supabase no disponible: {str(e)}')
            from flask import jsonify
            return jsonify({'error': 'Servicio no disponible'}), 503
    return decorated_function

class SupabaseQuery:
    """Clase helper para construir queries de Supabase"""
    
    def __init__(self, table):
        self.table = table
        self.filters = []
        self.order_by = None
        self.limit_value = None
        self.offset_value = None
        self.select_fields = '*'
    
    def select(self, fields):
        """Seleccionar campos específicos"""
        self.select_fields = fields
        return self
    
    def where(self, column, operator, value):
        """Agregar filtro WHERE"""
        self.filters.append((column, operator, value))
        return self
    
    def eq(self, column, value):
        """Igual a"""
        return self.where(column, 'eq', value)
    
    def neq(self, column, value):
        """Diferente de"""
        return self.where(column, 'neq', value)
    
    def gt(self, column, value):
        """Mayor que"""
        return self.where(column, 'gt', value)
    
    def gte(self, column, value):
        """Mayor o igual que"""
        return self.where(column, 'gte', value)
    
    def lt(self, column, value):
        """Menor que"""
        return self.where(column, 'lt', value)
    
    def lte(self, column, value):
        """Menor o igual que"""
        return self.where(column, 'lte', value)
    
    def like(self, column, pattern):
        """Like (búsqueda de texto)"""
        return self.where(column, 'like', pattern)
    
    def ilike(self, column, pattern):
        """Like insensible a mayúsculas"""
        return self.where(column, 'ilike', pattern)
    
    def in_(self, column, values):
        """IN (lista de valores)"""
        return self.where(column, 'in', values)
    
    def is_null(self, column):
        """IS NULL"""
        return self.where(column, 'is', None)
    
    def is_not_null(self, column):
        """IS NOT NULL"""
        return self.where(column, 'is', 'not.null')
    
    def order(self, column, ascending=True):
        """Ordenar resultados"""
        self.order_by = (column, ascending)
        return self
    
    def limit(self, limit):
        """Limitar resultados"""
        self.limit_value = limit
        return self
    
    def offset(self, offset):
        """Desplazar resultados"""
        self.offset_value = offset
        return self
    
    def execute(self):
        """Ejecutar la consulta"""
        try:
            supabase = get_supabase()
            query = supabase.table(self.table).select(self.select_fields)
            
            # Aplicar filtros
            for column, operator, value in self.filters:
                if operator == 'eq':
                    query = query.eq(column, value)
                elif operator == 'neq':
                    query = query.neq(column, value)
                elif operator == 'gt':
                    query = query.gt(column, value)
                elif operator == 'gte':
                    query = query.gte(column, value)
                elif operator == 'lt':
                    query = query.lt(column, value)
                elif operator == 'lte':
                    query = query.lte(column, value)
                elif operator == 'like':
                    query = query.like(column, value)
                elif operator == 'ilike':
                    query = query.ilike(column, value)
                elif operator == 'in':
                    query = query.in_(column, value)
                elif operator == 'is':
                    if value is None:
                        query = query.is_(column, None)
                    else:
                        query = query.is_(column, value)
            
            # Aplicar orden
            if self.order_by:
                column, ascending = self.order_by
                query = query.order(column, desc=not ascending)
            
            # Aplicar límite y offset
            if self.limit_value is not None:
                query = query.limit(self.limit_value)
            if self.offset_value is not None:
                query = query.offset(self.offset_value)
            
            return query.execute()
        except Exception as e:
            logger.error(f'Error ejecutando consulta Supabase: {str(e)}')
            raise

def query(table):
    """Crear una nueva consulta"""
    return SupabaseQuery(table)