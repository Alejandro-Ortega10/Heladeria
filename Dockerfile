# Imagen base multiplataforma (funciona en x86_64 y ARM64 Raspberry Pi)
FROM python:3.11-slim

# --- Dependencias del sistema (audio, utilidades) ---
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    alsa-utils \
    libasound2-dev \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# --- Directorio de trabajo ---
WORKDIR /app

# --- Copiar e instalar dependencias Python ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Copiar el código del proyecto ---
# Los modelos pesados (piper/, modelo_vosk/, voz_es.onnx) se montan por volumen
# para no inflar la imagen Docker
COPY API/ ./API/
COPY App/ ./App/
COPY DataBase/ ./DataBase/
COPY Local_agent_voz.py .
COPY Local_agent_voz_texto.py .
