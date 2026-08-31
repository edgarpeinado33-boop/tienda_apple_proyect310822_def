/**
 * JavaScript principal - Estilo Apple
 * Maneja el carrito de compras, notificaciones y funcionalidades interactivas
 */

$(document).ready(function() {
    console.log('🍎 Tienda Apple iniciada');
    
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Actualizar badge del carrito al cargar
    actualizarBadgeCarrito();
    
    // Búsqueda overlay
    $('#searchToggle').on('click', function(e) {
        e.preventDefault();
        $('#searchOverlay').addClass('active');
        setTimeout(function() {
            $('.search-input').focus();
        }, 300);
    });
    
    $('#searchClose').on('click', function() {
        $('#searchOverlay').removeClass('active');
    });
    
    $('#searchOverlay').on('click', function(e) {
        if (e.target === this) {
            $(this).removeClass('active');
        }
    });
    
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape') {
            $('#searchOverlay').removeClass('active');
        }
    });
    
    // ============================================
    // AGREGAR AL CARRITO
    // ============================================
    $('.btn-agregar-carrito').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const varianteId = $(this).data('variante-id');
        const productoId = $(this).data('producto-id');
        const cantidad = $(this).data('cantidad') || 1;
        const $btn = $(this);
        
        $btn.prop('disabled', true);
        $btn.html('<i class="fas fa-spinner fa-spin me-1"></i> Agregando...');
        
        function ejecutarAgregar(idVariante) {
            if (!idVariante) {
                mostrarNotificacion('⚠️ Producto no disponible', 'warning');
                $btn.prop('disabled', false);
                $btn.html('<i class="fas fa-plus me-1"></i> Agregar');
                return;
            }
            
            agregarAlCarrito(idVariante, cantidad, function() {
                $btn.prop('disabled', false);
                $btn.html('<i class="fas fa-plus me-1"></i> Agregar');
            });
        }
        
        if (varianteId) {
            ejecutarAgregar(varianteId);
            return;
        }
        
        if (productoId) {
            $.ajax({
                url: `/productos/${productoId}/variante`,
                method: 'GET',
                success: function(response) {
                    if (response.id_variante) {
                        ejecutarAgregar(response.id_variante);
                    } else {
                        mostrarNotificacion('⚠️ Este producto no está disponible', 'warning');
                        $btn.prop('disabled', false);
                        $btn.html('<i class="fas fa-plus me-1"></i> Agregar');
                    }
                },
                error: function() {
                    mostrarNotificacion('⚠️ Producto no disponible', 'warning');
                    $btn.prop('disabled', false);
                    $btn.html('<i class="fas fa-plus me-1"></i> Agregar');
                }
            });
            return;
        }
        
        mostrarNotificacion('⚠️ Producto no disponible', 'warning');
        $btn.prop('disabled', false);
        $btn.html('<i class="fas fa-plus me-1"></i> Agregar');
    });
    
    // ============================================
    // ACTUALIZAR CANTIDAD
    // ============================================
    $(document).on('click', '.update-cart', function() {
        const lineaId = $(this).data('linea-id');
        const cantidad = $(this).data('cantidad');
        const $btn = $(this);
        
        if (cantidad <= 0) {
            if (!confirm('¿Eliminar este producto del carrito?')) return;
        }
        
        $btn.prop('disabled', true);
        $btn.html('<i class="fas fa-spinner fa-spin"></i>');
        
        actualizarCantidadCarrito(lineaId, cantidad, function() {
            $btn.prop('disabled', false);
            $btn.html('<i class="fas fa-minus"></i>');
        });
    });
    
    // ============================================
    // ELIMINAR PRODUCTO
    // ============================================
    $(document).on('click', '.remove-cart', function() {
        if (!confirm('¿Eliminar este producto del carrito?')) return;
        
        const lineaId = $(this).data('linea-id');
        const $btn = $(this);
        
        $btn.prop('disabled', true);
        $btn.html('<i class="fas fa-spinner fa-spin"></i>');
        
        eliminarDelCarrito(lineaId, function() {
            $btn.prop('disabled', false);
            $btn.html('<i class="fas fa-trash"></i>');
        });
    });
    
    // ============================================
    // VACIAR CARRITO - CON CONFIRMACIÓN
    // ============================================
    $(document).on('click', '#vaciarCarrito', function(e) {
        e.preventDefault();
        if (!confirm('¿Estás seguro de que quieres vaciar el carrito?')) return;
        
        const $btn = $(this);
        $btn.prop('disabled', true);
        $btn.html('<i class="fas fa-spinner fa-spin me-1"></i> Vaciando...');
        
        vaciarCarrito(function() {
            $btn.prop('disabled', false);
            $btn.html('<i class="fas fa-trash me-2"></i> Vaciar carrito');
        });
    });
    
    // Auto-ocultar alertas
    setTimeout(function() {
        $('.alert:not(.permanent)').fadeOut('slow', function() {
            $(this).remove();
        });
    }, 5000);
});

// ============================================
// FUNCIONES GLOBALES
// ============================================

function agregarAlCarrito(varianteId, cantidad, callback) {
    const csrfToken = $('input[name="csrf_token"]').val() || $('meta[name="csrf-token"]').attr('content');
    
    $.ajax({
        url: '/carrito/agregar',
        method: 'POST',
        data: {
            variante_id: varianteId,
            cantidad: cantidad,
            csrf_token: csrfToken
        },
        success: function(response) {
            if (response.success) {
                actualizarBadgeCarrito();
                mostrarNotificacion('✅ Producto agregado al carrito', 'success');
                setTimeout(function() {
                    location.reload();
                }, 500);
            } else {
                mostrarNotificacion('⚠️ ' + (response.message || 'Error al agregar'), 'warning');
            }
            if (callback) callback();
        },
        error: function(xhr) {
            let mensaje = 'Error al agregar al carrito';
            if (xhr.status === 401) {
                mensaje = '⚠️ Debes iniciar sesión para agregar productos';
                mostrarNotificacion(mensaje, 'warning');
                setTimeout(function() {
                    window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname);
                }, 1500);
                if (callback) callback();
                return;
            }
            if (xhr.responseJSON && xhr.responseJSON.error) {
                mensaje = xhr.responseJSON.error;
            }
            mostrarNotificacion('❌ ' + mensaje, 'danger');
            if (callback) callback();
        }
    });
}

