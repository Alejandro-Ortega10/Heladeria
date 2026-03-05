import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Panel de administración - Heladería", layout="centered")

API_BASE = "http://127.0.0.1:8000"

st.title("Panel de administración")
st.subheader("Heladería La Dulce")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 Mostrar datos"):
        try:
            r = requests.get(f"{API_BASE}/sabores")
            r.raise_for_status()

            sabores = r.json()

            if sabores:
                df = pd.DataFrame(sabores)

                st.success(f"Se encontraron {len(df)} registros")

                # Mostrar tabla tipo base de datos
                st.table(df)

            else:
                st.info("La tabla sabores está vacía")

        except Exception as e:
            st.error(f"Error al obtener datos: {e}")

with col2:
    if st.button("🧹 Limpiar sabores"):
        if st.checkbox("Confirmar eliminación", key="confirm"):
            try:
                requests.delete(f"{API_BASE}/sabores")
                st.success("Registros eliminados")
            except Exception as e:
                st.error(e)

st.markdown("---")
st.caption("Asegúrate de que la API esté corriendo.")