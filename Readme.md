## 🚀 Cómo empezar

1. **Preparar el entorno (Solo la primera vez):**

    # Activar el entorno

    source venv/bin/activate

2. **Ejecución del Sistema:**

    Es necesario abrir **dos terminales** y activar el entorno en cada una:

    **Terminal 1: API (Servidor)**
    source venv/bin/activate
    uvicorn API.main:app --reload --host 0.0.0.0 --port 8000

   **Terminal 2: Dashboard (Interfaz)**

    source venv/bin/activate
    streamlit run App/App.py

3.
3.1 Ubicación de la carpeta 
    Primero, asegúrate de estar en el directorio principal de la heladería:
3.2 Descarga del Binario de Piper
    Dependiendo de tu sistema operativo, descarga el archivo comprimido:
    Para PC (Ubuntu/Linux x86_64): https://huggingface.co/rhasspy/piper-voices/tree/main/es/es_MX/claude/high
    Para Raspberry Pi (64-bit aarch64): https://huggingface.co/rhasspy/piper-voices/tree/main/es/es_MX/claude/high
    Luego, descomprímelo dentro de la carpeta del proyecto:

3.3 Descarga de los Modelos de Voz
    Para que la heladería hable en español, necesitamos los archivos de modelo. Descarga ambos y colócalos en la raíz de /Heladeria:
    Archivo ONNX (Voz): https://huggingface.co/rhasspy/piper-voices/tree/main/es/es_MX/ald/medium
    Archivo JSON (Configuración): https://huggingface.co/rhasspy/piper-voices/tree/main/es/es_MX/ald/medium

3.4 Configuración de Permisos (Opcional)
    Es crucial darle permisos de ejecución al binario de Piper para que Python pueda utilizarlo. Ajusta la ruta según cómo se haya extraído la carpeta:
    chmod +x ./piper/piper

## 📁 Estructura

- `API/`: Lógica FastAPI (Ventas, Compras, Inventario).
- `App/`: Interfaz Streamlit.
- `DataBase/`: Base de Datos SQLite y Script de creación.
- `venv/`: Entorno virtual con dependencias.