# Imagen base multiplataforma — funciona en x86_64 y ARM64 (Raspberry Pi 4/5)
FROM python:3.11-slim

# ── Dependencias del sistema ──────────────────────────────────────────────────
# libportaudio2 + portaudio19-dev: necesarios para PyAudio / arecord en ARM
# alsa-utils: provee aplay/arecord
# libasound2-dev + libasound2-plugins: soporte ALSA completo (dmix, dsnoop, etc.)
# libpulse0: cliente PulseAudio (permite funcionar aunque no esté corriendo)
# python3-pyaudio: bindings pre-compilados para ARM (evita compilar con gcc)
# ─────────────────────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        build-essential \
        portaudio19-dev \
        libportaudio2 \
        libasound2-dev \
        libasound2-plugins \
        alsa-utils \
        libpulse0 \
        python3-pyaudio \
        wget \
        unzip \
    && rm -rf /var/lib/apt/lists/*

# ── Configuración ALSA mínima para silenciar errores de PCM inexistentes ─────
# (rear, center_lfe, side, etc.) que no existen en hardware de Raspberry Pi.
# Se copian al contenedor; el archivo real del host se monta via compose
# como /proc/asound (solo lectura) para que ALSA vea las tarjetas reales.
COPY docker/asound.conf /etc/asound.conf

# ── Directorio de trabajo ─────────────────────────────────────────────────────
WORKDIR /app

# ── Dependencias Python ───────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Código del proyecto ───────────────────────────────────────────────────────
# Los modelos pesados (piper/, modelo_vosk/, voz_es.onnx) se montan por volumen
# para no inflar la imagen Docker.
COPY API/              ./API/
COPY App/              ./App/
COPY DataBase/         ./DataBase/
COPY Local_agent_voz.py        .
COPY Local_agent_voz_texto.py  .
