import ollama
import requests
import json
import subprocess

# --- CONFIGURACIÓN ---
API_URL = "http://127.0.0.1:8000"
MODELO = "llama3.2"
PIPER_BIN = "./piper/piper" # Asegúrate de que esta ruta sea correcta
VOZ_MODELO = "voz_es.onnx"

def hablar(texto):
    """Convierte el texto en voz usando Piper y lo reproduce."""
    print(f"\n🤖 Agente dice: {texto}")
    clean_text = texto.replace('"', '').replace('#', '')
    cmd = f'echo "{clean_text}" | {PIPER_BIN} --model {VOZ_MODELO} --output_file salida.wav'
    subprocess.run(cmd, shell=True, check=True)
    subprocess.run("aplay -q salida.wav", shell=True)

def decodificar_y_vender(texto_cliente, catalogo_sabores):
    """Convierte el texto del cliente a JSON usando Ollama y valida con FastAPI."""
    mensaje_sistema = f"""
    Eres un extractor de datos de una heladería. 
    Tu único objetivo es extraer el sabor y la cantidad del pedido basándote en este catálogo: 
    {catalogo_sabores}
    
    Responde ÚNICAMENTE con un JSON válido con esta estructura exacta: {{"idSabor": ID_NUMERICO, "cantidad": CANTIDAD_NUMERICA}}
    Si no logras identificar el pedido, responde: {{"error": "No entendí"}}
    """

    print("🧠 Ollama está procesando tu pedido...")
    
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
    print(f"🔍 DEBUG IA (Lo que entendió Ollama): {texto_json}")

    try:
        datos_pedido = json.loads(texto_json)

        if "error" in datos_pedido:
            return "Lo siento, no logré entender qué sabor o cuántos quieres. ¿Puedes repetirlo?"

        # 1. Adaptamos el JSON al modelo Pydantic 'Venta' de FastAPI
        payload_api = {
            "items": [
                {
                    "idSabor": datos_pedido.get("idSabor"),
                    "cantidad": datos_pedido.get("cantidad")
                }
            ]
        }

        # 2. Hacemos la petición a la API
        respuesta_api = requests.post(f"{API_URL}/ventas", json=payload_api)

        # 3. Evaluamos la respuesta de la API
        if respuesta_api.status_code == 200:
            return "¡Excelente elección! Tu pedido ha sido procesado y descontado del inventario."
        elif respuesta_api.status_code == 400:
            detalle_error = respuesta_api.json().get("detail", "No se pudo realizar la venta.")
            return f"Hubo un problema con tu pedido. {detalle_error}. ¿Te gustaría probar otro sabor?"
        else:
            return "Hubo un error interno en el sistema al intentar procesar la venta."

    except json.JSONDecodeError:
        return "Hubo un problema interno procesando tu pedido, por favor intenta de nuevo."

# --- BUCLE PRINCIPAL ---
def iniciar_agente():
    print("Conectando con la base de datos de la heladería...")
    try:
        respuesta_catalogo = requests.get(f"{API_URL}/inventario")
        if respuesta_catalogo.status_code == 200:
            lista_sabores = respuesta_catalogo.json()
            catalogo_sabores = ", ".join([f'ID {s["id"]}: {s["nombre"]} (Stock: {s["stock"]})' for s in lista_sabores])
            
            # --- MOSTRAR MENÚ POR CONSOLA ---
            print("\n" + "="*40)
            print("🍦 MENÚ DISPONIBLE EN LA HELADERÍA 🍦")
            for s in lista_sabores:
                print(f"   👉 {s['nombre']} | Disponibles: {s['stock']}")
            print("="*40)
            
        else:
            catalogo_sabores = "Error al obtener catálogo."
            print("⚠️ No se pudo cargar el menú correctamente.")
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se pudo conectar a la API. ¿Está Uvicorn encendido?")
        return

    hablar("Hola, bienvenido. ¿Qué helado te gustaría llevar hoy?")
    
    while True:
        # --- ENTRADA DE TEXTO ---
        print("\n💡 Ejemplo: 'quiero 10 helados de fresa' o 'dame 2 de vainilla'")
        usuario_input = input("🗣️ Escribe tu pedido (o 'salir' para terminar): ")
        
        if "salir" in usuario_input.lower() or "adiós" in usuario_input.lower():
            hablar("Hasta luego. Vuelve pronto.")
            break
            
        if usuario_input.strip(): 
            respuesta_final = decodificar_y_vender(usuario_input, catalogo_sabores)
            hablar(respuesta_final)

if __name__ == "__main__":
    iniciar_agente()