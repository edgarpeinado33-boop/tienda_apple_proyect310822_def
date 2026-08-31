"""
Controlador de Autenticación
Maneja login, registro, perfil y cierre de sesión
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app, make_response
from flask_login import login_user, logout_user, login_required, current_user
from app.models.usuario import Usuario
from app.utils.security import generate_token, sanitize_input, verify_token
from app.utils.supabase_client import get_supabase
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    if current_user.is_authenticated:
        return redirect(url_for('producto.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not email or not password:
            flash('Por favor ingresa tu email y contraseña', 'warning')
            return render_template('auth/login.html')
        
        # === DEPURACIÓN: LOGS ===
        logger.info(f'🔍 Intento de login para email: {email}')
        
        # Buscar usuario manualmente para depurar
        user_obj = Usuario.find_by_email(email)
        if user_obj:
            logger.info(f'✅ Usuario encontrado: {user_obj.nombre_completo}')
            logger.info(f'   - Activo: {user_obj.activo}')
            logger.info(f'   - Email verificado: {user_obj.email_verificado}')
            logger.info(f'   - ID: {user_obj.id}')
            
            # Verificar contraseña manualmente
            from app.utils.security import verify_password
            es_valida = verify_password(password, user_obj.contrasena_hash)
            logger.info(f'   - Contraseña válida: {es_valida}')
            
            if not es_valida:
                flash('Email o contraseña incorrectos', 'danger')
                return render_template('auth/login.html')
            
            if not user_obj.activo:
                flash('Tu cuenta está desactivada. Contacta con soporte.', 'danger')
                return render_template('auth/login.html')
            
            if not user_obj.email_verificado:
                flash('Debes verificar tu email antes de iniciar sesión. Revisa tu bandeja de entrada.', 'warning')
                return render_template('auth/login.html')
            
            # Si todo está bien, iniciar sesión
            login_user(user_obj, remember=remember)
            flash(f'¡Bienvenido {user_obj.nombre_completo}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('producto.index'))
        else:
            logger.warning(f'❌ Usuario no encontrado con email: {email}')
            flash('Email o contraseña incorrectos', 'danger')
    
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro de usuarios"""
    if current_user.is_authenticated:
        return redirect(url_for('producto.index'))
    
    if request.method == 'POST':
        nombre_completo = request.form.get('nombre_completo', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        telefono = request.form.get('telefono', '').strip()
        terms = request.form.get('terms', False)
        
        # Validaciones
        if not nombre_completo or not email or not password:
            flash('Todos los campos requeridos deben ser llenados', 'warning')
            return render_template('auth/register.html')
        
        if len(nombre_completo) < 3:
            flash('El nombre debe tener al menos 3 caracteres', 'warning')
            return render_template('auth/register.html')
        
        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'warning')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'warning')
            return render_template('auth/register.html')
        
        if not terms:
            flash('Debes aceptar los términos y condiciones', 'warning')
            return render_template('auth/register.html')
        
        # Sanitizar inputs
        nombre_completo = sanitize_input(nombre_completo)
        email = sanitize_input(email)
        
        try:
            # Crear usuario
            user = Usuario.create_user(nombre_completo, email, password, telefono)
            if user:
                logger.info(f'✅ Usuario registrado: {email}')
                flash('¡Registro exitoso! Por favor inicia sesión', 'success')
                return redirect(url_for('auth.login'))
        except Exception as e:
            if 'duplicate key' in str(e) or 'unique constraint' in str(e).lower():
                flash('Este email ya está registrado', 'danger')
            else:
                flash('Error al registrar usuario. Por favor intenta nuevamente', 'danger')
                logger.error(f'Error en registro: {str(e)}')
    
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    try:
        supabase = get_supabase()
        supabase.table('sesion')\
            .update({
                'estado': 'cerrada', 
                'fecha_cierre': datetime.now().isoformat()
            })\
            .eq('id_usuario', current_user.id)\
            .eq('estado', 'activa')\
            .execute()
    except Exception as e:
        logger.error(f'Error cerrando sesión en Supabase: {str(e)}')
    
    logout_user()
    session.clear()
    session.modified = True
    
    response = make_response(redirect(url_for('auth.login')))
    response.set_cookie('session', '', expires=0)
    response.set_cookie('remember_token', '', expires=0)
    
    flash('Sesión cerrada exitosamente', 'success')
    return response


@auth_bp.route('/logout/force')
def force_logout():
    """Forzar cierre de sesión (sin login_required)"""
    logout_user()
    session.clear()
    session.modified = True
    
    response = make_response(redirect(url_for('auth.login')))
    response.set_cookie('session', '', expires=0)
    response.set_cookie('remember_token', '', expires=0)
    
    flash('Sesión cerrada exitosamente', 'success')
    return response


