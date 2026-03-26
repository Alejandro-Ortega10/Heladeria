#!/bin/bash
# =================================================================
# SCRIPT DE DESPLIEGUE PARA RASPBERRY PI
# Ejecutar directamente en la Raspberry Pi con:
#   bash deploy_raspberry.sh
# =================================================================

set -e  # Detener si hay error

# Detectar usuario actual
CURRENT_USER=$(whoami)
PROJECT_DIR="$(pwd)" # El directorio desde donde se ejecuta el script
echo "=== PREPARANDO RASPBERRY PI PARA HELADERIA (Usuario: $CURRENT_USER) ==="

# 1. Instalar dependencias del sistema
echo "[1/6] Instalando dependencias del sistema..."
sudo apt-get update -qq
sudo apt-get install -y \
    docker.io docker-compose \
    portaudio19-dev alsa-utils \
    wget unzip curl

# 2. Habilitar Docker sin sudo
sudo usermod -aG docker $CURRENT_USER
echo "      Docker instalado correctamente para $CURRENT_USER."

# 3. Instalar Ollama (IA local) en el HOST de la Raspberry (no en Docker)
echo "[2/6] Instalando Ollama..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
    sudo systemctl enable ollama
    sudo systemctl start ollama
    sleep 3  # Esperar que inicie
    echo "      Descargando modelo llama3.2 (puede tardar varios minutos)..."
    ollama pull llama3.2
else
    echo "      Ollama ya está instalado."
fi

# 4. Descargar modelo Vosk (reconocimiento de voz en español)
echo "[3/6] Descargando modelo Vosk..."
cd "$PROJECT_DIR"
if [ ! -d "modelo_vosk" ]; then
    wget -q https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip
    unzip -q vosk-model-small-es-0.42.zip
    mv vosk-model-small-es-0.42 modelo_vosk
    rm vosk-model-small-es-0.42.zip
    echo "      Modelo Vosk descargado."
else
    echo "      Modelo Vosk ya existe, omitiendo."
fi

# 5. Descargar Piper TTS (versión ARM64 para Raspberry Pi)
echo "[4/6] Descargando Piper TTS (ARM64)..."
if [ ! -f "piper/piper" ]; then
    wget -q https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_aarch64.tar.gz
    tar -xzf piper_linux_aarch64.tar.gz
    chmod +x ./piper/piper
    rm piper_linux_aarch64.tar.gz
    echo "      Piper ARM64 descargado."
else
    echo "      Piper ya existe, omitiendo."
fi

# 6. Descargar modelos de voz en español (Piper)
echo "[5/6] Descargando modelos de voz..."
if [ ! -f "voz_es.onnx" ]; then
    wget -q -O voz_es.onnx \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/ald/medium/es_MX-ald-medium.onnx"
    wget -q -O voz_es.onnx.json \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/ald/medium/es_MX-ald-medium.onnx.json"
    echo "      Modelos de voz descargados."
else
    echo "      Modelos de voz ya existen, omitiendo."
fi

# 7. Construir y levantar contenedores Docker
echo "[6/6] Construyendo y levantando contenedores..."
docker-compose build
docker-compose up -d

echo ""
echo "======================================================"
echo "✅ DESPLIEGUE COMPLETADO"
echo "   Dashboard: http://$(hostname -I | awk '{print $1}'):8501"
echo "   API:        http://$(hostname -I | awk '{print $1}'):8000"
echo "   La IA de Voz está escuchando en el contenedor 'heladeria-voz'"
echo ""
echo "Comandos útiles:"
echo "   docker-compose logs -f voz   # Ver logs del agente de voz"
echo "   docker-compose restart       # Reiniciar todo"
echo "   docker-compose down          # Detener todo"
echo "======================================================"
