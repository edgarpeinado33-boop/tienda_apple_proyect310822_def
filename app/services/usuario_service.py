"""
Servicio de Usuario
Maneja toda la lógica de negocio relacionada con usuarios
"""
from app.utils.supabase_client import get_supabase, get_supabase_service
from app.utils.security import hash_password, verify_password, generate_token, sanitize_email
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UsuarioService:
    """Servicio para operaciones con usuarios"""
    
    @staticmethod
    def get_all(page=1, per_page=20, search=None):
        """Obtener todos los usuarios con paginación"""
        try:
            supabase = get_supabase_service()
            start = (page - 1) * per_page
            
            query = supabase.table('USUARIO').select('*, USUARIO_ROL(ROL(nombre_rol))')
            
            if search:
                query = query.or_(f"nombre_completo.ilike.%{search}%,email.ilike.%{search}%")
            
            query = query.range(start, start + per_page - 1).order('fecha_registro', desc=True)
            result = query.execute()
            
            # Contar total
            count_query = supabase.table('USUARIO').select('*', count='exact')
            if search:
                count_query = count_query.or_(f"nombre_completo.ilike.%{search}%,email.ilike.%{search}%")
            count_result = count_query.execute()
            
            return {
                'usuarios': result.data,
                'total': count_result.count,
                'page': page,
                'per_page': per_page,
                'total_pages': (count_result.count + per_page - 1) // per_page
            }
        except Exception as e:
            logger.error(f'Error obteniendo usuarios: {str(e)}')
            raise
    
    @staticmethod
    def get_by_id(user_id):
        """Obtener usuario por ID"""
        try:
            supabase = get_supabase()
            result = supabase.table('USUARIO')\
                .select('*, USUARIO_ROL(ROL(*)), PERFIL_USUARIO(*)')\
                .eq('id_usuario', user_id)\
                .execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f'Error obteniendo usuario: {str(e)}')
            raise
    
    @staticmethod
    def get_by_email(email):
        """Obtener usuario por email"""
        try:
            supabase = get_supabase()
            result = supabase.table('USUARIO')\
                .select('*')\
                .eq('email', sanitize_email(email))\
                .execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f'Error obteniendo usuario por email: {str(e)}')
            raise
    
    @staticmethod
    def create(nombre_completo, email, password, telefono=None):
        """Crear nuevo usuario"""
        try:
            supabase = get_supabase()
            
            # Sanitizar
            email = sanitize_email(email)
            
            # Verificar que no exista
            existing = UsuarioService.get_by_email(email)
            if existing:
                raise Exception('El email ya está registrado')
            
            # Hashear contraseña
            hashed, salt = hash_password(password)
            
            # Crear usuario
            user_data = {
                'nombre_completo': nombre_completo.strip(),
                'email': email,
                'contrasena_hash': hashed,
                'salt': salt,
                'telefono': telefono,
                'fecha_registro': datetime.now().date().isoformat()
            }
            
            result = supabase.table('USUARIO')\
                .insert(user_data)\
                .execute()
            
            if result.data:
                user_id = result.data[0]['id_usuario']
                
                # Asignar rol CLIENTE
                UsuarioService.assign_role(user_id, 'CLIENTE')
                
                # Crear perfil
                UsuarioService.create_profile(user_id)
                
                # Crear dirección predeterminada
                UsuarioService.create_default_address(user_id)
                
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f'Error creando usuario: {str(e)}')
            raise
    
    @staticmethod
    def update(user_id, data):
        """Actualizar usuario"""
        try:
            supabase = get_supabase()
            
            # Limpiar datos
            clean_data = {}
            for key, value in data.items():
                if value is not None:
                    if key == 'email':
                        clean_data[key] = sanitize_email(value)
                    elif key == 'nombre_completo':
                        clean_data[key] = value.strip()
                    else:
                        clean_data[key] = value
            
            result = supabase.table('USUARIO')\
                .update(clean_data)\
                .eq('id_usuario', user_id)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f'Error actualizando usuario: {str(e)}')
            raise
    
    @staticmethod
    def change_password(user_id, old_password, new_password):
        """Cambiar contraseña del usuario"""
        try:
            supabase = get_supabase()
            
            # Obtener usuario
            user = UsuarioService.get_by_id(user_id)
            if not user:
                raise Exception('Usuario no encontrado')
            
            # Verificar contraseña actual
            if not verify_password(old_password, user['contrasena_hash']):
                raise Exception('Contraseña actual incorrecta')
            
            # Hashear nueva contraseña
            hashed, salt = hash_password(new_password)
            
            # Actualizar
            result = supabase.table('USUARIO')\
                .update({
                    'contrasena_hash': hashed,
                    'salt': salt
                })\
                .eq('id_usuario', user_id)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f'Error cambiando contraseña: {str(e)}')
            raise
    
    @staticmethod
    def toggle_active(user_id):
        """Activar/desactivar usuario"""
        try:
            supabase = get_supabase_service()
            
            # Obtener estado actual
            user = UsuarioService.get_by_id(user_id)
            if not user:
                raise Exception('Usuario no encontrado')
            
            nuevo_estado = not user['activo']
            
            result = supabase.table('USUARIO')\
                .update({'activo': nuevo_estado})\
                .eq('id_usuario', user_id)\
                .execute()
            
            return {
                'activo': nuevo_estado,
                'usuario': result.data[0] if result.data else None
            }
        except Exception as e:
            logger.error(f'Error cambiando estado del usuario: {str(e)}')
            raise
    
    @staticmethod
    def assign_role(user_id, role_name):
        """Asignar rol a usuario"""
        try:
            supabase = get_supabase()
            
            # Obtener ID del rol
            role_result = supabase.table('ROL')\
                .select('id_rol')\
                .eq('nombre_rol', role_name)\
                .execute()
            
            if not role_result.data:
                raise Exception(f'Rol {role_name} no encontrado')
            
            role_id = role_result.data[0]['id_rol']
            
            # Verificar si ya tiene el rol
            existing = supabase.table('USUARIO_ROL')\
                .select('*')\
                .eq('id_usuario', user_id)\
                .eq('id_rol', role_id)\
                .execute()
            
            if existing.data:
                # Reactivar si existe
                result = supabase.table('USUARIO_ROL')\
                    .update({'activo': True})\
                    .eq('id_usuario_rol', existing.data[0]['id_usuario_rol'])\
                    .execute()
            else:
                # Asignar rol
                role_data = {
                    'id_usuario': user_id,
                    'id_rol': role_id,
                    'activo': True
                }
                result = supabase.table('USUARIO_ROL')\
                    .insert(role_data)\
                    .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f'Error asignando rol: {str(e)}')
            raise
    
    @staticmethod
    def remove_role(user_id, role_id):
        """Eliminar rol de usuario"""
        try:
            supabase = get_supabase()
            
            result = supabase.table('USUARIO_ROL')\
                .update({'activo': False})\
                .eq('id_usuario', user_id)\
                .eq('id_rol', role_id)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f'Error eliminando rol: {str(e)}')
            raise
    
    @staticmethod
    def create_profile(user_id):
        """Crear perfil de usuario"""
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
            
            result = supabase.table('PERFIL_USUARIO')\
                .insert(profile_data)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f'Error creando perfil: {str(e)}')
            raise
    
    @staticmethod
    def update_profile(user_id, data):
        """Actualizar perfil de usuario"""
        try:
            supabase = get_supabase()
            
            result = supabase.table('PERFIL_USUARIO')\
                .update(data)\
                .eq('id_usuario', user_id)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f'Error actualizando perfil: {str(e)}')
            raise
    
    @staticmethod
    def create_default_address(user_id):
        """Crear dirección predeterminada"""
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
            
            result = supabase.table('DIRECCION_ENVIO')\
                .insert(address_data)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f'Error creando dirección: {str(e)}')
            raise
    
    @staticmethod
    def get_addresses(user_id):
        """Obtener direcciones del usuario"""
        try:
            supabase = get_supabase()
            result = supabase.table('DIRECCION_ENVIO')\
                .select('*')\
                .eq('id_usuario', user_id)\
                .eq('activa', True)\
                .order('predeterminada', desc=True)\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f'Error obteniendo direcciones: {str(e)}')
            raise
    
    @staticmethod
    def add_address(user_id, address_data):
        """Agregar dirección de envío"""
        try:
            supabase = get_supabase()
            
            # Si es predeterminada, quitar predeterminada de otras
            if address_data.get('predeterminada'):
                supabase.table('DIRECCION_ENVIO')\
                    .update({'predeterminada': False})\
                    .eq('id_usuario', user_id)\
                    .execute()
            
            address_data['id_usuario'] = user_id
            result = supabase.table('DIRECCION_ENVIO')\
                .insert(address_data)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f'Error agregando dirección: {str(e)}')
            raise
    
    @staticmethod
    def delete_address(user_id, address_id):
        """Eliminar dirección de envío"""
        try:
            supabase = get_supabase()
            
            result = supabase.table('DIRECCION_ENVIO')\
                .update({'activa': False})\
                .eq('id_direccion', address_id)\
                .eq('id_usuario', user_id)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f'Error eliminando dirección: {str(e)}')
            raise
    
    @staticmethod
    def get_estadisticas():
        """Obtener estadísticas de usuarios"""
        try:
            supabase = get_supabase_service()
            
            # Total usuarios
            total = supabase.table('USUARIO').select('*', count='exact').execute()
            
            # Usuarios activos
            activos = supabase.table('USUARIO')\
                .select('*', count='exact')\
                .eq('activo', True)\
                .execute()
            
            # Verificados
            verificados = supabase.table('USUARIO')\
                .select('*', count='exact')\
                .eq('email_verificado', True)\
                .execute()
            
            # Registros del mes
            inicio_mes = datetime.now().replace(day=1).date().isoformat()
            nuevos_mes = supabase.table('USUARIO')\
                .select('*', count='exact')\
                .gte('fecha_registro', inicio_mes)\
                .execute()
            
            return {
                'total': total.count,
                'activos': activos.count,
                'verificados': verificados.count,
                'nuevos_mes': nuevos_mes.count
            }
        except Exception as e:
            logger.error(f'Error obteniendo estadísticas: {str(e)}')
            raise