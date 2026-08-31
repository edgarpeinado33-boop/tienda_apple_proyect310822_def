-- ======================================================
-- BASE DE DATOS PARA SUPABASE - TIENDA APPLE
-- ======================================================

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ======================================================
-- 1. MÓDULO DE SEGURIDAD Y USUARIOS
-- ======================================================

-- Tabla: USUARIO
CREATE TABLE USUARIO (
    id_usuario UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre_completo VARCHAR(150) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contrasena_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    telefono VARCHAR(20),
    fecha_registro DATE NOT NULL DEFAULT CURRENT_DATE,
    ultimo_acceso TIMESTAMP,
    email_verificado BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    token_recuperacion VARCHAR(255),
    token_expiracion TIMESTAMP,
    ip_registro VARCHAR(45),
    pregunta_seguridad VARCHAR(200),
    respuesta_seguridad_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: ROL
CREATE TABLE ROL (
    id_rol UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre_rol VARCHAR(50) UNIQUE NOT NULL,
    descripcion VARCHAR(200),
    nivel_permiso INT DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: PERMISO
CREATE TABLE PERMISO (
    id_permiso UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre_permiso VARCHAR(100) UNIQUE NOT NULL,
    recurso VARCHAR(100) NOT NULL,
    accion VARCHAR(50) NOT NULL,
    descripcion VARCHAR(200),
    modulo VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: ROL_PERMISO
CREATE TABLE ROL_PERMISO (
    id_rol_permiso UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_rol UUID NOT NULL REFERENCES ROL(id_rol) ON DELETE CASCADE,
    id_permiso UUID NOT NULL REFERENCES PERMISO(id_permiso) ON DELETE CASCADE,
    concedido BOOLEAN DEFAULT TRUE,
    fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    asignado_por VARCHAR(100),
    UNIQUE(id_rol, id_permiso)
);

-- Tabla: USUARIO_ROL
CREATE TABLE USUARIO_ROL (
    id_usuario_rol UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_usuario UUID NOT NULL REFERENCES USUARIO(id_usuario) ON DELETE CASCADE,
    id_rol UUID NOT NULL REFERENCES ROL(id_rol) ON DELETE CASCADE,
    fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    asignado_por VARCHAR(100),
    fecha_fin TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE,
    UNIQUE(id_usuario, id_rol, activo)
);

-- Tabla: SESION
CREATE TABLE SESION (
    id_sesion UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_usuario UUID NOT NULL REFERENCES USUARIO(id_usuario) ON DELETE CASCADE,
    token_sesion VARCHAR(255) UNIQUE NOT NULL,
    token_refresh VARCHAR(255),
    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion TIMESTAMP,
    fecha_cierre TIMESTAMP,
    direccion_ip VARCHAR(45),
    user_agent TEXT,
    navegador VARCHAR(50),
    sistema_operativo VARCHAR(50),
    estado VARCHAR(20) DEFAULT 'activa',
    dispositivo VARCHAR(50)
);

-- Tabla: BITACORA_AUDITORIA
CREATE TABLE BITACORA_AUDITORIA (
    id_bitacora UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_usuario UUID REFERENCES USUARIO(id_usuario) ON DELETE SET NULL,
    fecha_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accion VARCHAR(100) NOT NULL,
    tabla_afectada VARCHAR(50),
    registro_afectado VARCHAR(50),
    valor_anterior TEXT,
    valor_nuevo TEXT,
    direccion_ip VARCHAR(45),
    user_agent TEXT,
    modulo VARCHAR(50),
    severidad VARCHAR(20) DEFAULT 'info',
    session_id UUID
);

-- Tabla: INTENTO_LOGIN
CREATE TABLE INTENTO_LOGIN (
    id_intento UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(100) NOT NULL,
    direccion_ip VARCHAR(45),
    fecha_intento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exitoso BOOLEAN DEFAULT FALSE,
    motivo_fallo VARCHAR(200)
);

-- ======================================================
-- 2. MÓDULO DE CLIENTES Y PERFILES
-- ======================================================

-- Tabla: CLIENTE
CREATE TABLE CLIENTE (
    id_cliente UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_usuario UUID NOT NULL UNIQUE REFERENCES USUARIO(id_usuario) ON DELETE CASCADE,
    razon_social VARCHAR(200),
    numero_documento VARCHAR(50),
    tipo_documento VARCHAR(20) DEFAULT 'DNI',
    nombre_contacto VARCHAR(150),
    telefono_contacto VARCHAR(20),
    email_contacto VARCHAR(100),
    observaciones TEXT,
    segmento VARCHAR(50),
    descuento_especial DECIMAL(10,2) DEFAULT 0.00,
    verificado BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: PERFIL_USUARIO
CREATE TABLE PERFIL_USUARIO (
    id_perfil UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_usuario UUID NOT NULL UNIQUE REFERENCES USUARIO(id_usuario) ON DELETE CASCADE,
    direccion VARCHAR(255),
    ciudad VARCHAR(100),
    codigo_postal VARCHAR(20),
    pais VARCHAR(100) DEFAULT 'España',
    provincia VARCHAR(100),
    empresa VARCHAR(150),
    cargo VARCHAR(100),
    imagen_perfil_url VARCHAR(500),
    preferencias_notificacion TEXT,
    idioma_preferido VARCHAR(10) DEFAULT 'es',
    zona_horaria VARCHAR(50) DEFAULT 'Europe/Madrid',
    tema_preferido VARCHAR(20) DEFAULT 'light',
    notificaciones_email BOOLEAN DEFAULT TRUE,
    notificaciones_push BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: DIRECCION_ENVIO
CREATE TABLE DIRECCION_ENVIO (
    id_direccion UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_usuario UUID NOT NULL REFERENCES USUARIO(id_usuario) ON DELETE CASCADE,
    nombre_direccion VARCHAR(100) NOT NULL,
    calle VARCHAR(150) NOT NULL,
    numero VARCHAR(20),
    complemento VARCHAR(100),
    ciudad VARCHAR(100) NOT NULL,
    estado_provincia VARCHAR(100),
    codigo_postal VARCHAR(20) NOT NULL,
    pais VARCHAR(100) DEFAULT 'España',
    telefono_contacto VARCHAR(20),
    instrucciones_entrega TEXT,
    predeterminada BOOLEAN DEFAULT FALSE,
    tipo_direccion VARCHAR(20) DEFAULT 'casa',
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ======================================================
-- 3. MÓDULO DE CATÁLOGO DE PRODUCTOS
-- ======================================================

-- Tabla: CATEGORIA
CREATE TABLE CATEGORIA (
    id_categoria UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    id_categoria_padre UUID REFERENCES CATEGORIA(id_categoria) ON DELETE SET NULL,
    slug VARCHAR(120) UNIQUE NOT NULL,
    icono_url VARCHAR(500),
    orden INT DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: PRODUCTO
CREATE TABLE PRODUCTO (
    id_producto UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    precio_base DECIMAL(12,2) NOT NULL,
    imagen_url VARCHAR(500),
    familia VARCHAR(50),
    marca VARCHAR(50) DEFAULT 'Apple',
    fecha_lanzamiento DATE,
    estado VARCHAR(20) DEFAULT 'activo',
    proveedor VARCHAR(100),
    codigo_fabricante VARCHAR(50),
    peso_kg DECIMAL(8,3),
    dimensiones VARCHAR(100),
    requiere_autorizacion BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: PRODUCTO_CATEGORIA
CREATE TABLE PRODUCTO_CATEGORIA (
    id_producto_categoria UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_producto UUID NOT NULL REFERENCES PRODUCTO(id_producto) ON DELETE CASCADE,
    id_categoria UUID NOT NULL REFERENCES CATEGORIA(id_categoria) ON DELETE CASCADE,
    categoria_principal BOOLEAN DEFAULT FALSE,
    UNIQUE(id_producto, id_categoria)
);

-- Tabla: VARIANTE_PRODUCTO
CREATE TABLE VARIANTE_PRODUCTO (
    id_variante UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_producto UUID NOT NULL REFERENCES PRODUCTO(id_producto) ON DELETE CASCADE,
    color VARCHAR(50),
    capacidad VARCHAR(20),
    tamaño VARCHAR(20),
    material VARCHAR(50),
    talla_correa VARCHAR(10),
    precio_extra DECIMAL(12,2) DEFAULT 0.00,
    stock_disponible INT NOT NULL DEFAULT 0,
    sku VARCHAR(50) UNIQUE NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    codigo_barras VARCHAR(50),
    stock_minimo INT DEFAULT 0,
    stock_umbral_alerta INT DEFAULT 5,
    peso_extra_kg DECIMAL(8,3) DEFAULT 0.000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: HISTORIAL_PRECIO
CREATE TABLE HISTORIAL_PRECIO (
    id_historial_precio UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_variante UUID NOT NULL REFERENCES VARIANTE_PRODUCTO(id_variante) ON DELETE CASCADE,
    precio_anterior DECIMAL(12,2) NOT NULL,
    precio_nuevo DECIMAL(12,2) NOT NULL,
    fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    motivo VARCHAR(200),
    usuario_modifico VARCHAR(100),
    tipo_cambio VARCHAR(20) DEFAULT 'ajuste'
);

-- Tabla: FINANCIACION
CREATE TABLE FINANCIACION (
    id_financiacion UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_variante UUID NOT NULL REFERENCES VARIANTE_PRODUCTO(id_variante) ON DELETE CASCADE,
    duracion_meses INT NOT NULL,
    tin DECIMAL(5,2),
    tae DECIMAL(5,2),
    total_intereses DECIMAL(12,2),
    cuota_mensual DECIMAL(12,2),
    fecha_validez_inicio DATE,
    fecha_validez_fin DATE,
    entidad_financiera VARCHAR(100),
    comision_apertura DECIMAL(12,2) DEFAULT 0.00,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: IMAGEN_PRODUCTO
CREATE TABLE IMAGEN_PRODUCTO (
    id_imagen UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_variante UUID NOT NULL REFERENCES VARIANTE_PRODUCTO(id_variante) ON DELETE CASCADE,
    url_imagen VARCHAR(500) NOT NULL,
    descripcion VARCHAR(200),
    orden INT DEFAULT 0,
    principal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: RESENA_PRODUCTO
CREATE TABLE RESENA_PRODUCTO (
    id_resena UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_variante UUID NOT NULL REFERENCES VARIANTE_PRODUCTO(id_variante) ON DELETE CASCADE,
    id_usuario UUID NOT NULL REFERENCES USUARIO(id_usuario) ON DELETE CASCADE,
    calificacion INT NOT NULL CHECK (calificacion BETWEEN 1 AND 5),
    titulo VARCHAR(100),
    comentario TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aprobado BOOLEAN DEFAULT FALSE,
    respuesta_admin TEXT,
    fecha_respuesta TIMESTAMP
);

-- ======================================================
-- 4. MÓDULO DE CARRITO DE COMPRAS
-- ======================================================

-- Tabla: CUPON_DESCUENTO
CREATE TABLE CUPON_DESCUENTO (
    id_cupon UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo VARCHAR(50) UNIQUE NOT NULL,
    descripcion VARCHAR(200),
    porcentaje_descuento DECIMAL(5,2),
    monto_fijo_descuento DECIMAL(12,2),
    fecha_validez_inicio DATE,
    fecha_validez_fin DATE,
    uso_maximo INT,
    usos_actuales INT DEFAULT 0,
    monto_minimo_compra DECIMAL(12,2),
    usuarios_permitidos TEXT,
    productos_aplicables TEXT,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: CARRITO
CREATE TABLE CARRITO (
    id_carrito UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_usuario UUID REFERENCES USUARIO(id_usuario) ON DELETE SET NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(20) DEFAULT 'activo',
    session_id VARCHAR(100),
    subtotal DECIMAL(12,2) DEFAULT 0.00,
    descuentos DECIMAL(12,2) DEFAULT 0.00,
    codigo_cupon VARCHAR(50),
    total DECIMAL(12,2) DEFAULT 0.00,
    fecha_expiracion TIMESTAMP
);

-- Tabla: LINEA_CARRITO
CREATE TABLE LINEA_CARRITO (
    id_linea_carrito UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_carrito UUID NOT NULL REFERENCES CARRITO(id_carrito) ON DELETE CASCADE,
    id_variante UUID NOT NULL REFERENCES VARIANTE_PRODUCTO(id_variante) ON DELETE CASCADE,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    fecha_agregado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    precio_unitario DECIMAL(12,2) NOT NULL,
    descuento_aplicado DECIMAL(12,2) DEFAULT 0.00,
    UNIQUE(id_carrito, id_variante)
);

-- ======================================================
-- 5. MÓDULO DE PEDIDOS Y FACTURACIÓN
-- ======================================================

-- Tabla: METODO_PAGO
CREATE TABLE METODO_PAGO (
    id_metodo_pago UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_usuario UUID NOT NULL REFERENCES USUARIO(id_usuario) ON DELETE CASCADE,
    tipo VARCHAR(30) NOT NULL,
    ultimos_digitos VARCHAR(4),
    nombre_titular VARCHAR(150),
    fecha_expiracion DATE,
    predeterminado BOOLEAN DEFAULT FALSE,
    token VARCHAR(255),
    proveedor VARCHAR(50),
    tipo_tarjeta VARCHAR(20),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: PEDIDO
CREATE TABLE PEDIDO (
    id_pedido UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_usuario UUID NOT NULL REFERENCES USUARIO(id_usuario) ON DELETE CASCADE,
    id_direccion_envio UUID NOT NULL REFERENCES DIRECCION_ENVIO(id_direccion) ON DELETE CASCADE,
    fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(20) DEFAULT 'pendiente',
    subtotal DECIMAL(12,2) NOT NULL,
    impuestos DECIMAL(12,2) NOT NULL,
    gastos_envio DECIMAL(12,2) NOT NULL,
    descuento_total DECIMAL(12,2) DEFAULT 0.00,
    total DECIMAL(12,2) NOT NULL,
    direccion_envio_texto TEXT NOT NULL,
    notas TEXT,
    metodo_pedido VARCHAR(50),
    id_cupon_aplicado UUID REFERENCES CUPON_DESCUENTO(id_cupon) ON DELETE SET NULL,
    fecha_procesamiento TIMESTAMP,
    fecha_envio_real TIMESTAMP,
    fecha_entrega_estimada DATE,
    fecha_cancelacion TIMESTAMP,
    motivo_cancelacion VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: LINEA_PEDIDO
CREATE TABLE LINEA_PEDIDO (
    id_linea UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_pedido UUID NOT NULL REFERENCES PEDIDO(id_pedido) ON DELETE CASCADE,
    id_variante UUID NOT NULL REFERENCES VARIANTE_PRODUCTO(id_variante) ON DELETE CASCADE,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_unitario DECIMAL(12,2) NOT NULL,
    id_financiacion_seleccionada UUID REFERENCES FINANCIACION(id_financiacion) ON DELETE SET NULL,
    descuento_aplicado DECIMAL(12,2) DEFAULT 0.00,
    estado_linea VARCHAR(20) DEFAULT 'pendiente',
    impuesto_linea DECIMAL(12,2) DEFAULT 0.00,
    total_linea DECIMAL(12,2) NOT NULL,
    numero_serie_asignado VARCHAR(50)
);

-- Tabla: TRANSACCION_PAGO
CREATE TABLE TRANSACCION_PAGO (
    id_transaccion UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_pedido UUID NOT NULL REFERENCES PEDIDO(id_pedido) ON DELETE CASCADE,
    id_metodo_pago UUID REFERENCES METODO_PAGO(id_metodo_pago) ON DELETE SET NULL,
    monto DECIMAL(12,2) NOT NULL,
    fecha_transaccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(20) DEFAULT 'iniciado',
    codigo_autorizacion VARCHAR(100),
    mensaje_error VARCHAR(255),
    referencia_externa VARCHAR(100),
    ip_transaccion VARCHAR(45),
    moneda VARCHAR(10) DEFAULT 'EUR',
    comision DECIMAL(12,2) DEFAULT 0.00
);

-- Tabla: FACTURA
CREATE TABLE FACTURA (
    id_factura UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_pedido UUID NOT NULL UNIQUE REFERENCES PEDIDO(id_pedido) ON DELETE CASCADE,
    id_usuario UUID NOT NULL REFERENCES USUARIO(id_usuario) ON DELETE CASCADE,
    fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    numero_factura VARCHAR(50) UNIQUE NOT NULL,
    tipo_documento VARCHAR(20) DEFAULT 'FACTURA',
    ruc_emisor VARCHAR(20),
    razon_social_emisor VARCHAR(200),
    ruc_cliente VARCHAR(20),
    razon_social_cliente VARCHAR(200),
    xml_path VARCHAR(500),
    pdf_path VARCHAR(500),
    estado_factura VARCHAR(20) DEFAULT 'emitida',
    tipo_comprobante VARCHAR(20),
    total_factura DECIMAL(12,2) NOT NULL,
    clave_acceso VARCHAR(100),
    fecha_autorizacion TIMESTAMP,
    numero_autorizacion VARCHAR(50),
    json_original JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ======================================================
-- 6. MÓDULO DE LOGÍSTICA Y POSVENTA
-- ======================================================

-- Tabla: ENVIO
CREATE TABLE ENVIO (
    id_envio UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_pedido UUID NOT NULL UNIQUE REFERENCES PEDIDO(id_pedido) ON DELETE CASCADE,
    transportista VARCHAR(100),
    numero_seguimiento VARCHAR(100),
    fecha_envio TIMESTAMP,
    fecha_estimada_entrega DATE,
    fecha_entrega_real TIMESTAMP,
    estado_envio VARCHAR(20) DEFAULT 'preparacion',
    costo_envio DECIMAL(12,2) NOT NULL,
    direccion_envio_texto TEXT NOT NULL,
    metodo_envio VARCHAR(50),
    historial_seguimiento JSONB,
    responsable_envio VARCHAR(100),
    notas_logistica TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: DEVOLUCION
CREATE TABLE DEVOLUCION (
    id_devolucion UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_pedido UUID NOT NULL REFERENCES PEDIDO(id_pedido) ON DELETE CASCADE,
    id_usuario UUID NOT NULL REFERENCES USUARIO(id_usuario) ON DELETE CASCADE,
    id_linea_pedido UUID REFERENCES LINEA_PEDIDO(id_linea) ON DELETE SET NULL,
    fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    motivo VARCHAR(200) NOT NULL,
    estado VARCHAR(20) DEFAULT 'solicitada',
    monto_reembolso DECIMAL(12,2),
    metodo_reembolso VARCHAR(50),
    fecha_aprobacion TIMESTAMP,
    numero_guia_devolucion VARCHAR(100),
    observaciones TEXT,
    transportista_devolucion VARCHAR(100),
    fecha_recepcion_almacen TIMESTAMP,
    condicion_producto VARCHAR(100),
    motivo_detalle TEXT
);

-- Tabla: GARANTIA
CREATE TABLE GARANTIA (
    id_garantia UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_variante UUID NOT NULL REFERENCES VARIANTE_PRODUCTO(id_variante) ON DELETE CASCADE,
    id_pedido UUID NOT NULL REFERENCES PEDIDO(id_pedido) ON DELETE CASCADE,
    tipo_garantia VARCHAR(50) DEFAULT 'estandar',
    fecha_inicio DATE,
    fecha_fin DATE,
    cobertura TEXT,
    estado VARCHAR(20) DEFAULT 'activa',
    proveedor VARCHAR(100),
    numero_garantia VARCHAR(50),
    terminos_condiciones TEXT,
    contacto_soporte VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: NOTIFICACION
CREATE TABLE NOTIFICACION (
    id_notificacion UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_usuario UUID NOT NULL REFERENCES USUARIO(id_usuario) ON DELETE CASCADE,
    fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo VARCHAR(20) NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    mensaje TEXT NOT NULL,
    estado VARCHAR(20) DEFAULT 'pendiente',
    canal VARCHAR(50),
    fecha_lectura TIMESTAMP,
    enlace_accion VARCHAR(500),
    leido BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ======================================================
-- 7. ÍNDICES PARA MEJORAR EL RENDIMIENTO
-- ======================================================

-- Índices para USUARIO
CREATE INDEX idx_usuario_email ON USUARIO(email);
CREATE INDEX idx_usuario_activo ON USUARIO(activo);

-- Índices para SESION
CREATE INDEX idx_sesion_token ON SESION(token_sesion);
CREATE INDEX idx_sesion_usuario ON SESION(id_usuario);
CREATE INDEX idx_sesion_estado ON SESION(estado);

-- Índices para BITACORA_AUDITORIA
CREATE INDEX idx_bitacora_fecha ON BITACORA_AUDITORIA(fecha_evento);
CREATE INDEX idx_bitacora_usuario ON BITACORA_AUDITORIA(id_usuario);
CREATE INDEX idx_bitacora_accion ON BITACORA_AUDITORIA(accion);

-- Índices para INTENTO_LOGIN
CREATE INDEX idx_intento_email ON INTENTO_LOGIN(email);
CREATE INDEX idx_intento_fecha ON INTENTO_LOGIN(fecha_intento);

-- Índices para CLIENTE
CREATE INDEX idx_cliente_documento ON CLIENTE(numero_documento);
CREATE INDEX idx_cliente_verificado ON CLIENTE(verificado);

-- Índices para DIRECCION_ENVIO
CREATE INDEX idx_direccion_usuario ON DIRECCION_ENVIO(id_usuario);
CREATE INDEX idx_direccion_predeterminada ON DIRECCION_ENVIO(predeterminada);

-- Índices para CATEGORIA
CREATE INDEX idx_categoria_slug ON CATEGORIA(slug);
CREATE INDEX idx_categoria_padre ON CATEGORIA(id_categoria_padre);

-- Índices para PRODUCTO
CREATE INDEX idx_producto_nombre ON PRODUCTO(nombre);
CREATE INDEX idx_producto_familia ON PRODUCTO(familia);
CREATE INDEX idx_producto_estado ON PRODUCTO(estado);

-- Índices para VARIANTE_PRODUCTO
CREATE INDEX idx_variante_sku ON VARIANTE_PRODUCTO(sku);
CREATE INDEX idx_variante_producto ON VARIANTE_PRODUCTO(id_producto);
CREATE INDEX idx_variante_stock ON VARIANTE_PRODUCTO(stock_disponible);

-- Índices para HISTORIAL_PRECIO
CREATE INDEX idx_historial_variante ON HISTORIAL_PRECIO(id_variante);
CREATE INDEX idx_historial_fecha ON HISTORIAL_PRECIO(fecha_cambio);

-- Índices para FINANCIACION
CREATE INDEX idx_financiacion_variante ON FINANCIACION(id_variante);
CREATE INDEX idx_financiacion_activo ON FINANCIACION(activo);

-- Índices para IMAGEN_PRODUCTO
CREATE INDEX idx_imagen_variante ON IMAGEN_PRODUCTO(id_variante);

-- Índices para RESENA_PRODUCTO
CREATE INDEX idx_resena_variante ON RESENA_PRODUCTO(id_variante);
CREATE INDEX idx_resena_calificacion ON RESENA_PRODUCTO(calificacion);

-- Índices para CUPON_DESCUENTO
CREATE INDEX idx_cupon_codigo ON CUPON_DESCUENTO(codigo);
CREATE INDEX idx_cupon_activo ON CUPON_DESCUENTO(activo);

-- Índices para CARRITO
CREATE INDEX idx_carrito_usuario ON CARRITO(id_usuario);
CREATE INDEX idx_carrito_session ON CARRITO(session_id);
CREATE INDEX idx_carrito_estado ON CARRITO(estado);

-- Índices para METODO_PAGO
CREATE INDEX idx_metodo_pago_usuario ON METODO_PAGO(id_usuario);

-- Índices para PEDIDO
CREATE INDEX idx_pedido_usuario ON PEDIDO(id_usuario);
CREATE INDEX idx_pedido_estado ON PEDIDO(estado);
CREATE INDEX idx_pedido_fecha ON PEDIDO(fecha_pedido);

-- Índices para LINEA_PEDIDO
CREATE INDEX idx_linea_pedido ON LINEA_PEDIDO(id_pedido);
CREATE INDEX idx_linea_estado ON LINEA_PEDIDO(estado_linea);

-- Índices para TRANSACCION_PAGO
CREATE INDEX idx_transaccion_pedido ON TRANSACCION_PAGO(id_pedido);
CREATE INDEX idx_transaccion_estado ON TRANSACCION_PAGO(estado);

-- Índices para FACTURA
CREATE INDEX idx_factura_numero ON FACTURA(numero_factura);
CREATE INDEX idx_factura_pedido ON FACTURA(id_pedido);
CREATE INDEX idx_factura_estado ON FACTURA(estado_factura);

-- Índices para ENVIO
CREATE INDEX idx_envio_seguimiento ON ENVIO(numero_seguimiento);
CREATE INDEX idx_envio_estado ON ENVIO(estado_envio);

-- Índices para DEVOLUCION
CREATE INDEX idx_devolucion_pedido ON DEVOLUCION(id_pedido);
CREATE INDEX idx_devolucion_estado ON DEVOLUCION(estado);

-- Índices para GARANTIA
CREATE INDEX idx_garantia_variante ON GARANTIA(id_variante);
CREATE INDEX idx_garantia_estado ON GARANTIA(estado);

-- Índices para NOTIFICACION
CREATE INDEX idx_notificacion_usuario ON NOTIFICACION(id_usuario);
CREATE INDEX idx_notificacion_estado ON NOTIFICACION(estado);

-- ======================================================
-- 8. VISTAS ÚTILES
-- ======================================================

-- Vista: V_PEDIDO_COMPLETO
CREATE OR REPLACE VIEW V_PEDIDO_COMPLETO AS
SELECT 
    p.id_pedido,
    p.fecha_pedido,
    p.estado,
    p.total,
    u.nombre_completo AS cliente_nombre,
    u.email AS cliente_email,
    d.calle AS direccion_calle,
    d.ciudad AS direccion_ciudad,
    e.numero_seguimiento,
    e.estado_envio,
    f.numero_factura
FROM PEDIDO p
LEFT JOIN USUARIO u ON p.id_usuario = u.id_usuario
LEFT JOIN DIRECCION_ENVIO d ON p.id_direccion_envio = d.id_direccion
LEFT JOIN ENVIO e ON p.id_pedido = e.id_pedido
LEFT JOIN FACTURA f ON p.id_pedido = f.id_pedido;

-- Vista: V_STOCK_PRODUCTOS
CREATE OR REPLACE VIEW V_STOCK_PRODUCTOS AS
SELECT 
    v.id_variante,
    v.sku,
    v.stock_disponible,
    v.stock_minimo,
    p.nombre AS producto_nombre,
    CONCAT(p.nombre, ' - ', v.color, ' ', v.capacidad) AS descripcion_completa
FROM VARIANTE_PRODUCTO v
INNER JOIN PRODUCTO p ON v.id_producto = p.id_producto
WHERE v.activo = TRUE;

-- ======================================================
-- 9. FUNCIONES Y PROCEDIMIENTOS
-- ======================================================

-- Función para actualizar stock
CREATE OR REPLACE FUNCTION sp_actualizar_stock(
    p_id_variante UUID,
    p_cantidad INT
)
RETURNS TABLE(mensaje TEXT, nuevo_stock INT) AS $$
DECLARE
    stock_actual INT;
BEGIN
    -- Obtener stock actual con bloqueo
    SELECT stock_disponible INTO stock_actual
    FROM VARIANTE_PRODUCTO
    WHERE id_variante = p_id_variante
    FOR UPDATE;
    
    IF stock_actual >= p_cantidad THEN
        -- Actualizar stock
        UPDATE VARIANTE_PRODUCTO
        SET stock_disponible = stock_disponible - p_cantidad
        WHERE id_variante = p_id_variante;
        
        -- Registrar en auditoría
        INSERT INTO BITACORA_AUDITORIA (id_bitacora, tabla_afectada, registro_afectado, accion, valor_anterior, valor_nuevo)
        VALUES (uuid_generate_v4(), 'VARIANTE_PRODUCTO', p_id_variante::TEXT, 'ACTUALIZACION_STOCK', 
                CONCAT('Stock: ', stock_actual), 
                CONCAT('Stock: ', stock_actual - p_cantidad));
        
        RETURN QUERY SELECT 'STOCK_ACTUALIZADO'::TEXT AS mensaje, (stock_actual - p_cantidad)::INT AS nuevo_stock;
    ELSE
        RETURN QUERY SELECT 'STOCK_INSUFICIENTE'::TEXT AS mensaje, stock_actual::INT AS nuevo_stock;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ======================================================
-- 10. TRIGGERS
-- ======================================================

-- Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger a tablas con updated_at
CREATE TRIGGER update_usuario_updated_at
    BEFORE UPDATE ON USUARIO
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cliente_updated_at
    BEFORE UPDATE ON CLIENTE
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_perfil_usuario_updated_at
    BEFORE UPDATE ON PERFIL_USUARIO
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_direccion_envio_updated_at
    BEFORE UPDATE ON DIRECCION_ENVIO
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categoria_updated_at
    BEFORE UPDATE ON CATEGORIA
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_producto_updated_at
    BEFORE UPDATE ON PRODUCTO
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_variante_producto_updated_at
    BEFORE UPDATE ON VARIANTE_PRODUCTO
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cupon_descuento_updated_at
    BEFORE UPDATE ON CUPON_DESCUENTO
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_carrito_updated_at
    BEFORE UPDATE ON CARRITO
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_metodo_pago_updated_at
    BEFORE UPDATE ON METODO_PAGO
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pedido_updated_at
    BEFORE UPDATE ON PEDIDO
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_factura_updated_at
    BEFORE UPDATE ON FACTURA
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_envio_updated_at
    BEFORE UPDATE ON ENVIO
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para bitácora de pedidos
CREATE OR REPLACE FUNCTION trg_bitacora_pedido_func()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.estado IS DISTINCT FROM NEW.estado THEN
        INSERT INTO BITACORA_AUDITORIA (
            id_bitacora, id_usuario, tabla_afectada, registro_afectado, 
            accion, valor_anterior, valor_nuevo
        ) VALUES (
            uuid_generate_v4(), 
            NEW.id_usuario, 
            'PEDIDO', 
            NEW.id_pedido::TEXT,
            'CAMBIO_ESTADO',
            OLD.estado,
            NEW.estado
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_bitacora_pedido
    AFTER UPDATE ON PEDIDO
    FOR EACH ROW
    EXECUTE FUNCTION trg_bitacora_pedido_func();

-- ======================================================
-- 11. DATOS INICIALES
-- ======================================================

-- Insertar roles básicos
INSERT INTO ROL (id_rol, nombre_rol, descripcion, nivel_permiso) VALUES
(uuid_generate_v4(), 'SUPER_ADMIN', 'Administrador con todos los permisos', 100),
(uuid_generate_v4(), 'ADMIN_TIENDA', 'Administrador de la tienda', 80),
(uuid_generate_v4(), 'ADMIN_PRODUCTOS', 'Gestor de catálogo de productos', 60),
(uuid_generate_v4(), 'ADMIN_PEDIDOS', 'Gestor de pedidos y logística', 60),
(uuid_generate_v4(), 'ADMIN_FACTURACION', 'Gestor de facturación y finanzas', 70),
(uuid_generate_v4(), 'VENDEDOR', 'Vendedor con acceso a gestionar clientes', 40),
(uuid_generate_v4(), 'CLIENTE', 'Cliente registrado', 10),
(uuid_generate_v4(), 'INVITADO', 'Usuario no registrado', 0);

-- Insertar permisos básicos
INSERT INTO PERMISO (id_permiso, nombre_permiso, recurso, accion, descripcion, modulo) VALUES
(uuid_generate_v4(), 'usuario:ver', 'usuario', 'ver', 'Ver información de usuarios', 'seguridad'),
(uuid_generate_v4(), 'usuario:crear', 'usuario', 'crear', 'Crear nuevos usuarios', 'seguridad'),
(uuid_generate_v4(), 'usuario:editar', 'usuario', 'editar', 'Editar usuarios existentes', 'seguridad'),
(uuid_generate_v4(), 'usuario:eliminar', 'usuario', 'eliminar', 'Eliminar usuarios', 'seguridad'),
(uuid_generate_v4(), 'usuario:bloquear', 'usuario', 'bloquear', 'Bloquear/desbloquear usuarios', 'seguridad'),
(uuid_generate_v4(), 'rol:gestionar', 'rol', 'gestionar', 'Gestionar roles y permisos', 'seguridad'),
(uuid_generate_v4(), 'producto:ver', 'producto', 'ver', 'Ver catálogo de productos', 'catalogo'),
(uuid_generate_v4(), 'producto:crear', 'producto', 'crear', 'Crear nuevos productos', 'catalogo'),
(uuid_generate_v4(), 'producto:editar', 'producto', 'editar', 'Editar productos existentes', 'catalogo'),
(uuid_generate_v4(), 'producto:eliminar', 'producto', 'eliminar', 'Eliminar productos del catálogo', 'catalogo'),
(uuid_generate_v4(), 'pedido:ver', 'pedido', 'ver', 'Ver pedidos', 'pedidos'),
(uuid_generate_v4(), 'pedido:crear', 'pedido', 'crear', 'Crear pedidos', 'pedidos'),
(uuid_generate_v4(), 'pedido:editar', 'pedido', 'editar', 'Modificar pedidos', 'pedidos'),
(uuid_generate_v4(), 'pedido:anular', 'pedido', 'anular', 'Anular pedidos', 'pedidos'),
(uuid_generate_v4(), 'factura:ver', 'factura', 'ver', 'Ver facturas', 'facturacion'),
(uuid_generate_v4(), 'factura:crear', 'factura', 'crear', 'Generar facturas', 'facturacion'),
(uuid_generate_v4(), 'factura:anular', 'factura', 'anular', 'Anular facturas', 'facturacion'),
(uuid_generate_v4(), 'envio:gestionar', 'envio', 'gestionar', 'Gestionar envíos y logística', 'logistica'),
(uuid_generate_v4(), 'devolucion:gestionar', 'devolucion', 'gestionar', 'Gestionar devoluciones', 'logistica'),
(uuid_generate_v4(), 'auditoria:ver', 'auditoria', 'ver', 'Ver bitácora de auditoría', 'seguridad'),
(uuid_generate_v4(), 'configuracion:editar', 'configuracion', 'editar', 'Editar configuración del sistema', 'sistema');

-- Insertar categorías principales de Apple
INSERT INTO CATEGORIA (id_categoria, nombre, slug, descripcion) VALUES
(uuid_generate_v4(), 'iPhone', 'iphone', 'Teléfonos inteligentes Apple'),
(uuid_generate_v4(), 'iPad', 'ipad', 'Tabletas Apple'),
(uuid_generate_v4(), 'Mac', 'mac', 'Computadoras Apple'),
(uuid_generate_v4(), 'Apple Watch', 'apple-watch', 'Relojes inteligentes Apple'),
(uuid_generate_v4(), 'AirPods', 'airpods', 'Auriculares y audífonos Apple'),
(uuid_generate_v4(), 'Apple TV', 'apple-tv', 'Dispositivos de streaming Apple'),
(uuid_generate_v4(), 'Accesorios', 'accesorios', 'Accesorios para dispositivos Apple');

-- Insertar subcategorías de ejemplo
INSERT INTO CATEGORIA (id_categoria, nombre, slug, descripcion, id_categoria_padre) 
SELECT uuid_generate_v4(), 'MacBook', 'macbook', 'Portátiles Mac', id_categoria FROM CATEGORIA WHERE slug = 'mac';

INSERT INTO CATEGORIA (id_categoria, nombre, slug, descripcion, id_categoria_padre) 
SELECT uuid_generate_v4(), 'iMac', 'imac', 'Computadoras de escritorio Mac', id_categoria FROM CATEGORIA WHERE slug = 'mac';

INSERT INTO CATEGORIA (id_categoria, nombre, slug, descripcion, id_categoria_padre) 
SELECT uuid_generate_v4(), 'Mac mini', 'mac-mini', 'Mini computadoras Mac', id_categoria FROM CATEGORIA WHERE slug = 'mac';

INSERT INTO CATEGORIA (id_categoria, nombre, slug, descripcion, id_categoria_padre) 
SELECT uuid_generate_v4(), 'Mac Studio', 'mac-studio', 'Workstations Mac', id_categoria FROM CATEGORIA WHERE slug = 'mac';

-- ======================================================
-- 12. CONFIGURACIÓN DE RLS (Row Level Security)
-- ======================================================

-- Habilitar RLS en todas las tablas
ALTER TABLE USUARIO ENABLE ROW LEVEL SECURITY;
ALTER TABLE ROL ENABLE ROW LEVEL SECURITY;
ALTER TABLE PERMISO ENABLE ROW LEVEL SECURITY;
ALTER TABLE ROL_PERMISO ENABLE ROW LEVEL SECURITY;
ALTER TABLE USUARIO_ROL ENABLE ROW LEVEL SECURITY;
ALTER TABLE SESION ENABLE ROW LEVEL SECURITY;
ALTER TABLE BITACORA_AUDITORIA ENABLE ROW LEVEL SECURITY;
ALTER TABLE INTENTO_LOGIN ENABLE ROW LEVEL SECURITY;
ALTER TABLE CLIENTE ENABLE ROW LEVEL SECURITY;
ALTER TABLE PERFIL_USUARIO ENABLE ROW LEVEL SECURITY;
ALTER TABLE DIRECCION_ENVIO ENABLE ROW LEVEL SECURITY;
ALTER TABLE CATEGORIA ENABLE ROW LEVEL SECURITY;
ALTER TABLE PRODUCTO ENABLE ROW LEVEL SECURITY;
ALTER TABLE PRODUCTO_CATEGORIA ENABLE ROW LEVEL SECURITY;
ALTER TABLE VARIANTE_PRODUCTO ENABLE ROW LEVEL SECURITY;
ALTER TABLE HISTORIAL_PRECIO ENABLE ROW LEVEL SECURITY;
ALTER TABLE FINANCIACION ENABLE ROW LEVEL SECURITY;
ALTER TABLE IMAGEN_PRODUCTO ENABLE ROW LEVEL SECURITY;
ALTER TABLE RESENA_PRODUCTO ENABLE ROW LEVEL SECURITY;
ALTER TABLE CUPON_DESCUENTO ENABLE ROW LEVEL SECURITY;
ALTER TABLE CARRITO ENABLE ROW LEVEL SECURITY;
ALTER TABLE LINEA_CARRITO ENABLE ROW LEVEL SECURITY;
ALTER TABLE METODO_PAGO ENABLE ROW LEVEL SECURITY;
ALTER TABLE PEDIDO ENABLE ROW LEVEL SECURITY;
ALTER TABLE LINEA_PEDIDO ENABLE ROW LEVEL SECURITY;
ALTER TABLE TRANSACCION_PAGO ENABLE ROW LEVEL SECURITY;
ALTER TABLE FACTURA ENABLE ROW LEVEL SECURITY;
ALTER TABLE ENVIO ENABLE ROW LEVEL SECURITY;
ALTER TABLE DEVOLUCION ENABLE ROW LEVEL SECURITY;
ALTER TABLE GARANTIA ENABLE ROW LEVEL SECURITY;
ALTER TABLE NOTIFICACION ENABLE ROW LEVEL SECURITY;

-- Políticas RLS básicas

-- USUARIO: Los usuarios pueden ver y editar su propio perfil
CREATE POLICY usuario_select_own ON USUARIO
    FOR SELECT USING (auth.uid() = id_usuario);

CREATE POLICY usuario_update_own ON USUARIO
    FOR UPDATE USING (auth.uid() = id_usuario);

-- DIRECCION_ENVIO: Los usuarios solo ven sus propias direcciones
CREATE POLICY direccion_envio_select_own ON DIRECCION_ENVIO
    FOR SELECT USING (auth.uid() = id_usuario);

CREATE POLICY direccion_envio_insert_own ON DIRECCION_ENVIO
    FOR INSERT WITH CHECK (auth.uid() = id_usuario);

CREATE POLICY direccion_envio_update_own ON DIRECCION_ENVIO
    FOR UPDATE USING (auth.uid() = id_usuario);

CREATE POLICY direccion_envio_delete_own ON DIRECCION_ENVIO
    FOR DELETE USING (auth.uid() = id_usuario);

-- CARRITO: Los usuarios solo ven su propio carrito
CREATE POLICY carrito_select_own ON CARRITO
    FOR SELECT USING (auth.uid() = id_usuario);

CREATE POLICY carrito_insert_own ON CARRITO
    FOR INSERT WITH CHECK (auth.uid() = id_usuario);

CREATE POLICY carrito_update_own ON CARRITO
    FOR UPDATE USING (auth.uid() = id_usuario);

CREATE POLICY carrito_delete_own ON CARRITO
    FOR DELETE USING (auth.uid() = id_usuario);

-- PEDIDO: Los usuarios ven sus propios pedidos
CREATE POLICY pedido_select_own ON PEDIDO
    FOR SELECT USING (auth.uid() = id_usuario);

-- Los administradores pueden ver y gestionar todos los pedidos (ejemplo de política para admin)
-- Nota: El rol de admin se puede verificar mediante una consulta a USUARIO_ROL
CREATE POLICY pedido_select_admin ON PEDIDO
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM USUARIO_ROL ur
            JOIN ROL r ON ur.id_rol = r.id_rol
            WHERE ur.id_usuario = auth.uid()
            AND r.nombre_rol IN ('SUPER_ADMIN', 'ADMIN_TIENDA', 'ADMIN_PEDIDOS')
            AND ur.activo = TRUE
        )
    );




-- Insertar datos iniciales de ejemplo para productos, variantes y categorías
-- ======================================================
-- LLENAR TABLAS CON DATOS DE PRUEBA - TIENDA APPLE
-- ======================================================

-- ======================================================
-- 1. USUARIOS
-- ======================================================

INSERT INTO usuario (id_usuario, nombre_completo, email, contrasena_hash, salt, telefono, fecha_registro, email_verificado, activo) VALUES
(uuid_generate_v4(), 'Administrador', 'admin@tiendaapple.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYHjZ5PkYWm', 'dummy', '+34 600 000 001', CURRENT_DATE, TRUE, TRUE),
(uuid_generate_v4(), 'Juan Pérez', 'juan@email.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYHjZ5PkYWm', 'dummy', '+34 600 000 002', CURRENT_DATE, TRUE, TRUE),
(uuid_generate_v4(), 'María García', 'maria@email.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYHjZ5PkYWm', 'dummy', '+34 600 000 003', CURRENT_DATE, TRUE, TRUE),
(uuid_generate_v4(), 'Carlos López', 'carlos@email.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYHjZ5PkYWm', 'dummy', '+34 600 000 004', CURRENT_DATE, TRUE, TRUE);

-- ======================================================
-- 2. ASIGNAR ROLES
-- ======================================================

INSERT INTO usuario_rol (id_usuario_rol, id_usuario, id_rol, activo)
SELECT uuid_generate_v4(), u.id_usuario, r.id_rol, TRUE
FROM usuario u, rol r
WHERE u.email = 'admin@tiendaapple.com' AND r.nombre_rol = 'SUPER_ADMIN';

INSERT INTO usuario_rol (id_usuario_rol, id_usuario, id_rol, activo)
SELECT uuid_generate_v4(), u.id_usuario, r.id_rol, TRUE
FROM usuario u, rol r
WHERE u.email != 'admin@tiendaapple.com' AND r.nombre_rol = 'CLIENTE';

-- ======================================================
-- 3. PERFILES DE USUARIO
-- ======================================================

INSERT INTO perfil_usuario (id_perfil, id_usuario, direccion, ciudad, codigo_postal, pais, provincia)
SELECT 
    uuid_generate_v4(),
    u.id_usuario,
    'Calle Principal ' || (ROW_NUMBER() OVER (ORDER BY u.email) * 10)::text,
    CASE u.email
        WHEN 'admin@tiendaapple.com' THEN 'Madrid'
        WHEN 'juan@email.com' THEN 'Madrid'
        WHEN 'maria@email.com' THEN 'Barcelona'
        WHEN 'carlos@email.com' THEN 'Valencia'
    END,
    CASE u.email
        WHEN 'admin@tiendaapple.com' THEN '28001'
        WHEN 'juan@email.com' THEN '28001'
        WHEN 'maria@email.com' THEN '08001'
        WHEN 'carlos@email.com' THEN '46001'
    END,
    'España',
    CASE u.email
        WHEN 'admin@tiendaapple.com' THEN 'Madrid'
        WHEN 'juan@email.com' THEN 'Madrid'
        WHEN 'maria@email.com' THEN 'Barcelona'
        WHEN 'carlos@email.com' THEN 'Valencia'
    END
FROM usuario u;

-- ======================================================
-- 4. DIRECCIONES DE ENVÍO
-- ======================================================

INSERT INTO direccion_envio (id_direccion, id_usuario, nombre_direccion, calle, numero, ciudad, codigo_postal, pais, predeterminada, activa)
SELECT 
    uuid_generate_v4(),
    u.id_usuario,
    'Casa',
    'Calle ' || u.nombre_completo,
    '1',
    CASE u.email
        WHEN 'admin@tiendaapple.com' THEN 'Madrid'
        WHEN 'juan@email.com' THEN 'Madrid'
        WHEN 'maria@email.com' THEN 'Barcelona'
        WHEN 'carlos@email.com' THEN 'Valencia'
    END,
    CASE u.email
        WHEN 'admin@tiendaapple.com' THEN '28001'
        WHEN 'juan@email.com' THEN '28001'
        WHEN 'maria@email.com' THEN '08001'
        WHEN 'carlos@email.com' THEN '46001'
    END,
    'España',
    TRUE,
    TRUE
FROM usuario u;

-- ======================================================
-- 5. CATEGORÍAS (YA EXISTEN DEL SCRIPT INICIAL)
-- ======================================================

-- ======================================================
-- 6. PRODUCTOS
-- ======================================================

INSERT INTO producto (id_producto, nombre, descripcion, precio_base, imagen_url, familia, marca, estado) VALUES
(uuid_generate_v4(), 'iPhone 15 Pro Max', 'El iPhone más avanzado con titanio, chip A17 Pro y cámara de 48MP.', 1199.00, 'https://images.unsplash.com/photo-1510557880100-43aa80b5e834?w=400', 'iPhone', 'Apple', 'activo'),
(uuid_generate_v4(), 'iPhone 15 Pro', 'iPhone 15 Pro con titanio, chip A17 Pro y cámara de 48MP.', 1099.00, 'https://images.unsplash.com/photo-1510557880100-43aa80b5e834?w=400', 'iPhone', 'Apple', 'activo'),
(uuid_generate_v4(), 'iPhone 15', 'iPhone 15 con Dynamic Island y cámara de 48MP.', 799.00, 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=400', 'iPhone', 'Apple', 'activo'),
(uuid_generate_v4(), 'MacBook Air M2', 'MacBook Air con chip M2, ligera y potente.', 1299.00, 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400', 'MacBook', 'Apple', 'activo'),
(uuid_generate_v4(), 'MacBook Pro 14" M3', 'MacBook Pro con chip M3, para profesionales.', 1999.00, 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400', 'MacBook', 'Apple', 'activo'),
(uuid_generate_v4(), 'iMac 24" M3', 'iMac todo en uno con chip M3. Pantalla 4.5K Retina.', 1499.00, 'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=400', 'iMac', 'Apple', 'activo'),
(uuid_generate_v4(), 'iPad Pro 12.9" M2', 'iPad Pro con chip M2 y pantalla XDR de 12.9".', 1099.00, 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400', 'iPad', 'Apple', 'activo'),
(uuid_generate_v4(), 'iPad Air 10.9" M1', 'iPad Air con chip M1 y pantalla Liquid Retina.', 599.00, 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400', 'iPad', 'Apple', 'activo'),
(uuid_generate_v4(), 'Apple Watch Series 9', 'Apple Watch Series 9 con pantalla siempre activa.', 399.00, 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=400', 'Apple Watch', 'Apple', 'activo'),
(uuid_generate_v4(), 'Apple Watch Ultra 2', 'Apple Watch Ultra 2 con pantalla de 49mm.', 799.00, 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=400', 'Apple Watch', 'Apple', 'activo'),
(uuid_generate_v4(), 'AirPods Pro 2', 'AirPods Pro con cancelación de ruido y audio espacial.', 249.00, 'https://images.unsplash.com/photo-1588423771073-b8903fbb85b5?w=400', 'AirPods', 'Apple', 'activo'),
(uuid_generate_v4(), 'AirPods Max', 'AirPods Max con audio de alta fidelidad.', 549.00, 'https://images.unsplash.com/photo-1588423771073-b8903fbb85b5?w=400', 'AirPods', 'Apple', 'activo'),
(uuid_generate_v4(), 'Apple TV 4K', 'Apple TV 4K con chip A15 Bionic.', 149.00, 'https://images.unsplash.com/photo-1581251917070-90de70bdc9e0?w=400', 'Apple TV', 'Apple', 'activo'),
(uuid_generate_v4(), 'HomePod Mini', 'HomePod Mini con Siri y audio de alta calidad.', 99.00, 'https://images.unsplash.com/photo-1581251917070-90de70bdc9e0?w=400', 'HomePod', 'Apple', 'activo');

-- ======================================================
-- 7. ASIGNAR PRODUCTOS A CATEGORÍAS
-- ======================================================

INSERT INTO producto_categoria (id_producto_categoria, id_producto, id_categoria)
SELECT uuid_generate_v4(), p.id_producto, c.id_categoria
FROM producto p, categoria c
WHERE (p.familia = 'iPhone' AND c.slug = 'iphone')
   OR (p.familia IN ('MacBook', 'iMac') AND c.slug = 'mac')
   OR (p.familia = 'iPad' AND c.slug = 'ipad')
   OR (p.familia = 'Apple Watch' AND c.slug = 'apple-watch')
   OR (p.familia = 'AirPods' AND c.slug = 'airpods')
   OR (p.familia = 'Apple TV' AND c.slug = 'apple-tv')
   OR (p.familia = 'HomePod' AND c.slug = 'accesorios');

-- ======================================================
-- 8. VARIANTES CON STOCK
-- ======================================================

DO $$
DECLARE
    v_producto_id UUID;
BEGIN
    -- iPhone 15 Pro Max
    SELECT id_producto INTO v_producto_id FROM producto WHERE nombre = 'iPhone 15 Pro Max';
    INSERT INTO variante_producto (id_variante, id_producto, color, capacidad, precio_extra, stock_disponible, sku, activo, stock_minimo) VALUES
    (uuid_generate_v4(), v_producto_id, 'Titanio Natural', '256GB', 0, 15, 'IP15PM-NAT-256', TRUE, 5),
    (uuid_generate_v4(), v_producto_id, 'Titanio Azul', '256GB', 0, 12, 'IP15PM-BLU-256', TRUE, 5),
    (uuid_generate_v4(), v_producto_id, 'Titanio Blanco', '512GB', 200, 8, 'IP15PM-WHT-512', TRUE, 5),
    (uuid_generate_v4(), v_producto_id, 'Titanio Negro', '1TB', 400, 5, 'IP15PM-BLK-1TB', TRUE, 3);

    -- iPhone 15 Pro
    SELECT id_producto INTO v_producto_id FROM producto WHERE nombre = 'iPhone 15 Pro';
    INSERT INTO variante_producto (id_variante, id_producto, color, capacidad, precio_extra, stock_disponible, sku, activo, stock_minimo) VALUES
    (uuid_generate_v4(), v_producto_id, 'Titanio Natural', '128GB', 0, 20, 'IP15P-NAT-128', TRUE, 5),
    (uuid_generate_v4(), v_producto_id, 'Titanio Azul', '256GB', 100, 15, 'IP15P-BLU-256', TRUE, 5),
    (uuid_generate_v4(), v_producto_id, 'Titanio Blanco', '512GB', 300, 10, 'IP15P-WHT-512', TRUE, 5);

    -- iPhone 15
    SELECT id_producto INTO v_producto_id FROM producto WHERE nombre = 'iPhone 15';
    INSERT INTO variante_producto (id_variante, id_producto, color, capacidad, precio_extra, stock_disponible, sku, activo, stock_minimo) VALUES
    (uuid_generate_v4(), v_producto_id, 'Negro', '128GB', 0, 25, 'IP15-BLK-128', TRUE, 5),
    (uuid_generate_v4(), v_producto_id, 'Blanco', '256GB', 100, 20, 'IP15-WHT-256', TRUE, 5);

    -- MacBook Air M2
    SELECT id_producto INTO v_producto_id FROM producto WHERE nombre = 'MacBook Air M2';
    INSERT INTO variante_producto (id_variante, id_producto, color, capacidad, precio_extra, stock_disponible, sku, activo, stock_minimo) VALUES
    (uuid_generate_v4(), v_producto_id, 'Plateado', '256GB', 0, 10, 'MBA-M2-SLV-256', TRUE, 3),
    (uuid_generate_v4(), v_producto_id, 'Gris Espacial', '512GB', 200, 8, 'MBA-M2-SPG-512', TRUE, 3),
    (uuid_generate_v4(), v_producto_id, 'Medianoche', '1TB', 400, 5, 'MBA-M2-MID-1TB', TRUE, 3);

    -- MacBook Pro 14" M3
    SELECT id_producto INTO v_producto_id FROM producto WHERE nombre = 'MacBook Pro 14" M3';
    INSERT INTO variante_producto (id_variante, id_producto, color, capacidad, precio_extra, stock_disponible, sku, activo, stock_minimo) VALUES
    (uuid_generate_v4(), v_producto_id, 'Plateado', '512GB', 0, 7, 'MBP14-M3-SLV-512', TRUE, 3),
    (uuid_generate_v4(), v_producto_id, 'Gris Espacial', '1TB', 300, 5, 'MBP14-M3-SPG-1TB', TRUE, 3);

    -- iPad Pro 12.9
    SELECT id_producto INTO v_producto_id FROM producto WHERE nombre = 'iPad Pro 12.9" M2';
    INSERT INTO variante_producto (id_variante, id_producto, color, capacidad, precio_extra, stock_disponible, sku, activo, stock_minimo) VALUES
    (uuid_generate_v4(), v_producto_id, 'Gris Espacial', '128GB', 0, 12, 'IPAD-PRO-129-SPG-128', TRUE, 3),
    (uuid_generate_v4(), v_producto_id, 'Plateado', '256GB', 100, 10, 'IPAD-PRO-129-SLV-256', TRUE, 3);

    -- iPad Air
    SELECT id_producto INTO v_producto_id FROM producto WHERE nombre = 'iPad Air 10.9" M1';
    INSERT INTO variante_producto (id_variante, id_producto, color, capacidad, precio_extra, stock_disponible, sku, activo, stock_minimo) VALUES
    (uuid_generate_v4(), v_producto_id, 'Gris Espacial', '64GB', 0, 15, 'IPAD-AIR-SPG-64', TRUE, 3),
    (uuid_generate_v4(), v_producto_id, 'Plateado', '256GB', 150, 10, 'IPAD-AIR-SLV-256', TRUE, 3);

    -- Apple Watch Series 9
    SELECT id_producto INTO v_producto_id FROM producto WHERE nombre = 'Apple Watch Series 9';
    INSERT INTO variante_producto (id_variante, id_producto, color, talla_correa, precio_extra, stock_disponible, sku, activo, stock_minimo) VALUES
    (uuid_generate_v4(), v_producto_id, 'Medianoche', '42mm', 0, 20, 'AWS9-MID-42', TRUE, 5),
    (uuid_generate_v4(), v_producto_id, 'Plateado', '45mm', 50, 15, 'AWS9-SLV-45', TRUE, 5);

    -- Apple Watch Ultra 2
    SELECT id_producto INTO v_producto_id FROM producto WHERE nombre = 'Apple Watch Ultra 2';
    INSERT INTO variante_producto (id_variante, id_producto, color, talla_correa, precio_extra, stock_disponible, sku, activo, stock_minimo) VALUES
    (uuid_generate_v4(), v_producto_id, 'Titanio', '49mm', 0, 8, 'AWU2-TIT-49', TRUE, 3);

    -- AirPods Pro 2
    SELECT id_producto INTO v_producto_id FROM producto WHERE nombre = 'AirPods Pro 2';
    INSERT INTO variante_producto (id_variante, id_producto, color, precio_extra, stock_disponible, sku, activo, stock_minimo) VALUES
    (uuid_generate_v4(), v_producto_id, 'Blanco', 0, 30, 'APP2-WHT', TRUE, 5);

    -- AirPods Max
    SELECT id_producto INTO v_producto_id FROM producto WHERE nombre = 'AirPods Max';
    INSERT INTO variante_producto (id_variante, id_producto, color, precio_extra, stock_disponible, sku, activo, stock_minimo) VALUES
    (uuid_generate_v4(), v_producto_id, 'Plateado', 0, 10, 'APM-SLV', TRUE, 3);

    -- HomePod Mini
    SELECT id_producto INTO v_producto_id FROM producto WHERE nombre = 'HomePod Mini';
    INSERT INTO variante_producto (id_variante, id_producto, color, precio_extra, stock_disponible, sku, activo, stock_minimo) VALUES
    (uuid_generate_v4(), v_producto_id, 'Blanco', 0, 15, 'HPM-WHT', TRUE, 3),
    (uuid_generate_v4(), v_producto_id, 'Negro', 0, 10, 'HPM-BLK', TRUE, 3);
END $$;

-- ======================================================
-- 9. CUPONES DE DESCUENTO
-- ======================================================

INSERT INTO cupon_descuento (id_cupon, codigo, descripcion, porcentaje_descuento, fecha_validez_inicio, fecha_validez_fin, uso_maximo, monto_minimo_compra, activo) VALUES
(uuid_generate_v4(), 'BIENVENIDA10', '10% de descuento para nuevos clientes', 10.00, CURRENT_DATE, CURRENT_DATE + INTERVAL '30 days', 100, 50.00, TRUE),
(uuid_generate_v4(), 'VERANO20', '20% de descuento en productos seleccionados', 20.00, CURRENT_DATE, CURRENT_DATE + INTERVAL '60 days', 50, 100.00, TRUE),
(uuid_generate_v4(), 'FLASH15', '15% de descuento en compras superiores a 200€', 15.00, CURRENT_DATE, CURRENT_DATE + INTERVAL '15 days', 30, 200.00, TRUE);

-- ======================================================
-- 10. VERIFICAR RESULTADOS
-- ======================================================

DO $$
DECLARE
    v_usuarios INT;
    v_productos INT;
    v_variantes INT;
    v_categorias INT;
BEGIN
    SELECT COUNT(*) INTO v_usuarios FROM usuario;
    SELECT COUNT(*) INTO v_productos FROM producto;
    SELECT COUNT(*) INTO v_variantes FROM variante_producto;
    SELECT COUNT(*) INTO v_categorias FROM categoria;
    
    RAISE NOTICE '';
    RAISE NOTICE '==================================================';
    RAISE NOTICE '🍎 DATOS CARGADOS EXITOSAMENTE';
    RAISE NOTICE '==================================================';
    RAISE NOTICE '✅ Usuarios: %', v_usuarios;
    RAISE NOTICE '✅ Productos: %', v_productos;
    RAISE NOTICE '✅ Variantes: %', v_variantes;
    RAISE NOTICE '✅ Categorías: %', v_categorias;
    RAISE NOTICE '==================================================';
    RAISE NOTICE '🔑 CREDENCIALES DE ACCESO:';
    RAISE NOTICE '   Admin: admin@tiendaapple.com / Admin123!';
    RAISE NOTICE '   Usuario: juan@email.com / Cliente123!';
    RAISE NOTICE '==================================================';
    RAISE NOTICE '🌐 Abre http://127.0.0.1:5000';
    RAISE NOTICE '==================================================';
END $$;
-- Insertar categorías principales
INSERT INTO categoria (id_categoria, nombre, slug, descripcion, activo) VALUES
(uuid_generate_v4(), 'iPhone', 'iphone', 'Teléfonos inteligentes Apple', true),
(uuid_generate_v4(), 'iPad', 'ipad', 'Tabletas Apple', true),
(uuid_generate_v4(), 'Mac', 'mac', 'Computadoras Apple', true),
(uuid_generate_v4(), 'Apple Watch', 'apple-watch', 'Relojes inteligentes Apple', true),
(uuid_generate_v4(), 'AirPods', 'airpods', 'Auriculares y audífonos Apple', true),
(uuid_generate_v4(), 'Apple TV', 'apple-tv', 'Dispositivos de streaming Apple', true),
(uuid_generate_v4(), 'Accesorios', 'accesorios', 'Accesorios para dispositivos Apple', true)
ON CONFLICT (slug) DO NOTHING;


-- ======================================================
-- ACTUALIZAR IMAGEN DE CADA PRODUCTO INDIVIDUALMENTE
-- URLs 100% FUNCIONALES DE PLACEHOLD.CO
-- ======================================================

-- iPhone
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/0071e3/ffffff?text=iPhone%2015%20Pro%20Max' WHERE nombre = 'iPhone 15 Pro Max';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/0071e3/ffffff?text=iPhone%2015%20Pro' WHERE nombre = 'iPhone 15 Pro';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/0071e3/ffffff?text=iPhone%2015' WHERE nombre = 'iPhone 15';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/0071e3/ffffff?text=iPhone%2015%20Plus' WHERE nombre = 'iPhone 15 Plus';

-- MacBook
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/1d1d1f/ffffff?text=MacBook%20Air%20M2' WHERE nombre = 'MacBook Air M2';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/1d1d1f/ffffff?text=MacBook%20Air%20M3' WHERE nombre = 'MacBook Air M3';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/1d1d1f/ffffff?text=MacBook%20Pro%2014' WHERE nombre = 'MacBook Pro 14" M3';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/1d1d1f/ffffff?text=MacBook%20Pro%2016' WHERE nombre = 'MacBook Pro 16" M3';

-- iMac / Mac mini / Mac Studio
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/86868b/ffffff?text=iMac%2024' WHERE nombre = 'iMac 24" M3';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/1d1d1f/ffffff?text=Mac%20mini' WHERE nombre = 'Mac mini M2';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/1d1d1f/ffffff?text=Mac%20Studio' WHERE nombre = 'Mac Studio M2';

-- iPad
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/0d1b2a/ffffff?text=iPad%20Pro%2012.9' WHERE nombre = 'iPad Pro 12.9" M2';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/0d1b2a/ffffff?text=iPad%20Pro%2011' WHERE nombre = 'iPad Pro 11" M2';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/0d1b2a/ffffff?text=iPad%20Air' WHERE nombre = 'iPad Air 10.9" M1';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/0d1b2a/ffffff?text=iPad%2010.9' WHERE nombre = 'iPad 10.9" A14';

-- Apple Watch
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/1a1a2e/ffffff?text=Watch%20Ultra%202' WHERE nombre = 'Apple Watch Ultra 2';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/1a1a2e/ffffff?text=Watch%20Series%209' WHERE nombre = 'Apple Watch Series 9';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/1a1a2e/ffffff?text=Watch%20SE' WHERE nombre = 'Apple Watch SE';

-- AirPods
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/2d2d2f/ffffff?text=AirPods%20Pro%202' WHERE nombre = 'AirPods Pro 2';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/2d2d2f/ffffff?text=AirPods%20Max' WHERE nombre = 'AirPods Max';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/2d2d2f/ffffff?text=AirPods%203' WHERE nombre = 'AirPods 3';

-- Apple TV
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/1d1d1f/ffffff?text=Apple%20TV%204K' WHERE nombre = 'Apple TV 4K';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/1d1d1f/ffffff?text=Apple%20TV%20HD' WHERE nombre = 'Apple TV HD';

-- HomePod
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/86868b/ffffff?text=HomePod%202' WHERE nombre = 'HomePod 2';
UPDATE producto SET imagen_url = 'https://placehold.co/400x300/86868b/ffffff?text=HomePod%20Mini' WHERE nombre = 'HomePod Mini';
ALTER TABLE carrito ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE pedido ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;