import streamlit as st
import requests
import os

st.set_page_config(page_title="Heladería Unificada", layout="wide")

# Función para verificar conexión con la API
def check_api():
    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        return r.status_code == 200
    except:
        return False

# Sidebar
st.sidebar.title("Heladería")
if not check_api():
    st.sidebar.error("API Offline")
else:
    st.sidebar.success("API Online")

seccion = st.sidebar.radio("Navegación", ["Inventario", "Ventas", "Compras"])

def get_inventario():
    try:
        r = requests.get(f"{API_URL}/inventario")
        return r.json() if r.status_code == 200 else []
    except:
        return []

def delete_sabor(id):
    try:
        r = requests.delete(f"{API_URL}/inventario/{id}")
        return r.status_code == 200
    except:
        return False

def get_ventas():
    try:
        r = requests.get(f"{API_URL}/ventas")
        return r.json() if r.status_code == 200 else []
    except:
        return []

def get_compras():
    try:
        r = requests.get(f"{API_URL}/compras")
        return r.json() if r.status_code == 200 else []
    except:
        return []

# --- SECCIÓN INVENTARIO ---
if seccion == "Inventario":
    st.header("Gestión de Inventario")
    
    sabores = get_inventario()
    
    # Tabla simple de inventario
    if sabores:
        col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
        col1.write("**ID**")
        col2.write("**Nombre**")
        col3.write("**Precio**")
        col4.write("**Stock**")
        col5.write("**Acciones**")
        st.divider()

        for s in sabores:
            c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 2])
            c1.text(s["id"])
            c2.text(s["nombre"])
            c3.text(f"${s['precio']:,.0f}")
            c4.text(s["stock"])
            
            # Botones de Acción
            btn_col1, btn_col2 = c5.columns(2)
            if btn_col1.button("Editar", key=f"edit_{s['id']}"):
                st.session_state.edit_id = s["id"]
                st.session_state.edit_data = s
            
            if btn_col2.button("Eliminar", key=f"del_{s['id']}"):
                if delete_sabor(s["id"]):
                    st.success(f"Sabor eliminado: {s['nombre']}")
                    st.rerun()
                else:
                    st.error("Error al eliminar")

    # Formulario de Edición
    if "edit_id" in st.session_state:
        with st.expander("📝 Editar Sabor", expanded=True):
            d = st.session_state.edit_data
            with st.form("form_edit"):
                name = st.text_input("Nombre", value=d["nombre"])
                price = st.number_input("Precio", value=float(d["precio"]))
                stock = st.number_input("Stock", value=int(d["stock"]))
                if st.form_submit_button("Guardar"):
                    res = requests.put(f"{API_URL}/inventario", json={"id": d["id"], "nombre": name, "precio": price, "stock": stock})
                    if res.status_code == 200:
                        st.success("Actualizado")
                        del st.session_state.edit_id
                        st.rerun()

    # Formulario Nuevo
    with st.expander("➕ Agregar Sabor"):
        with st.form("form_new"):
            n_name = st.text_input("Nombre")
            n_price = st.number_input("Precio", min_value=0.0)
            n_stock = st.number_input("Stock Inicial", min_value=0)
            if st.form_submit_button("Agregar"):
                res = requests.post(f"{API_URL}/inventario", json={"nombre": n_name, "precio": n_price, "stock": n_stock})
                if res.status_code == 200:
                    st.success("Agregado")
                    st.rerun()

# --- SECCIÓN VENTAS ---
elif seccion == "Ventas":
    st.header("Gestión de Ventas")
    tab1, tab2 = st.tabs(["Registrar Venta", "Historial"])

    with tab1:
        sabores = get_inventario()
        items_venta = []
        total = 0

        if sabores:
            for s in sabores:
                col1, col2, col3 = st.columns([3, 2, 2])
                col1.write(f"**{s['nombre']}** (${s['precio']:,.0f})")
                cant = col2.number_input(f"Cantidad", min_value=0, max_value=s["stock"], key=f"v_{s['id']}")
                sub = cant * s["precio"]
                col3.write(f"Subtotal: ${sub:,.0f}")
                if cant > 0:
                    items_venta.append({"idSabor": s["id"], "cantidad": cant})
                    total += sub
            
            st.divider()
            st.subheader(f"Total Venta: ${total:,.0f}")
            if st.button("Finalizar Venta", type="primary", disabled=len(items_venta)==0):
                res = requests.post(f"{API_URL}/ventas", json={"items": items_venta})
                if res.status_code == 200:
                    st.success(f"Venta realizada: #{res.json()['venta_id']}")
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "Error"))
    
    with tab2:
        ventas_h = get_ventas()
        if not ventas_h:
            st.info("No hay ventas registradas.")
        for v in ventas_h:
            with st.expander(f"Venta #{v['id']} - {v['fecha']} - Total: ${v['total']:,.0f}"):
                st.write("**Detalles:**")
                for item in v["items"]:
                    st.write(f"- {item['nombre']} x{item['cantidad']} (${item['precio_unitario']:,.0f} c/u)")

# --- SECCIÓN COMPRAS ---
elif seccion == "Compras":
    st.header("Gestión de Compras")
    tab1, tab2 = st.tabs(["Registrar Compra", "Historial"])

    with tab1:
        sabores = get_inventario()
        items_compra = []
        total_costo = 0

        if sabores:
            for s in sabores:
                col1, col2 = st.columns([3, 2])
                col1.write(f"**{s['nombre']}** (Stock: {s['stock']})")
                cant = col2.number_input(f"Cantidad a comprar", min_value=0, key=f"c_{s['id']}")
                if cant > 0:
                    items_compra.append({"sabor_id": s["id"], "cantidad_comprada": cant})
                    total_costo += (cant * s["precio"])
            
            st.divider()
            st.subheader(f"Inversión Total: ${total_costo:,.0f}")
            if st.button("Registrar Compra", type="primary", disabled=len(items_compra)==0):
                res = requests.post(f"{API_URL}/compras", json={"items": items_compra, "total_compra": total_costo})
                if res.status_code == 200:
                    st.success("Inventario actualizado")
                    st.rerun()
    
    with tab2:
        compras_h = get_compras()
        if not compras_h:
            st.info("No hay compras registradas.")
        for c in compras_h:
            with st.expander(f"Compra #{c['id']} - {c['fecha']} - Total: ${c['total_compra']:,.0f}"):
                st.write("**Detalles:**")
                for item in c["items"]:
                    st.write(f"- {item['nombre']} x{item['cantidad_comprada']}")