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

# ============================================================
# SECCIÓN: INVENTARIO
# Se muestra cuando el usuario selecciona "📦 Inventario"
# ============================================================
if seccion == "📦 Inventario":
    st.header("📦 Inventario de Sabores")

    # Botón para recargar los datos sin refrescar toda la página
    if st.button("🔄 Actualizar Inventario"):
        st.rerun()

    # Pedir los datos a la API
    data, err = api_get("sabores")
    if err:
        st.error(err)
    else:
        # Convertir la lista de sabores en una tabla de pandas
        df = pd.DataFrame(data["inventario"])

        # Función que colorea las filas según el nivel de stock
        # Rojo: stock crítico (menos de 10)
        # Amarillo: stock bajo (entre 10 y 20)
        # Sin color: stock normal (más de 20)
        def color_stock(val):
            if val < 10:
                return 'background-color: #ffcccc'  # rojo
            elif val < 20:
                return 'background-color: #fff3cc'  # amarillo
            return ''

        styled = df.style.applymap(color_stock, subset=['stock'])
        st.dataframe(styled, use_container_width=True)

# ── Formulario: Agregar nuevo sabor ──────────────────────
    # st.expander crea una sección colapsable — no ocupa espacio hasta que se abre
    with st.expander("➕ Agregar Nuevo Sabor"):
        with st.form("form_nuevo_sabor"):
            nombre = st.text_input("Nombre del sabor")
            precio = st.number_input("Precio (COP)", min_value=0.0, step=500.0)
            stock_ini = st.number_input("Stock inicial", min_value=0, step=1)
            submitted = st.form_submit_button("Agregar")
            if submitted:
                if not nombre:  # validar que el nombre no esté vacío
                    st.warning("El nombre del sabor no puede estar vacío.")
                else:
                    resp, code = api_post("sabores", {"nombre": nombre, "precio": precio, "stock": stock_ini})
                    if code == 201:
                        st.success(f"Sabor '{nombre}' agregado!")
                        st.rerun()
                    else:
                        st.error(f"Error: {resp.get('detail')}")

    # ── Formulario: Actualizar stock ──────────────────────────
    with st.expander("Actualizar Stock"):
        data2, _ = api_get("sabores")
        if data2:
            # Crear diccionario {nombre: id} para el selectbox
            sabores_dict = {s['nombre']: s['id'] for s in data2["inventario"]}
            sel = st.selectbox("Seleccionar sabor", list(sabores_dict.keys()))
            nuevo_stock = st.number_input("Nuevo stock", min_value=0, step=1)
            if st.button("Actualizar Stock"):
                import requests as req
                r = req.put(f"{API_URL}/sabores/{sabores_dict[sel]}", json={"stock": nuevo_stock})
                if r.status_code == 200:
                    st.success("Stock actualizado!")
                    st.rerun()