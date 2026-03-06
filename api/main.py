# ============================================================
# api/main.py — Servidor principal de la API de la Heladería
# ============================================================
# Este archivo configura y lanza el servidor FastAPI.
# Es el punto de entrada de toda la API — aquí se define
# cómo responde el servidor, qué rutas existen y cómo
# maneja los errores.
# ============================================================

# --- Importaciones de FastAPI ---
# FastAPI: el framework para crear la API
# HTTPException: para lanzar errores HTTP controlados (ej: 404, 400)
# Request: representa la petición que llega al servidor
from fastapi import FastAPI, HTTPException, Request

# CORSMiddleware: permite que Streamlit (otro puerto) hable con esta API
from fastapi.middleware.cors import CORSMiddleware

# JSONResponse: para construir respuestas JSON personalizadas
from fastapi.responses import JSONResponse

# sqlite3: librería de Python para conectarse a la base de datos
import sqlite3

# sys y os: módulos del sistema para manipular rutas de archivos
import sys
import os

# --- Ajuste de rutas para importar desde carpetas hermanas ---
# __file__ = ruta de este archivo (api/main.py)
# os.path.join(..., '..') = sube un nivel → raíz del proyecto
# sys.path.insert(0, ...) = le dice a Python que busque módulos desde ahí
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa la ruta de la base de datos desde db/DataBase.py
# Así no repetimos la ruta en cada archivo (principio DRY)
from db.DataBase import DB_PATH

# --- Creación de la aplicación FastAPI ---
# Este objeto 'app' es el servidor. Todo endpoint y middleware
# se conecta a él. El título y descripción aparecen en /docs
app = FastAPI(
    title="Heladería API",
    description="API REST para el sistema de gestión de heladería offline",
    version="1.0.0"
)

# --- Configuración de CORS ---
# CORS evita que el navegador bloquee peticiones entre puertos distintos.
# Streamlit corre en :8501 y la API en :8000 — sin esto no se comunican.
# Se ponen localhost y 127.0.0.1 porque algunos sistemas usan uno u otro.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_methods=["*"],   # Permite GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],   # Permite cualquier cabecera HTTP
)

# --- Función reutilizable de conexión a la base de datos ---
# En vez de repetir sqlite3.connect() en cada endpoint,
# todos los endpoints llamarán a esta función.
# row_factory = sqlite3.Row permite acceder a columnas por nombre:
# ej: row["nombre"] en vez de row[1]
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Endpoint de salud ---
# Una "puerta" simple para verificar que el servidor está vivo.
# Si responde {"status": "ok"} → el servidor está funcionando.
# Útil para diagnóstico y monitoreo.
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Heladeria API"}

# --- Manejador global de errores HTTP (FastAPI) ---
# Intercepta cualquier HTTPException lanzada dentro de los endpoints.
# Estandariza el formato de error para que el dashboard siempre
# reciba la misma estructura: {"error": true, "detail": "...", "code": ...}
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "detail": exc.detail, "code": exc.status_code}
    )

# --- Manejador global de errores (Starlette) ---
# FastAPI está construido sobre Starlette. Algunos errores como el 404
# de rutas inexistentes los genera Starlette directamente, no FastAPI.
# Este segundo manejador los captura para mantener el mismo formato.
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "detail": exc.detail, "code": exc.status_code}
    )