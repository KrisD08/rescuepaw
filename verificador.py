# verificador.py
import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

def imagen_a_base64(ruta_imagen):
    """Convierte una imagen a base64."""
    with open(ruta_imagen, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def verificar_foto_tiene_perro(url_foto):
    """
    Usa IA para verificar si la foto tiene un perro.
    Devuelve True si hay perro, False si no.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    # Si no hay API key configurada, modo simulación (para desarrollo)
    if not api_key or api_key == "aqui_va_tu_api_key":
        print("[SIMULACIÓN] Verificando foto... resultado: PERRO DETECTADO")
        return True, "Simulación: perro detectado correctamente."
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "google/gemini-2.0-flash-lite-preview-02-05:free",  # Modelo gratuito en OpenRouter
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analiza esta imagen. ¿Contiene un perro? Responde SOLO con: SI_HAY_PERRO o NO_HAY_PERRO, seguido de una coma y una descripción breve de máximo 10 palabras."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": url_foto}
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        resultado = response.json()["choices"][0]["message"]["content"]
        hay_perro = resultado.startswith("SI_HAY_PERRO")
        descripcion = resultado.split(",", 1)[-1].strip() if "," in resultado else resultado
        return hay_perro, descripcion
    except Exception as e:
        print(f"[ERROR verificador] {e}")
        return False, "Error al verificar la imagen."