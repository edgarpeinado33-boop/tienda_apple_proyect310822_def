"""
Modelo de Usuario
"""
from flask_login import UserMixin
from datetime import datetime
from app.utils.supabase_client import get_supabase
from app.utils.security import verify_password, hash_password
import logging

logger = logging.getLogger(__name__)

class Usuario(UserMixin):
    """Modelo de Usuario con autenticación"""
    
    def __init__(self, data=None):
        if data:
            self.id = data.get('id_usuario')
            self.nombre_completo = data.get('nombre_completo')
            self.email = data.get('email')
            self.contrasena_hash = data.get('contrasena_hash')
            self.salt = data.get('salt')
            self.telefono = data.get('telefono')
            self.fecha_registro = data.get('fecha_registro')
            self.ultimo_acceso = data.get('ultimo_acceso')
            self.email_verificado = data.get('email_verificado', False)
            self.activo = data.get('activo', True)
            self.token_recuperacion = data.get('token_recuperacion')
            self.token_expiracion = data.get('token_expiracion')
            self.ip_registro = data.get('ip_registro')
            self.pregunta_seguridad = data.get('pregunta_seguridad')
            self.respuesta_seguridad_hash = data.get('respuesta_seguridad_hash')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')
            self._roles = None
            self._perfil = None
            self._is_admin = None
    
    def get_id(self):
        return str(self.id)
    
    def is_active(self):
        return self.activo and self.email_verificado
    
    def is_authenticated(self):
        return True
    
    def is_anonymous(self):
        return False
    
    @property
    def is_admin(self):
        """Verifica si el usuario tiene rol de administrador."""
        if self._is_admin is None:
            roles = self.get_roles()
            admin_roles = ['SUPER_ADMIN', 'ADMIN_TIENDA', 'ADMIN_PEDIDOS', 'ADMIN_PRODUCTOS', 'ADMIN_FACTURACION']
            self._is_admin = any(role in admin_roles for role in roles)
        return self._is_admin
    
    def has_role(self, role_name):
        roles = self.get_roles()
        return role_name in roles
    
    def get_roles(self):
        if self._roles is not None:
            return self._roles
        try:
            supabase = get_supabase()
            result = supabase.table('usuario_rol')\
                .select('rol(nombre_rol)')\
                .eq('id_usuario', self.id)\
                .eq('activo', True)\
                .execute()
            self._roles = [item['rol']['nombre_rol'] for item in result.data if item.get('rol')]
            return self._roles
        except Exception as e:
            logger.error(f'Error obteniendo roles: {str(e)}')
            return []
    
    def get_perfil(self):
        if self._perfil is not None:
            return self._perfil
        try:
            supabase = get_supabase()
            result = supabase.table('perfil_usuario')\
                .select('*')\
                .eq('id_usuario', self.id)\
                .execute()
            if result.data:
                self._perfil = result.data[0]
                return self._perfil
            return None
        except Exception as e:
            logger.error(f'Error obteniendo perfil: {str(e)}')
            return None
    
    def get_direcciones(self):
        try:
            supabase = get_supabase()
            result = supabase.table('direccion_envio')\
                .select('*')\
                .eq('id_usuario', self.id)\
                .eq('activa', True)\
                .order('predeterminada', desc=True)\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f'Error obteniendo direcciones: {str(e)}')
            return []
    
    def get_direccion_predeterminada(self):
        direcciones = self.get_direcciones()
        for direccion in direcciones:
            if direccion.get('predeterminada'):
                return direccion
        return direcciones[0] if direcciones else None
    
    def to_dict(self):
        return {
            'id_usuario': self.id,
            'nombre_completo': self.nombre_completo,
            'email': self.email,
            'telefono': self.telefono,
            'fecha_registro': self.fecha_registro,
            'email_verificado': self.email_verificado,
            'activo': self.activo,
            'roles': self.get_roles(),
            'is_admin': self.is_admin,
            'created_at': self.created_at
        }
    
    @staticmethod
    def find_by_email(email):
        try:
            supabase = get_supabase()
            result = supabase.table('usuario')\
                .select('*')\
                .eq('email', email)\
                .execute()
            if result.data and len(result.data) > 0:
                return Usuario(result.data[0])
            return None
        except Exception as e:
            logger.error(f'Error buscando usuario por email: {str(e)}')
            return None
    
    @staticmethod
    def find_by_id(user_id):
        try:
            supabase = get_supabase()
            result = supabase.table('usuario')\
                .select('*')\
                .eq('id_usuario', user_id)\
                .execute()
            if result.data and len(result.data) > 0:
                return Usuario(result.data[0])
            return None
        except Exception as e:
            logger.error(f'Error buscando usuario por ID: {str(e)}')
            return None
    
    @staticmethod
    def create_user(nombre_completo, email, password, telefono=None):
        try:
            supabase = get_supabase()
            hashed, salt = hash_password(password)
            user_data = {
                'nombre_completo': nombre_completo,
                'email': email,
                'contrasena_hash': hashed,
                'salt': salt,
                'telefono': telefono,
                'fecha_registro': datetime.now().date().isoformat(),
                'email_verificado': True,
                'activo': True
            }
            result = supabase.table('usuario')\
                .insert(user_data)\
                .execute()
            if result.data and len(result.data) > 0:
                user_id = result.data[0]['id_usuario']
                try:
                    Usuario.assign_role(user_id, 'CLIENTE')
                except Exception as e:
                    logger.error(f'Error asignando rol: {str(e)}')
                try:
                    Usuario.create_profile(user_id)
                except Exception as e:
                    logger.error(f'Error creando perfil: {str(e)}')
                try:
                    Usuario.create_default_address(user_id)
                except Exception as e:
                    logger.error(f'Error creando dirección: {str(e)}')
                return Usuario(result.data[0])
            return None
        except Exception as e:
            logger.error(f'Error creando usuario: {str(e)}')
            raise
    
    @staticmethod
    def assign_role(user_id, role_name):
        try:
            supabase = get_supabase()
            role_result = supabase.table('rol')\
                .select('id_rol')\
                .eq('nombre_rol', role_name)\
                .execute()
            if not role_result.data:
                raise Exception(f'Rol {role_name} no encontrado')
            role_id = role_result.data[0]['id_rol']
            existing = supabase.table('usuario_rol')\
                .select('*')\
                .eq('id_usuario', user_id)\
                .eq('id_rol', role_id)\
                .execute()
            if existing.data:
                supabase.table('usuario_rol')\
                    .update({'activo': True})\
                    .eq('id_usuario_rol', existing.data[0]['id_usuario_rol'])\
                    .execute()
            else:
                role_data = {
                    'id_usuario': user_id,
                    'id_rol': role_id,
                    'activo': True
                }
                supabase.table('usuario_rol')\
                    .insert(role_data)\
                    .execute()
            return True
        except Exception as e:
            logger.error(f'Error asignando rol: {str(e)}')
            raise
    
    @staticmethod
    def create_profile(user_id):
        try:
            supabase = get_supabase()
            profile_data = {
                'id_usuario': user_id,
                'pais': 'España',
                'idioma_preferido': 'es',
                'zona_horaria': 'Europe/Madrid',
                'notificaciones_email': True,
                'notificaciones_push': True,
                'tema_preferido': 'light'
            }
            supabase.table('perfil_usuario')\
                .insert(profile_data)\
                .execute()
            return True
        except Exception as e:
            logger.error(f'Error creando perfil: {str(e)}')
            return False
    
    @staticmethod
    def create_default_address(user_id):
        try:
            supabase = get_supabase()
            address_data = {
                'id_usuario': user_id,
                'nombre_direccion': 'Dirección Principal',
                'calle': 'Calle Principal 1',
                'ciudad': 'Madrid',
                'codigo_postal': '28001',
                'pais': 'España',
                'predeterminada': True,
                'activa': True
            }
            supabase.table('direccion_envio')\
                .insert(address_data)\
                .execute()
            return True
        except Exception as e:
            logger.error(f'Error creando dirección: {str(e)}')
            return False
    
    @staticmethod
    def authenticate(email, password):
        user = Usuario.find_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.contrasena_hash):
            return None
        if not user.activo:
            return None
        if not user.email_verificado:
            return None
        try:
            supabase = get_supabase()
            supabase.table('usuario')\
                .update({'ultimo_acceso': datetime.now().isoformat()})\
                .eq('id_usuario', user.id)\
                .execute()
        except Exception as e:
            logger.error(f'Error actualizando último acceso: {str(e)}')
        return user