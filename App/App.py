import streamlit as st
import requests
import pandas as pd
from datetime import date

# URL base de la API
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
    ["📦 Inventario", "💰 Ventas", "🛒 Compras", "📊 Resumen del Día"] # Se agregaron las 4 secciones solicitadas
)

# Funciones helper para comunicarse con la API (Sin modificar)
def api_get(endpoint: str):
    try:
        r = requests.get(f"{API_URL}/{endpoint}", timeout=3)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "No se puede conectar a la API. ¿Está corriendo el servicio?"
    except Exception as e:
        return None, f"Error: {str(e)}"

def api_post(endpoint: str, payload: dict):
    try:
        r = requests.post(f"{API_URL}/{endpoint}", json=payload, timeout=3)
        return r.json(), r.status_code
    except Exception as e:
        return {"detail": str(e)}, 500


#salud, error = api_get("health")
#if error:
#    st.error(error)
#    st.stop()

# --- DATOS DE PRUEBA (MOCKS) PARA LA INTERFAZ ---
sabores_mock = [
    {"id": 1, "nombre": "Fresa", "precio": 3500.0, "stock": 20},
    {"id": 2, "nombre": "Chocolate", "precio": 4000.0, "stock": 15},
    {"id": 3, "nombre": "Vainilla", "precio": 3000.0, "stock": 30}
]

ventas_mock = pd.DataFrame({
    "Fecha": ["2026-03-07", "2026-03-07", "2026-03-07"],
    "ID Venta": [101, 102, 103],
    "Valor Total Pagado": [10500.0, 8000.0, 15000.0]
})

st.divider()

# --- 1. INVENTARIO ---
if seccion == "📦 Inventario":
    st.header("📦 Inventario de Sabores")
    
    # Encabezados de la tabla
    col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
    col1.write("**ID**")
    col2.write("**Nombre**")
    col3.write("**Precio**")
    col4.write("**Stock**")
    col5.write("**Acción**")
    st.divider()

    # Filas de la tabla
    try:
        r = requests.get(f"{API_URL}/sabores")
        r.raise_for_status()
        sabores = r.json()
    except Exception as e:
        st.error(f"Error al obtener datos: {e}")
    for sabor in sabores:
        c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 2])
        c1.write(sabor["id"])
        c2.write(sabor["nombre"])
        c3.write(f"${sabor['precio']:,.0f}")
        c4.write(sabor["stock"])
        
        # Botón para modificar
        if c5.button("Modificar", key=f"btn_mod_{sabor['id']}"):
            st.session_state.modificando_id = sabor["id"]

    # Menú desplegable para modificar si se presionó el botón
    if "modificando_id" in st.session_state:
        st.write("---")
        st.subheader(f"Modificando Sabor ID: {st.session_state.modificando_id}")
        with st.form("form_modificar"):
            mod_nombre = st.text_input("Nuevo Nombre")
            mod_precio = st.number_input("Nuevo Precio", min_value=0.0, step=100.0)
            mod_stock = st.number_input("Nuevo Stock", min_value=0, step=1)
            btn_guardar = st.form_submit_button("Guardar Cambios")
            if btn_guardar:
                st.success("Cambios guardados visualmente.")

# --- 2. VENTAS ---
elif seccion == "💰 Ventas":
    st.header("💰 Registrar Nueva Venta")
    
    # Encabezados
    col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
    col1.write("**ID**")
    col2.write("**Nombre**")
    col3.write("**Precio Unitario**")
    col4.write("**Cantidad**")
    col5.write("**Valor Total**")
    st.divider()

    total_venta = 0.0

    # Filas de productos disponibles para vender
    for sabor in sabores_mock:
        c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 2])
        c1.write(sabor["id"])
        c2.write(sabor["nombre"])
        c3.write(f"${sabor['precio']:,.0f}")
        
        # st.number_input incluye nativamente los botones de subir y bajar cantidad
        cantidad = c4.number_input("Cant.", min_value=0, max_value=sabor["stock"], step=1, key=f"cant_v_{sabor['id']}", label_visibility="collapsed")
        
        subtotal = cantidad * sabor["precio"]
        total_venta += subtotal
        c5.write(f"${subtotal:,.0f}")

    st.divider()
    
    # Total y Botón de Vender (Fuera de la tabla)
    col_vacio, col_total = st.columns([4, 1])
    col_total.subheader(f"Total: ${total_venta:,.0f}")
    
    if st.button("Vender", type="primary", use_container_width=True):
        st.success("Venta efectuada visualmente.")

# --- 3. COMPRAS ---
elif seccion == "🛒 Compras":
    st.header("🛒 Registrar Nueva Compra (Abastecimiento)")
    
    # Encabezados
    col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
    col1.write("**ID**")
    col2.write("**Nombre**")
    col3.write("**Costo Unitario**")
    col4.write("**Cantidad Comprada**")
    col5.write("**Costo Total**")
    st.divider()

    total_compra = 0.0

    # Filas de productos para comprar/abastecer
    for sabor in sabores_mock:
        c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 2])
        c1.write(sabor["id"])
        c2.write(sabor["nombre"])
        
        # En compras, el precio de costo puede variar, así que permitimos editarlo visualmente
        costo_unitario = c3.number_input("Costo", min_value=0.0, value=sabor["precio"]*0.5, step=100.0, key=f"costo_c_{sabor['id']}", label_visibility="collapsed")
        cantidad = c4.number_input("Cant.", min_value=0, step=1, key=f"cant_c_{sabor['id']}", label_visibility="collapsed")
        
        subtotal = cantidad * costo_unitario
        total_compra += subtotal
        c5.write(f"${subtotal:,.0f}")

    st.divider()
    
    # Total y Botón de Comprar (Fuera de la tabla)
    col_vacio, col_total = st.columns([4, 1])
    col_total.subheader(f"Total: ${total_compra:,.0f}")
    
    if st.button("Registrar Compra", type="primary", use_container_width=True):
        st.success("Compra registrada visualmente.")

# --- 4. RESUMEN DEL DÍA ---
elif seccion == "📊 Resumen del Día":
    st.header("📊 Resumen de Ventas Diarias")
    
    # Campo para seleccionar fecha
    fecha_busqueda = st.date_input("Seleccionar Fecha", date.today())
    
    st.button("Buscar Ventas")
    st.divider()
    
    # Mostrar tabla estática con los resultados
    st.subheader(f"Ventas del día: {fecha_busqueda}")
    st.dataframe(ventas_mock, use_container_width=True, hide_index=True)