# wsgi.py - Punto de entrada para Vercel
from app import create_app

app = create_app('production')