@auth_bp.route('/profile')
@login_required
def profile():
    """Perfil de usuario"""
    try:
        supabase = get_supabase()
        
        perfil = supabase.table('perfil_usuario')\
            .select('*')\
            .eq('id_usuario', current_user.id)\
            .execute()
        
        direcciones = supabase.table('direccion_envio')\
            .select('*')\
            .eq('id_usuario', current_user.id)\
            .eq('activa', True)\
            .execute()
        
        pedidos = supabase.table('pedido')\
            .select('*')\
            .eq('id_usuario', current_user.id)\
            .order('fecha_pedido', desc=True)\
            .limit(5)\
            .execute()
        
        return render_template('auth/profile.html',
                             user=current_user,
                             perfil=perfil.data[0] if perfil.data else None,
                             direcciones=direcciones.data,
                             pedidos=pedidos.data)
    except Exception as e:
        logger.error(f'Error cargando perfil: {str(e)}')
        flash('Error cargando el perfil', 'danger')
        return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Actualizar perfil de usuario"""
    try:
        supabase = get_supabase()
        
        nombre_completo = request.form.get('nombre_completo', '').strip()
        telefono = request.form.get('telefono', '').strip()
        
        if not nombre_completo:
            flash('El nombre es requerido', 'warning')
            return redirect(url_for('auth.profile'))
        
        supabase.table('usuario')\
            .update({
                'nombre_completo': nombre_completo,
                'telefono': telefono
            })\
            .eq('id_usuario', current_user.id)\
            .execute()
        
        perfil_data = {
            'direccion': request.form.get('direccion', ''),
            'ciudad': request.form.get('ciudad', ''),
            'codigo_postal': request.form.get('codigo_postal', ''),
            'pais': request.form.get('pais', 'España'),
            'provincia': request.form.get('provincia', ''),
            'empresa': request.form.get('empresa', ''),
            'cargo': request.form.get('cargo', ''),
            'idioma_preferido': request.form.get('idioma_preferido', 'es'),
            'tema_preferido': request.form.get('tema_preferido', 'light'),
            'notificaciones_email': request.form.get('notificaciones_email') == 'on',
            'notificaciones_push': request.form.get('notificaciones_push') == 'on'
        }
        
        supabase.table('perfil_usuario')\
            .update(perfil_data)\
            .eq('id_usuario', current_user.id)\
            .execute()
        
        flash('Perfil actualizado exitosamente', 'success')
    except Exception as e:
        logger.error(f'Error actualizando perfil: {str(e)}')
        flash('Error actualizando el perfil', 'danger')
    
    return redirect(url_for('auth.profile'))


@auth_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """Cambiar contraseña"""
    try:
        supabase = get_supabase()
        from app.utils.security import hash_password, verify_password
        
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not current_password or not new_password or not confirm_password:
            flash('Todos los campos son requeridos', 'warning')
            return redirect(url_for('auth.profile'))
        
        if len(new_password) < 8:
            flash('La nueva contraseña debe tener al menos 8 caracteres', 'warning')
            return redirect(url_for('auth.profile'))
        
        if new_password != confirm_password:
            flash('Las contraseñas no coinciden', 'warning')
            return redirect(url_for('auth.profile'))
        
        user = Usuario.find_by_id(current_user.id)
        if not verify_password(current_password, user.contrasena_hash):
            flash('Contraseña actual incorrecta', 'danger')
            return redirect(url_for('auth.profile'))
        
        hashed, salt = hash_password(new_password)
        
        supabase.table('usuario')\
            .update({
                'contrasena_hash': hashed,
                'salt': salt
            })\
            .eq('id_usuario', current_user.id)\
            .execute()
        
        flash('Contraseña actualizada exitosamente', 'success')
    except Exception as e:
        logger.error(f'Error cambiando contraseña: {str(e)}')
        flash('Error cambiando la contraseña', 'danger')
    
    return redirect(url_for('auth.profile'))


@auth_bp.route('/profile/address/add', methods=['POST'])
@login_required
def add_address():
    """Agregar nueva dirección de envío"""
    try:
        supabase = get_supabase()
        
        address_data = {
            'id_usuario': current_user.id,
            'nombre_direccion': request.form.get('nombre_direccion', '').strip(),
            'calle': request.form.get('calle', '').strip(),
            'numero': request.form.get('numero', '').strip(),
            'complemento': request.form.get('complemento', '').strip(),
            'ciudad': request.form.get('ciudad', '').strip(),
            'estado_provincia': request.form.get('estado_provincia', '').strip(),
            'codigo_postal': request.form.get('codigo_postal', '').strip(),
            'pais': request.form.get('pais', 'España'),
            'telefono_contacto': request.form.get('telefono_contacto', '').strip(),
            'instrucciones_entrega': request.form.get('instrucciones_entrega', '').strip(),
            'tipo_direccion': request.form.get('tipo_direccion', 'casa'),
            'predeterminada': request.form.get('predeterminada') == 'on',
            'activa': True
        }
        
        if address_data['predeterminada']:
            supabase.table('direccion_envio')\
                .update({'predeterminada': False})\
                .eq('id_usuario', current_user.id)\
                .execute()
        
        result = supabase.table('direccion_envio')\
            .insert(address_data)\
            .execute()
        
        if result.data:
            flash('Dirección agregada exitosamente', 'success')
        else:
            flash('Error agregando dirección', 'danger')
    except Exception as e:
        logger.error(f'Error agregando dirección: {str(e)}')
        flash('Error agregando la dirección', 'danger')
    
    return redirect(url_for('auth.profile'))


@auth_bp.route('/profile/address/delete/<address_id>', methods=['POST'])
@login_required
def delete_address(address_id):
    """Eliminar dirección de envío"""
    try:
        supabase = get_supabase()
        
        result = supabase.table('direccion_envio')\
            .delete()\
            .eq('id_direccion', address_id)\
            .eq('id_usuario', current_user.id)\
            .execute()
        
        if result.data:
            flash('Dirección eliminada exitosamente', 'success')
        else:
            flash('Error eliminando dirección', 'danger')
    except Exception as e:
        logger.error(f'Error eliminando dirección: {str(e)}')
        flash('Error eliminando la dirección', 'danger')
    
    return redirect(url_for('auth.profile'))


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Verificar email con token"""
    try:
        payload = verify_token(token)
        user_id = payload.get('user_id')
        
        if not user_id:
            flash('Token inválido', 'danger')
            return redirect(url_for('auth.login'))
        
        supabase = get_supabase()
        
        user = supabase.table('usuario')\
            .select('*')\
            .eq('id_usuario', user_id)\
            .execute()
        
        if not user.data:
            flash('Usuario no encontrado', 'danger')
            return redirect(url_for('auth.login'))
        
        supabase.table('usuario')\
            .update({'email_verificado': True})\
            .eq('id_usuario', user_id)\
            .execute()
        
        flash('Email verificado exitosamente', 'success')
    except Exception as e:
        logger.error(f'Error verificando email: {str(e)}')
        flash('Error verificando el email', 'danger')
    
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Recuperar contraseña"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Por favor ingresa tu email', 'warning')
            return render_template('auth/forgot_password.html')
        
        try:
            supabase = get_supabase()
            
            user = supabase.table('usuario')\
                .select('*')\
                .eq('email', email)\
                .execute()
            
            if user.data:
                token = generate_token(user.data[0]['id_usuario'], expires_in=3600)
                
                supabase.table('usuario')\
                    .update({
                        'token_recuperacion': token,
                        'token_expiracion': (datetime.now().timestamp() + 3600)
                    })\
                    .eq('id_usuario', user.data[0]['id_usuario'])\
                    .execute()
                
                flash('Se ha enviado un enlace de recuperación a tu email', 'success')
            else:
                flash('No se encontró un usuario con este email', 'warning')
        except Exception as e:
            logger.error(f'Error en recuperación de contraseña: {str(e)}')
            flash('Error procesando la solicitud', 'danger')
    
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Restablecer contraseña"""
    try:
        payload = verify_token(token)
        user_id = payload.get('user_id')
        
        if not user_id:
            flash('Token inválido o expirado', 'danger')
            return redirect(url_for('auth.login'))
        
        if request.method == 'POST':
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if len(password) < 8:
                flash('La contraseña debe tener al menos 8 caracteres', 'warning')
                return render_template('auth/reset_password.html', token=token)
            
            if password != confirm_password:
                flash('Las contraseñas no coinciden', 'warning')
                return render_template('auth/reset_password.html', token=token)
            
            from app.utils.security import hash_password
            hashed, salt = hash_password(password)
            
            supabase = get_supabase()
            supabase.table('usuario')\
                .update({
                    'contrasena_hash': hashed,
                    'salt': salt,
                    'token_recuperacion': None,
                    'token_expiracion': None
                })\
                .eq('id_usuario', user_id)\
                .execute()
            
            flash('Contraseña actualizada exitosamente', 'success')
            return redirect(url_for('auth.login'))
        
        return render_template('auth/reset_password.html', token=token)
    except Exception as e:
        logger.error(f'Error en reset de contraseña: {str(e)}')
        flash('Error procesando la solicitud', 'danger')
        return redirect(url_for('auth.login'))