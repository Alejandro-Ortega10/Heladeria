import ollama
import requests
import json
import subprocess
import pyaudio
from vosk import Model, KaldiRecognizer

# --- CONFIGURACIÓN ---
API_URL = "http://127.0.0.1:8000"
MODELO = "llama3.2"
PIPER_BIN = "./piper/piper"
VOZ_MODELO = "voz_es.onnx"

# Cargar el modelo de Vosk (Asegúrate de que la carpeta se llame así)
modelo_escucha = Model("modelo_vosk")

def escuchar_cliente():
    """Captura el audio del micrófono y lo convierte a texto de forma offline."""
    reconocedor = KaldiRecognizer(modelo_escucha, 16000)
    microfono = pyaudio.PyAudio()
    
    stream = microfono.open(format=pyaudio.paInt16, channels=1, 
                            rate=16000, input=True, frames_per_buffer=8192)
    
    print("🎤 Escuchando... (Habla ahora)")
    stream.start_stream()

    texto_capturado = ""
    try:
        while True:
            data = stream.read(4096, exception_on_overflow=False)
            if reconocedor.AcceptWaveform(data):
                resultado = json.loads(reconocedor.Result())
                texto_capturado = resultado.get("text", "")
                if texto_capturado:
                    print(f"Cliente dijo: {texto_capturado}")
                    break
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        microfono.terminate()
        
    return texto_capturado

def hablar(texto):
    # (Tu función hablar que ya configuramos y funciona)
    clean_text = texto.replace('"', '').replace('#', '')
    cmd = f'echo "{clean_text}" | {PIPER_BIN} --model {VOZ_MODELO} --output_file salida.wav'
    subprocess.run(cmd, shell=True, check=True)
    subprocess.run("aplay -q salida.wav", shell=True)

def decodificar_y_vender(texto_cliente, catalogo_sabores):
    """
    1. Convierte la voz a JSON usando Ollama.
    2. Valida la transacción con la API.
    """
    mensaje_sistema = f"""
    Eres el sistema interno de una heladería. 
    Tu único objetivo es extraer el sabor y la cantidad del pedido del cliente basándote en este catálogo: 
    {catalogo_sabores}
    
    Responde ÚNICAMENTE con un JSON válido con esta estructura exacta: {{"sabor_id": id_del_sabor, "cantidad": cantidad_solicitada}}
    Si no logras identificar el pedido, responde: {{"error": "No entendí"}}
    """

    # Pedimos a Ollama que decodifique
    respuesta_ia = ollama.chat(model=MODELO, messages=[
        {'role': 'system', 'content': mensaje_sistema},
        {'role': 'user', 'content': texto_cliente}
    ])

    texto_json = respuesta_ia['message']['content']

    try:
        # Transformamos el texto de Ollama a un diccionario de Python
        datos_pedido = json.loads(texto_json)

        if "error" in datos_pedido:
            return "Lo siento, no logré entender qué sabor o cuántos quieres. ¿Puedes repetirlo?"

        # 2. Hacemos la petición a FastAPI (Aquí se valida el stock y la integridad)
        respuesta_api = requests.post(f"{API_URL}/vender", json=datos_pedido)

        # 3. Evaluamos la respuesta de la API
        if respuesta_api.status_code == 200:
            return "¡Excelente elección! Tu pedido ha sido procesado y descontado del inventario."
        elif respuesta_api.status_code == 400:
            # Aquí capturamos el error de la API si no hay stock
            detalle_error = respuesta_api.json().get("detail", "No se pudo realizar la venta.")
            return f"Hubo un problema con tu pedido: {detalle_error}. ¿Te gustaría probar otro sabor?"
        else:
            return "Hubo un error interno en el sistema al intentar procesar la venta."

    except json.JSONDecodeError:
        return "Hubo un problema interno procesando tu pedido, por favor intenta de nuevo."

# --- BUCLE PRINCIPAL ---
def iniciar_agente():
    # Primero obtenemos el catálogo real desde tu API para que Ollama sepa los IDs
    respuesta_catalogo = requests.get(f"{API_URL}/sabores")
    catalogo_sabores = respuesta_catalogo.text if respuesta_catalogo.status_code == 200 else "1: Vainilla, 2: Chocolate"

    hablar("Hola, bienvenido. ¿Qué helado te gustaría llevar hoy?")
    
    while True:
        usuario_input = input("Cliente (Escribe tu pedido): ")
        if usuario_input.lower() == 'salir':
            hablar("Hasta luego.")
            break
            
        # Procesamos, vendemos y obtenemos la respuesta
        respuesta_final = decodificar_y_vender(usuario_input, catalogo_sabores)
        
        # El sistema habla el resultado
        hablar(respuesta_final)

if __name__ == "__main__":
    iniciar_agente()

def iniciar_agente():
    respuesta_catalogo = requests.get(f"{API_URL}/sabores")
    catalogo_sabores = respuesta_catalogo.text if respuesta_catalogo.status_code == 200 else "1: Vainilla, 2: Chocolate"

    hablar("Hola, bienvenido. ¿Qué helado te gustaría llevar hoy?")
    
    while True:
        # ¡Magia pura! Reemplazamos el input() por escuchar_cliente()
        usuario_input = escuchar_cliente()
        
        if "salir" in usuario_input.lower() or "adiós" in usuario_input.lower():
            hablar("Hasta luego.")
            break
            
        if usuario_input: # Solo procesamos si realmente escuchó algo
            respuesta_final = decodificar_y_vender(usuario_input, catalogo_sabores)
            hablar(respuesta_final)
