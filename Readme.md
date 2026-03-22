## 🚀 Cómo empezar

1. **Preparar el entorno (Solo la primera vez)**
    * Crear y activar el entorno virtual:
      ```bash
      python3 -m venv venv
      source venv/bin/activate
      ```
    * Instalar dependencias:
      ```bash
      pip install fastapi uvicorn streamlit requests ollama vosk pyaudio
      ```

2. **Ejecución del Sistema**
    * Es necesario abrir **dos terminales** y activar el entorno en cada una:
    * **Terminal 1: API (Servidor)**
        * `source venv/bin/activate`
        * `uvicorn API.main:app --reload --host 0.0.0.0 --port 8000`
    * **Terminal 2: Dashboard (Interfaz)**
        * `source venv/bin/activate`
        * `streamlit run App/App.py`

3. **Configuración de Voz (Piper TTS)**
    * **3.1 Ubicación de la carpeta**
        * Asegúrate de estar en el directorio principal del proyecto: `/home/user/Programacion/Heladeria`
    * **3.2 Descarga del Binario de Piper**
        * Descarga el archivo según la arquitectura de tu máquina:
            * **Para PC (Ubuntu/Linux x86_64):** [Descargar Piper x86_64](https://github.com/rhasspy/piper/releases/)
            * **Para Raspberry Pi (64-bit aarch64):** [Descargar Piper aarch64](https://github.com/rhasspy/piper/releases/)
        * Descomprime el archivo en la raíz del proyecto:
          ```bash
          tar -xvf piper_linux_nombre_arquitectura.tar.gz
          ```
    * **3.3 Descarga de los Modelos de Voz**
        * Descarga estos dos archivos y guárdalos directamente en la carpeta raíz `/Heladeria`:
            * **Modelo de Voz (.onnx):** [es_MX-aldona-medium.onnx](https://huggingface.co/rhasspy/piper-voices/tree/main/es/es_MX/ald/medium)
            * **Configuración (.json):** [es_MX-aldona-medium.onnx.json](https://huggingface.co/rhasspy/piper-voices/tree/main/es/es_MX/ald/medium)
            * Guarda los archivos como voz_es.onnx y voz_es.onnx.json
    * **3.4 Configuración de Permisos**
        * Es fundamental dar permisos de ejecución al binario de Piper (ajusta la ruta según tu carpeta):
          ```bash
          chmod +x ./piper/piper
          ```

4. **Ejecución del Agente de Voz**
    * En una nueva terminal con el entorno activo, ejecuta:
      ```bash
      python3 local_agent_voz.py
      ```

5. **Configuración de Escucha (Vosk STT)**
    * **5.1 Instalación de dependencias de audio**
        * Para que el sistema reconozca el micrófono en Linux:
          ```bash
          sudo apt-get install python3-pyaudio portaudio19-dev alsa-utils -y
          ```
    * **5.2 Descarga del Modelo de Lenguaje**
        * Descarga el modelo de reconocimiento de voz para español:
            * **Vosk Spanish Small Model:** [Descargar vosk-model-small-es-0.42](https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip)
        * Descomprime el archivo en la raíz del proyecto y renombra la carpeta a `modelo_vosk`:
          ```bash
          unzip vosk-model-small-es-0.42.zip
          mv vosk-model-small-es-0.42 modelo_vosk
          ```

## 📁 Estructura del Proyecto

* **`API/`**: Lógica de la heladería con FastAPI (Ventas, Inventario).
* **`App/`**: Interfaz visual desarrollada en Streamlit.
* **`DataBase/`**: Archivo SQLite y scripts de base de datos.
* **`mcp/`**: Agentes de IA y lógica de integración.
* **`piper/`**: Binarios y ejecutables del motor de voz.
* **`modelo_vosk/`**: Archivos del modelo de reconocimiento de voz (STT).
* **`venv/`**: Entorno virtual de Python con las librerías necesarias.