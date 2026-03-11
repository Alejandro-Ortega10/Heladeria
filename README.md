# 🍦 Heladería Unificada

Versión simplificada y unificada del sistema de gestión de heladería.

## 🚀 Cómo empezar

1. **Preparar el entorno (Solo la primera vez):**

   # Activar el entorno

   source venv/bin/activate

2. **Ejecución del Sistema:**

   Es necesario abrir **dos terminales** y activar el entorno en cada una:

   **Terminal 1: API (Servidor)**
   source venv/bin/activate
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

   **Terminal 2: Dashboard (Interfaz)**

   source venv/bin/activate
   streamlit run app/dashboard.py

## 📁 Estructura

- `api/`: Lógica FastAPI (Ventas, Compras, Inventario).
- `app/`: Interfaz Streamlit.
- `db/`: Base de Datos SQLite y Script de creación.
- `venv/`: Entorno virtual con dependencias.