function actualizarCantidadCarrito(lineaId, cantidad, callback) {
    const csrfToken = $('input[name="csrf_token"]').val() || $('meta[name="csrf-token"]').attr('content');
    
    $.ajax({
        url: `/carrito/actualizar/${lineaId}`,
        method: 'POST',
        data: {
            cantidad: cantidad,
            csrf_token: csrfToken
        },
        success: function(response) {
            if (response.success) {
                actualizarBadgeCarrito();
                mostrarNotificacion('✅ Carrito actualizado', 'success');
                setTimeout(function() {
                    location.reload();
                }, 500);
            } else {
                mostrarNotificacion('⚠️ Error actualizando carrito', 'warning');
            }
            if (callback) callback();
        },
        error: function(xhr) {
            let mensaje = 'Error actualizando carrito';
            if (xhr.responseJSON && xhr.responseJSON.error) {
                mensaje = xhr.responseJSON.error;
            }
            mostrarNotificacion('❌ ' + mensaje, 'danger');
            if (callback) callback();
        }
    });
}

function eliminarDelCarrito(lineaId, callback) {
    const csrfToken = $('input[name="csrf_token"]').val() || $('meta[name="csrf-token"]').attr('content');
    
    $.ajax({
        url: `/carrito/eliminar/${lineaId}`,
        method: 'POST',
        data: {
            csrf_token: csrfToken
        },
        success: function(response) {
            if (response.success) {
                actualizarBadgeCarrito();
                mostrarNotificacion('✅ Producto eliminado', 'success');
                setTimeout(function() {
                    location.reload();
                }, 500);
            } else {
                mostrarNotificacion('⚠️ Error eliminando producto', 'warning');
            }
            if (callback) callback();
        },
        error: function(xhr) {
            let mensaje = 'Error eliminando producto';
            if (xhr.responseJSON && xhr.responseJSON.error) {
                mensaje = xhr.responseJSON.error;
            }
            mostrarNotificacion('❌ ' + mensaje, 'danger');
            if (callback) callback();
        }
    });
}

function vaciarCarrito(callback) {
    const csrfToken = $('input[name="csrf_token"]').val() || $('meta[name="csrf-token"]').attr('content');
    
    $.ajax({
        url: '/carrito/vaciar',
        method: 'POST',
        data: {
            csrf_token: csrfToken
        },
        success: function(response) {
            actualizarBadgeCarrito();
            mostrarNotificacion('🛒 Carrito vaciado', 'info');
            setTimeout(function() {
                location.reload();
            }, 500);
            if (callback) callback();
        },
        error: function(xhr) {
            let mensaje = 'Error vaciando carrito';
            if (xhr.responseJSON && xhr.responseJSON.error) {
                mensaje = xhr.responseJSON.error;
            }
            mostrarNotificacion('❌ ' + mensaje, 'danger');
            if (callback) callback();
        }
    });
}

function actualizarBadgeCarrito() {
    $.ajax({
        url: '/carrito/contar',
        method: 'GET',
        success: function(response) {
            if (response.total_items !== undefined) {
                const badge = $('#cart-badge');
                const total = response.total_items;
                badge.text(total);
                if (total === 0) {
                    badge.hide();
                } else {
                    badge.show();
                    badge.css('transform', 'scale(1.5)');
                    setTimeout(function() {
                        badge.css('transform', 'scale(1)');
                    }, 200);
                }
            }
        },
        error: function(xhr) {
            console.error('Error actualizando badge del carrito');
            if (xhr.status === 401) {
                $('#cart-badge').hide();
            }
        }
    });
}

function mostrarNotificacion(mensaje, tipo = 'info') {
    const colores = {
        'success': 'alert-success',
        'danger': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };
    const iconos = {
        'success': 'fa-check-circle',
        'danger': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    
    $('.notification-toast').remove();
    
    const html = `
        <div class="alert ${colores[tipo] || 'alert-info'} alert-dismissible fade show notification-toast shadow-lg" 
             style="position: fixed; top: 80px; right: 20px; z-index: 9999; max-width: 420px; min-width: 280px; border-radius: 14px; padding: 16px 20px; border: none;" 
             role="alert">
            <div class="d-flex align-items-center">
                <i class="fas ${iconos[tipo] || 'fa-info-circle'} fa-lg me-3" style="font-size: 1.3rem;"></i>
                <div class="flex-grow-1" style="font-weight: 500; font-size: 0.95rem;">${mensaje}</div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close" style="font-size: 0.7rem;"></button>
            </div>
        </div>
    `;
    
    $('body').append(html);
    
    setTimeout(function() {
        $('.notification-toast').fadeOut('slow', function() {
            $(this).remove();
        });
    }, 5000);
}

window.agregarAlCarrito = agregarAlCarrito;
window.actualizarBadgeCarrito = actualizarBadgeCarrito;
window.mostrarNotificacion = mostrarNotificacion;
window.actualizarCantidadCarrito = actualizarCantidadCarrito;
window.eliminarDelCarrito = eliminarDelCarrito;
window.vaciarCarrito = vaciarCarrito;