# app.py - Punto de entrada para Vercel
from app import create_app

app = create_app('production')  # o 'development' según necesites

# Para Vercel, la variable debe llamarse 'app'
# Si usas 'application', también funciona, pero 'app' es más común