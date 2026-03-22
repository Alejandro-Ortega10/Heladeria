import ollama
import requests
import json
import subprocess
import pyaudio
from vosk import Model, KaldiRecognizer

# --- CONFIGURACIÓN ---
API_URL = "http://127.0.0.1:8000"
MODELO = "llama3.2"
PIPER_BIN = "./piper/piper" # Ajusta según tu ruta de Piper
VOZ_MODELO = "voz_es.onnx"

# Cargar el modelo de Vosk
print("Cargando modelo de escucha Vosk...")
modelo_escucha = Model("modelo_vosk")

def escuchar_cliente():
    """Captura el audio del micrófono y lo convierte a texto de forma offline."""
    reconocedor = KaldiRecognizer(modelo_escucha, 16000)
    microfono = pyaudio.PyAudio()
    
    stream = microfono.open(format=pyaudio.paInt16, channels=1, 
                            rate=16000, input=True, frames_per_buffer=8192)
    
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
                # Opcional: Imprimir lo que va entendiendo en tiempo real
                parcial = json.loads(reconocedor.PartialResult())
                if parcial.get("partial"):
                    print(f"Reading...: {parcial.get('partial')}", end="\r")
                    
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        microfono.terminate()
        
    return texto_capturado

def hablar(texto):
    print(f"🤖 Agente dice: {texto}")
    clean_text = texto.replace('"', '').replace('#', '')
    cmd = f'echo "{clean_text}" | {PIPER_BIN} --model {VOZ_MODELO} --output_file salida.wav'
    subprocess.run(cmd, shell=True, check=True)
    subprocess.run("aplay -q salida.wav", shell=True)

def decodificar_y_vender(texto_cliente, catalogo_sabores):
    """Convierte la voz a JSON usando Ollama y valida con FastAPI."""
    mensaje_sistema = f"""
    Eres un extractor de datos de una heladería. 
    Tu único objetivo es extraer el sabor y la cantidad del pedido basándote en este catálogo: 
    {catalogo_sabores}
    
    Responde ÚNICAMENTE con un JSON válido con esta estructura exacta: {{"idSabor": ID_NUMERICO, "cantidad": CANTIDAD_NUMERICA}}
    Si no logras identificar el pedido, responde: {{"error": "No entendí"}}
    """

    # Forzamos a Llama 3.2 a devolver formato JSON
    respuesta_ia = ollama.chat(
        model=MODELO, 
        messages=[
            {'role': 'system', 'content': mensaje_sistema},
            {'role': 'user', 'content': texto_cliente}
        ],
        format="json"
    )

    texto_json = respuesta_ia['message']['content']
    print(f"DEBUG IA: {texto_json}") # Para ver qué generó Ollama

    try:
        datos_pedido = json.loads(texto_json)

        if "error" in datos_pedido:
            return "Lo siento, no logré entender qué sabor o cuántos quieres. ¿Puedes repetirlo?"

        # 1. Adaptamos el JSON al modelo Pydantic 'Venta' de tu FastAPI
        payload_api = {
            "items": [
                {
                    "idSabor": datos_pedido.get("idSabor"),
                    "cantidad": datos_pedido.get("cantidad")
                }
            ]
        }

        # 2. Hacemos la petición a la ruta CORRECTA (/ventas)
        respuesta_api = requests.post(f"{API_URL}/ventas", json=payload_api)

        # 3. Evaluamos la respuesta de la API
        if respuesta_api.status_code == 200:
            return "¡Excelente elección! Tu pedido ha sido procesado y descontado del inventario."
        elif respuesta_api.status_code == 400:
            detalle_error = respuesta_api.json().get("detail", "No se pudo realizar la venta.")
            return f"Hubo un problema con tu pedido. {detalle_error}. ¿Te gustaría probar otro sabor?"
        else:
            print(f"DEBUG API ERROR: {respuesta_api.status_code} - {respuesta_api.text}")
            return "Hubo un error interno en el sistema al intentar procesar la venta."

    except json.JSONDecodeError:
        return "Hubo un problema interno procesando tu pedido, por favor intenta de nuevo."

# --- BUCLE PRINCIPAL ---
def iniciar_agente():
    # 1. Obtenemos el catálogo real desde la ruta correcta (/inventario)
    print("Conectando con la base de datos de la heladería...")
    try:
        respuesta_catalogo = requests.get(f"{API_URL}/inventario")
        if respuesta_catalogo.status_code == 200:
            lista_sabores = respuesta_catalogo.json()
            # Formateamos el catálogo para que la IA lo entienda fácil
            catalogo_sabores = ", ".join([f'ID {s["id"]}: {s["nombre"]} (Stock: {s["stock"]})' for s in lista_sabores])
        else:
            catalogo_sabores = "Error al obtener catálogo."
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se pudo conectar a la API. ¿Está Uvicorn encendido?")
        return

    print(f"Catálogo cargado: {catalogo_sabores}")
    hablar("Hola, bienvenido. ¿Qué helado te gustaría llevar hoy?")
    
    while True:
        usuario_input = escuchar_cliente()
        
        if "salir" in usuario_input.lower() or "adiós" in usuario_input.lower():
            hablar("Hasta luego. Vuelve pronto.")
            break
            
        if usuario_input: 
            respuesta_final = decodificar_y_vender(usuario_input, catalogo_sabores)
            hablar(respuesta_final)

if __name__ == "__main__":
    iniciar_agente()