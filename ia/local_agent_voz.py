import ollama
import requests
import json
import subprocess

API_URL = "http://127.0.0.1:8000"
MODELO = "llama3.2"
PIPER_BIN = "./piper/piper"
VOZ_MODELO = "voz_es.onnx"

def hablar(texto):
    print(f"Diciendo: {texto}")
    try:
        # Limpiar texto de caracteres especiales que usa el modelo de IA
        clean_text = texto.replace("*", "").replace("#", "")
        
        # Comando para generar audio con Piper
        # Usamos comillas rectas y nos aseguramos de que el comando sea válido
        cmd = f'echo "{clean_text}" | {PIPER_BIN} --model {VOZ_MODELO} --output_file salida.wav'
        
        subprocess.run(cmd, shell=True, check=True)
        # Reproducir el archivo generado
        subprocess.run("aplay -q salida.wav", shell=True)
        
    except Exception as e:
        print(f"Error en hablar: {e}")

if __name__ == "__main__":
    # Prueba básica
    hablar("Hola, el sistema de voz está activo.")
