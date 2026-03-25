# base_datos.py
import json
import os

ARCHIVO = "datos_rescuepaw.json"

def cargar():
    """Carga los datos guardados."""
    if not os.path.exists(ARCHIVO):
        return {"perros": {}, "padrinos": {}}
    with open(ARCHIVO, "r") as f:
        return json.load(f)

def guardar(datos):
    """Guarda los datos en el archivo."""
    with open(ARCHIVO, "w") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

def registrar_perro(nombre, ubicacion, foto_url):
    """Registra un nuevo perro en el sistema."""
    datos = cargar()
    dog_id = f"dog_{len(datos['perros']) + 1:03d}"
    
    datos["perros"][dog_id] = {
        "nombre": nombre,
        "ubicacion": ubicacion,
        "foto_url": foto_url,
        "fondos_acumulados": 0.0,
        "comidas_hoy": 0,
        "total_comidas": 0,
        "registrado": True
    }
    guardar(datos)
    return dog_id

def obtener_perro(dog_id):
    """Obtiene los datos de un perro."""
    datos = cargar()
    return datos["perros"].get(dog_id, None)

def obtener_todos_perros():
    """Devuelve todos los perros registrados."""
    datos = cargar()
    return datos["perros"]

def registrar_padrino(user_id, nombre):
    """Registra un nuevo padrino (estudiante)."""
    datos = cargar()
    if str(user_id) not in datos["padrinos"]:
        datos["padrinos"][str(user_id)] = {
            "nombre": nombre,
            "saldo_sys": 10.0,  # 10 SYS de prueba al registrarse
            "comidas_aportadas": 0
        }
        guardar(datos)
        return True
    return False  # Ya existía

def obtener_padrino(user_id):
    """Obtiene los datos de un padrino."""
    datos = cargar()
    return datos["padrinos"].get(str(user_id), None)

def actualizar_comida(dog_id, user_id, costo_sys=0.5):
    """Registra una comida: descuenta del padrino y suma al perro."""
    datos = cargar()
    
    # Actualizar padrino
    datos["padrinos"][str(user_id)]["saldo_sys"] -= costo_sys
    datos["padrinos"][str(user_id)]["comidas_aportadas"] += 1
    
    # Actualizar perro
    datos["perros"][dog_id]["fondos_acumulados"] += costo_sys
    datos["perros"][dog_id]["comidas_hoy"] += 1
    datos["perros"][dog_id]["total_comidas"] += 1
    
    guardar(datos)

def resetear_comidas_diarias():
    """Resetea el contador diario de comidas (llamar cada 24h)."""
    datos = cargar()
    for dog_id in datos["perros"]:
        datos["perros"][dog_id]["comidas_hoy"] = 0
    guardar(datos)