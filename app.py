# app.py - Punto de entrada para Vercel
from app import create_app

# Crear la aplicación en modo producción
app = create_app('production')

# Algunos entornos esperan 'application'
application = app