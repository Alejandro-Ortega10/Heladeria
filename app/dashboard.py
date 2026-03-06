import streamlit as st
import requests
import pandas as pd

# URL base de la API — un solo lugar para cambiarla si es necesario
API_URL = "http://127.0.0.1:8000"

# Configuración de la página
st.set_page_config(
    page_title="Heladería Admin",
    page_icon="🍦",
    layout="wide"
)

# Barra lateral de navegación
st.sidebar.title("🍦 Heladería")
seccion = st.sidebar.radio(
    "Navegación",
    ["📦 Inventario", "💰 Registrar Venta", "📊 Resumen del Día"]
)

# Funciones helper para comunicarse con la API
# En vez de repetir requests.get/post en cada sección,
# usamos estas funciones reutilizables
def api_get(endpoint: str):
    try:
        r = requests.get(f"{API_URL}/{endpoint}", timeout=3)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "No se puede conectar a la API. ¿Esta corriendo el servicio?"
    except Exception as e:
        return None, f"Error: {str(e)}"

def api_post(endpoint: str, payload: dict):
    try:
        r = requests.post(f"{API_URL}/{endpoint}", json=payload, timeout=3)
        return r.json(), r.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

# Verificar que la API esté disponible antes de mostrar cualquier cosa
salud, error = api_get("health")
if error:
    st.error(error)
    st.stop()