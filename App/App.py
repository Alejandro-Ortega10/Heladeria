import streamlit as st
import requests

# URL base de la API
API_URL = "http://127.0.0.1:8000"

# Configuración de la página
st.set_page_config(page_title="Heladería Admin", page_icon="🍦", layout="wide")

# Barra lateral de navegación
st.sidebar.title("🍦 Heladería")
seccion = st.sidebar.radio(
    "Navegación",
    ["📦 Inventario", "💰 Ventas", "🛒 Compras"] 
)

def obtener_inventario():
    try:
        r = requests.get(f"{API_URL}/inventario", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"Error al conectar con la API: {e}")
    return []

st.divider()

# --- 1. INVENTARIO ---
if seccion == "📦 Inventario":
    st.header("📦 Inventario de Sabores")
    
    col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
    col1.write("**ID**")
    col2.write("**Nombre**")
    col3.write("**Precio**")
    col4.write("**Stock**")
    col5.write("**Acción**")
    st.divider()

    sabores = obtener_inventario()
    
    for sabor in sabores:
        c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 2])
        c1.write(sabor["id"])
        c2.write(sabor["nombre"])
        c3.write(f"${sabor['precio']:,.0f}")
        c4.write(sabor["stock"])
        
        if c5.button("Modificar", key=f"btn_mod_{sabor['id']}"):
            st.session_state.modificando_id = sabor["id"]
            st.session_state.modificando_datos = sabor

    # Formulario para modificar un sabor existente
    if "modificando_id" in st.session_state:
        st.write("---")
        datos_actuales = st.session_state.modificando_datos
        st.subheader(f"Modificando Sabor: {datos_actuales['nombre']}")
        
        with st.form("form_modificar"):
            mod_nombre = st.text_input("Nuevo Nombre", value=datos_actuales["nombre"])
            mod_precio = st.number_input("Nuevo Precio", min_value=0.0, value=float(datos_actuales["precio"]), step=100.0)
            mod_stock = st.number_input("Nuevo Stock", min_value=0, value=int(datos_actuales["stock"]), step=1)
            
            if st.form_submit_button("Guardar Cambios"):
                payload = {
                    "id": st.session_state.modificando_id,
                    "nombre": mod_nombre,
                    "precio": mod_precio,
                    "stock": mod_stock
                }
                r = requests.put(f"{API_URL}/inventario/", json=payload)
                if r.status_code == 200:
                    st.success("Inventario actualizado con éxito")
                    del st.session_state.modificando_id
                    del st.session_state.modificando_datos
                    st.rerun()
                else:
                    st.error(f"Error: {r.json().get('detail', 'Error desconocido')}")

    # Formulario para agregar un nuevo sabor
    st.write("---")
    st.subheader("Agregar Nuevo Sabor")
    with st.form("form_nuevo"):
        nuevo_nombre = st.text_input("Nombre")
        nuevo_precio = st.number_input("Precio", min_value=0.0, step=100.0)
        nuevo_stock = st.number_input("Stock Inicial", min_value=0, step=1)
        
        if st.form_submit_button("Agregar Sabor"):
            payload = {"nombre": nuevo_nombre, "precio": nuevo_precio, "stock": nuevo_stock}
            r = requests.post(f"{API_URL}/inventario/", json=payload)
            if r.status_code == 200:
                st.success("Sabor agregado con éxito")
                st.rerun()
            else:
                st.error("Error al agregar el sabor")

# --- 2. VENTAS ---
elif seccion == "💰 Ventas":
    st.header("💰 Registrar Nueva Venta")
    
    col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
    col1.write("**ID**")
    col2.write("**Nombre**")
    col3.write("**Precio Unitario**")
    col4.write("**Cantidad**")
    col5.write("**Valor Total**")
    st.divider()

    sabores = obtener_inventario()
    total_venta = 0.0
    items_venta = []

    for sabor in sabores:
        c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 2])
        c1.write(sabor["id"])
        c2.write(sabor["nombre"])
        c3.write(f"${sabor['precio']:,.0f}")
        
        cantidad = c4.number_input("Cant.", min_value=0, max_value=sabor["stock"], step=1, key=f"cant_v_{sabor['id']}", label_visibility="collapsed")
        
        subtotal = cantidad * sabor["precio"]
        total_venta += subtotal
        c5.write(f"${subtotal:,.0f}")

        if cantidad > 0:
            items_venta.append({"idSabor": sabor["id"], "cantidad": cantidad})

    st.divider()
    
    col_vacio, col_total = st.columns([4, 1])
    col_total.subheader(f"Total: ${total_venta:,.0f}")
    
    if st.button("Registrar Venta", type="primary", use_container_width=True, disabled=len(items_venta)==0):
        payload = {"items": items_venta}
        r = requests.post(f"{API_URL}/ventas/", json=payload)
        
        if r.status_code == 200:
            data = r.json()
            st.success(f"Venta #{data['venta_id']} registrada con éxito. Total cobrado: ${data['total']:,.0f}")
        else:
            st.error(f"Error en la venta: {r.json().get('detail', 'Error de conexión')}")

# --- 3. COMPRAS ---
elif seccion == "🛒 Compras":
    st.header("🛒 Registrar Nueva Compra (Abastecimiento)")
    
    col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
    col1.write("**ID**")
    col2.write("**Nombre**")
    col3.write("**Costo Unitario**")
    col4.write("**Cantidad Comprada**")
    col5.write("**Costo Total**")
    st.divider()

    sabores = obtener_inventario()
    total_compra = 0.0
    items_compra = []

    for sabor in sabores:
        c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 2])
        c1.write(sabor["id"])
        c2.write(sabor["nombre"])
        
        costo_unitario = c3.number_input("Costo", min_value=0.0, value=float(sabor["precio"]*0.5), step=100.0, key=f"costo_c_{sabor['id']}", label_visibility="collapsed")
        cantidad = c4.number_input("Cant.", min_value=0, step=1, key=f"cant_c_{sabor['id']}", label_visibility="collapsed")
        
        subtotal = cantidad * costo_unitario
        total_compra += subtotal
        c5.write(f"${subtotal:,.0f}")

        if cantidad > 0:
            items_compra.append({"sabor_id": sabor["id"], "cantidad_comprada": cantidad})

    st.divider()
    
    col_vacio, col_total = st.columns([4, 1])
    col_total.subheader(f"Total: ${total_compra:,.0f}")
    
    if st.button("Registrar Compra", type="primary", use_container_width=True, disabled=len(items_compra)==0):
        payload = {
            "items": items_compra,
            "total_compra": total_compra
        }
        r = requests.post(f"{API_URL}/compras/", json=payload)
        
        if r.status_code == 200:
            st.success(f"Compra registrada correctamente. Inventario abastecido.")
        else:
            st.error(f"Error en la compra: {r.json().get('detail', 'Error de conexión')}")