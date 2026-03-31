import requests
from base_datos import (
    registrar_perro, obtener_perro, obtener_todos_perros,
    registrar_padrino, obtener_padrino, actualizar_comida
)
from verificador import verificar_foto_tiene_perro
from blockchain import registrar_evento_en_blockchain

# ── CONFIG ─────────────────────────────────
COSTO_COMIDA_SYS = 0.5
LIMITE_COMIDAS_DIARIAS = 3
THRESHOLD_LIBERACION = 5.0
SALDO_INICIAL_PADRINO = 10.0

imagenes_usadas = set()

# ── FUNCIÓN NUEVA ──────────────────────────
def obtener_imagen_perro():
    while True:
        res = requests.get("https://dog.ceo/api/breeds/image/random")
        url = res.json()["message"]

        if url not in imagenes_usadas:
            imagenes_usadas.add(url)
            return url

# ───────────────────────────────────────────

class AgenteRescuePaw:

    def registrar_nuevo_padrino(self, user_id, nombre):
        exito = registrar_padrino(user_id, nombre)

        if not exito:
            return {
                "exito": False,
                "mensaje": f"⚠️ Ya estás registrado como padrino, {nombre}."
            }

        tx_hash = registrar_evento_en_blockchain(
            dog_id="sistema",
            user_id=str(user_id),
            tipo_evento="NUEVO_PADRINO",
            descripcion=f"Padrino: {nombre}"
        )

        return {
            "exito": True,
            "mensaje": f"🐾 Bienvenido {nombre}\n💰 {SALDO_INICIAL_PADRINO} SYS\n🔗 {tx_hash[:20]}..."
        }

    # 🔥 CAMBIO AQUÍ
    def registrar_nuevo_perro(self, nombre, ubicacion, registrado_por):

        foto_url = obtener_imagen_perro()

        # Validación IA (opcional pero mantenida)
        hay_perro, descripcion = verificar_foto_tiene_perro(foto_url)

        if not hay_perro:
            return {
                "exito": False,
                "mensaje": "❌ Error IA detectando perro"
            }

        dog_id = registrar_perro(nombre, ubicacion, foto_url)

        tx_hash = registrar_evento_en_blockchain(
            dog_id=dog_id,
            user_id=str(registrado_por),
            tipo_evento="REGISTRO_PERRO",
            descripcion=f"{nombre} en {ubicacion}"
        )

        return {
            "exito": True,
            "mensaje": f"🐕 {nombre} registrado en {ubicacion}\n🆔 {dog_id}",
            "foto_url": foto_url
        }

    def procesar_alimentacion(self, dog_id, user_id, foto_url):

        padrino = obtener_padrino(user_id)
        if not padrino:
            return {"exito": False, "mensaje": "❌ Regístrate primero"}

        perro = obtener_perro(dog_id)
        if not perro:
            return {"exito": False, "mensaje": "❌ Perro no existe"}

        if padrino["saldo_sys"] < COSTO_COMIDA_SYS:
            return {"exito": False, "mensaje": "❌ Sin saldo"}

        actualizar_comida(dog_id, user_id, COSTO_COMIDA_SYS)

        return {
            "exito": True,
            "mensaje": f"🍖 Alimentaste a {perro['nombre']}"
        }

    def ver_estado_perro(self, dog_id):
        perro = obtener_perro(dog_id)
        if not perro:
            return "❌ No existe"

        return f"{perro['nombre']} - {perro['fondos_acumulados']} SYS"

    def ver_todos_perros(self):
        perros = obtener_todos_perros()
        if not perros:
            return "🐾 No hay perros"

        msg = ""
        for dog_id, p in perros.items():
            msg += f"{dog_id} - {p['nombre']}\n"
        return msg