# wsgi.py - Punto de entrada para Vercel
import sys
import os

# Asegurar que las variables de entorno estén disponibles
# (Vercel las inyecta, pero por si acaso)

from app import create_app

# Crear la aplicación en modo producción
app = create_app('production')

# Algunos entornos esperan 'application'
application = app

# Imprimir en logs que la app ha arrancado
print("🚀 Aplicación iniciada correctamente en modo producción")