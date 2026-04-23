import ollama
import requests
import json
import subprocess
import pyaudio
import os
import sys
from vosk import Model, KaldiRecognizer

# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────
API_URL      = os.getenv("API_URL",      "http://localhost:8000")
OLLAMA_HOST  = os.getenv("OLLAMA_HOST",  "http://localhost:11434")
MODELO       = os.getenv("OLLAMA_MODEL", "llama3.2")
PIPER_BIN    = "./piper/piper"
VOZ_MODELO   = "voz_es.onnx"

# Índice de tarjeta de sonido para ALSA (puede ser anulado por variable de entorno).
# En la Raspberry Pi con micrófono USB lo más común es tarjeta 1 o 2.
# Déjalo en None para detección automática (primer device con entradas).
ALSA_CARD = os.getenv("ALSA_CARD", None)        # ej. "2" para hw:2,0

# Palabras que terminan la sesión (Vosk translitera, así que incluimos variantes)
PALABRAS_SALIDA = {"salir", "adios", "adiós", "chao", "chau", "terminar", "finalizar", "bye"}

# ─────────────────────────────────────────────────────────────
# Suprimir mensajes ALSA/Jack que van a stderr (ruido en consola)
# ─────────────────────────────────────────────────────────────
import ctypes
try:
    ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int,
                                          ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)
    def _alsa_error_handler(filename, line, function, err, fmt):
        pass  # Silenciar todos los mensajes de error de ALSA
    c_error_handler = ERROR_HANDLER_FUNC(_alsa_error_handler)
    asound = ctypes.cdll.LoadLibrary("libasound.so.2")
    asound.snd_lib_error_set_handler(c_error_handler)
except Exception:
    pass  # Si no está disponible la librería, continuar sin suprimir

# ─────────────────────────────────────────────────────────────
# Cargar el modelo de reconocimiento de voz (Vosk)
# ─────────────────────────────────────────────────────────────
print("Cargando modelo de escucha Vosk...")
modelo_escucha = Model("modelo_vosk")


def _encontrar_dispositivo_entrada():
    """
    Detecta automáticamente el índice del primer dispositivo de entrada disponible.
    Prioriza dispositivos USB (más comunes en Raspberry Pi con micrófono externo).
    Si ALSA_CARD está definido, usa ese índice directamente.
    """
    if ALSA_CARD is not None:
        try:
            idx = int(ALSA_CARD)
            print(f"🎙️  Usando dispositivo de audio forzado por ALSA_CARD: índice {idx}")
            return idx
        except ValueError:
            print(f"⚠️  ALSA_CARD='{ALSA_CARD}' no es un número válido, usando detección automática.")

    p = pyaudio.PyAudio()
    device_count = p.get_device_count()
    usb_idx = None
    first_input_idx = None

    for i in range(device_count):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            nombre = info["name"].lower()
            if first_input_idx is None:
                first_input_idx = i
            # Priorizar USB porque en Raspi el USB mic suele ser el deseado
            if "usb" in nombre or "device" in nombre:
                usb_idx = i
                break

    p.terminate()

    elegido = usb_idx if usb_idx is not None else first_input_idx
    if elegido is not None:
        print(f"🎙️  Dispositivo de entrada detectado automáticamente: índice {elegido}")
    else:
        print("❌ No se encontró ningún dispositivo de entrada de audio.")
    return elegido


def escuchar_cliente():
    """Captura audio del micrófono y lo convierte a texto de forma offline con Vosk."""
    reconocedor = KaldiRecognizer(modelo_escucha, 16000)
    microfono = pyaudio.PyAudio()

    device_index = _encontrar_dispositivo_entrada()
    if device_index is None:
        microfono.terminate()
        return ""

    try:
        stream = microfono.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            input_device_index=device_index,   # ← CRÍTICO: especificar el dispositivo
            frames_per_buffer=8192
        )
    except OSError as e:
        print(f"❌ No se pudo abrir el micrófono (device {device_index}): {e}")
        microfono.terminate()
        return ""

    print("\n🎤 Escuchando... (Habla ahora)")
    stream.start_stream()

    texto_capturado = ""
    try:
        while True:
            data = stream.read(4000, exception_on_overflow=False)
            if reconocedor.AcceptWaveform(data):
                resultado = json.loads(reconocedor.Result())
                texto_capturado = resultado.get("text", "")
                if texto_capturado:
                    print(f"✅ Cliente dijo: {texto_capturado}")
                    break
            else:
                parcial = json.loads(reconocedor.PartialResult())
                if parcial.get("partial"):
                    print(f"Leyendo...: {parcial.get('partial')}", end="\r")
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        microfono.terminate()

    return texto_capturado


def hablar(texto):
    """Convierte texto en voz con Piper y lo reproduce con aplay."""
    print(f"🤖 Agente dice: {texto}")
    clean_text = texto.replace('"', "").replace("#", "")
    cmd = f'echo "{clean_text}" | {PIPER_BIN} --model {VOZ_MODELO} --output_file salida.wav'

    # Redirigir stderr a /dev/null para suprimir mensajes de Piper y aplay
    subprocess.run(cmd, shell=True, check=True, stderr=subprocess.DEVNULL)
    subprocess.run("aplay -q salida.wav", shell=True, stderr=subprocess.DEVNULL)


def decodificar_y_vender(texto_cliente, catalogo_sabores):
    """Usa Ollama para extraer el pedido y lo registra mediante la API."""
    mensaje_sistema = f"""
    Eres un extractor de datos de una heladería.
    Tu único objetivo es extraer el sabor y la cantidad del pedido basándote en este catálogo:
    {catalogo_sabores}

    Responde ÚNICAMENTE con un JSON válido con esta estructura exacta: {{"idSabor": ID_NUMERICO, "cantidad": CANTIDAD_NUMERICA}}
    Si no logras identificar el pedido, responde: {{"error": "No entendí"}}
    """

    print("🧠 Ollama está procesando tu pedido...")
    respuesta_ia = ollama.chat(
        model=MODELO,
        messages=[
            {"role": "system", "content": mensaje_sistema},
            {"role": "user",   "content": texto_cliente}
        ],
        format="json"
    )

    texto_json = respuesta_ia["message"]["content"]
    print(f"🔍 DEBUG IA: {texto_json}")

    try:
        datos_pedido = json.loads(texto_json)
    except json.JSONDecodeError:
        return "Hubo un problema interno procesando tu pedido, por favor intenta de nuevo."

    if "error" in datos_pedido:
        return "Lo siento, no logré entender qué sabor o cuántos quieres. ¿Puedes repetirlo?"

    payload_api = {
        "items": [{
            "idSabor": datos_pedido.get("idSabor"),
            "cantidad": datos_pedido.get("cantidad")
        }]
    }

    respuesta_api = requests.post(f"{API_URL}/ventas", json=payload_api)

    if respuesta_api.status_code == 200:
        return "¡Excelente elección! Tu pedido ha sido procesado y descontado del inventario."
    elif respuesta_api.status_code == 400:
        detalle = respuesta_api.json().get("detail", "No se pudo realizar la venta.")
        return f"Hubo un problema con tu pedido. {detalle}. ¿Te gustaría probar otro sabor?"
    else:
        print(f"DEBUG API ERROR: {respuesta_api.status_code} - {respuesta_api.text}")
        return "Hubo un error interno en el sistema al intentar procesar la venta."


# ─────────────────────────────────────────────────────────────
# BUCLE PRINCIPAL
# ─────────────────────────────────────────────────────────────
def iniciar_agente():
    print("Conectando con la base de datos de la heladería...")
    try:
        respuesta = requests.get(f"{API_URL}/inventario", timeout=5)
        if respuesta.status_code == 200:
            lista_sabores = respuesta.json()
            catalogo_sabores = ", ".join(
                [f'ID {s["id"]}: {s["nombre"]} (Stock: {s["stock"]})' for s in lista_sabores]
            )
            print("\n" + "="*40)
            print("🍦 MENÚ DISPONIBLE EN LA HELADERÍA 🍦")
            for s in lista_sabores:
                print(f"   👉 {s['nombre']} | Stock: {s['stock']}")
            print("="*40)
        else:
            catalogo_sabores = "Error al obtener catálogo."
            print("⚠️  No se pudo cargar el menú correctamente.")
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se pudo conectar a la API. ¿Está Uvicorn encendido?")
        return

    hablar("Hola, bienvenido. ¿Qué helado te gustaría llevar hoy?")

    while True:
        usuario_input = escuchar_cliente()

        # Verificar palabras de salida antes de llamar a Ollama
        palabras = set(usuario_input.lower().split())
        if palabras & PALABRAS_SALIDA:
            hablar("Hasta luego. Vuelve pronto.")
            break

        if usuario_input.strip():
            respuesta_final = decodificar_y_vender(usuario_input, catalogo_sabores)
            hablar(respuesta_final)


if __name__ == "__main__":
    iniciar_agente()