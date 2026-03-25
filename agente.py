# agente.py
from base_datos import (
    registrar_perro, obtener_perro, obtener_todos_perros,
    registrar_padrino, obtener_padrino, actualizar_comida
)
from verificador import verificar_foto_tiene_perro
from blockchain import registrar_evento_en_blockchain

# ── CONFIGURACIÓN DEL AGENTE ──────────────────────────────────────
COSTO_COMIDA_SYS = 0.5        # Costo por registrar una comida
LIMITE_COMIDAS_DIARIAS = 3    # Máximo de comidas por perro por día
THRESHOLD_LIBERACION = 5.0    # SYS acumulados para liberar fondos
SALDO_INICIAL_PADRINO = 10.0  # SYS de prueba al registrarse
# ──────────────────────────────────────────────────────────────────

class AgenteRescuePaw:
    """
    El agente autónomo de RescuePaw.
    Supervisa todas las reglas sin intervención humana.
    """
    
    def registrar_nuevo_padrino(self, user_id, nombre):
        """
        PASO 1 del flujo: Un estudiante se registra como padrino.
        Recibe 10 SYS de prueba automáticamente.
        """
        exito = registrar_padrino(user_id, nombre)
        
        if not exito:
            return {
                "exito": False,
                "mensaje": f"⚠️ Ya estás registrado como padrino, {nombre}."
            }
        
        # Registrar en blockchain
        tx_hash = registrar_evento_en_blockchain(
            dog_id="sistema",
            user_id=str(user_id),
            tipo_evento="NUEVO_PADRINO",
            descripcion=f"Padrino registrado: {nombre}"
        )
        
        return {
            "exito": True,
            "mensaje": (
                f"🐾 ¡Bienvenido, {nombre}!\n"
                f"✅ Eres oficialmente padrino de RescuePaw.\n"
                f"💰 Saldo inicial: {SALDO_INICIAL_PADRINO} SYS (testnet)\n"
                f"🔗 Registrado en blockchain: `{tx_hash[:20]}...`\n\n"
                f"Usa `/alimentar <dog_id>` para ayudar a un perro."
            ),
            "tx_hash": tx_hash
        }
    
    def registrar_nuevo_perro(self, nombre, ubicacion, foto_url, registrado_por):
        """
        Registra un perro callejero en el sistema.
        El agente verifica que la foto realmente contenga un perro.
        """
        # COMPLIANCE 1: Verificar que la foto tiene un perro
        hay_perro, descripcion_ia = verificar_foto_tiene_perro(foto_url)
        
        if not hay_perro:
            return {
                "exito": False,
                "mensaje": (
                    f"❌ **Registro rechazado por el agente.**\n"
                    f"La IA no detectó un perro en la foto.\n"
                    f"Descripción: {descripcion_ia}\n"
                    f"Por favor sube una foto clara del perro."
                )
            }
        
        # Registrar el perro
        dog_id = registrar_perro(nombre, ubicacion, foto_url)
        
        # Registrar en blockchain
        tx_hash = registrar_evento_en_blockchain(
            dog_id=dog_id,
            user_id=str(registrado_por),
            tipo_evento="REGISTRO_PERRO",
            descripcion=f"Perro registrado: {nombre} en {ubicacion}"
        )
        
        return {
            "exito": True,
            "mensaje": (
                f"🐕 **¡Perro registrado exitosamente!**\n"
                f"📛 Nombre: **{nombre}**\n"
                f"📍 Ubicación: {ubicacion}\n"
                f"🆔 ID del perro: `{dog_id}`\n"
                f"🤖 IA confirmó: {descripcion_ia}\n"
                f"🔗 En blockchain: `{tx_hash[:20]}...`\n\n"
                f"Los padrinos pueden usar `/alimentar {dog_id}`"
            ),
            "dog_id": dog_id,
            "tx_hash": tx_hash
        }
    
    def procesar_alimentacion(self, dog_id, user_id, foto_url):
        """
        FLUJO PRINCIPAL: Un padrino reporta que alimentó a un perro.
        El agente ejecuta todos los checks de compliance automáticamente.
        """
        
        # ── COMPLIANCE 1: ¿El padrino existe? ────────────────────
        padrino = obtener_padrino(user_id)
        if not padrino:
            return {
                "exito": False,
                "razon": "padrino_no_registrado",
                "mensaje": (
                    "❌ **Acción rechazada.**\n"
                    "No estás registrado como padrino.\n"
                    "Usa `/registrar` primero."
                )
            }
        
        # ── COMPLIANCE 2: ¿El perro existe? ──────────────────────
        perro = obtener_perro(dog_id)
        if not perro:
            return {
                "exito": False,
                "razon": "perro_no_encontrado",
                "mensaje": (
                    f"❌ **Acción rechazada.**\n"
                    f"No existe un perro con ID `{dog_id}`.\n"
                    f"Usa `/perros` para ver la lista."
                )
            }
        
        # ── COMPLIANCE 3: ¿El padrino tiene saldo? ───────────────
        if padrino["saldo_sys"] < COSTO_COMIDA_SYS:
            return {
                "exito": False,
                "razon": "saldo_insuficiente",
                "mensaje": (
                    f"❌ **Acción rechazada.**\n"
                    f"Saldo insuficiente: {padrino['saldo_sys']} SYS\n"
                    f"Necesitas: {COSTO_COMIDA_SYS} SYS por comida."
                )
            }
        
        # ── COMPLIANCE 4: ¿El perro ya comió demasiado hoy? ──────
        if perro["comidas_hoy"] >= LIMITE_COMIDAS_DIARIAS:
            return {
                "exito": False,
                "razon": "limite_diario_alcanzado",
                "mensaje": (
                    f"❌ **Acción rechazada.**\n"
                    f"**{perro['nombre']}** ya alcanzó el límite diario "
                    f"({LIMITE_COMIDAS_DIARIAS} comidas).\n"
                    f"Vuelve mañana. 🌙"
                )
            }
        
        # ── COMPLIANCE 5: ¿La foto tiene un perro? ───────────────
        if foto_url:
            hay_perro, descripcion_ia = verificar_foto_tiene_perro(foto_url)
            if not hay_perro:
                return {
                    "exito": False,
                    "razon": "foto_invalida",
                    "mensaje": (
                        f"❌ **Acción rechazada.**\n"
                        f"La IA no detectó un perro en tu foto.\n"
                        f"Descripción: {descripcion_ia}\n"
                        f"Sube una foto clara del perro comiendo."
                    )
                }
        
        # ── TODOS LOS CHECKS PASARON → EJECUTAR ──────────────────
        actualizar_comida(dog_id, user_id, COSTO_COMIDA_SYS)
        perro_actualizado = obtener_perro(dog_id)
        padrino_actualizado = obtener_padrino(user_id)
        
        # Registrar en blockchain
        tx_hash = registrar_evento_en_blockchain(
            dog_id=dog_id,
            user_id=str(user_id),
            tipo_evento="ALIMENTACION",
            descripcion=f"Comida registrada para {perro['nombre']}"
        )
        
        # ── VERIFICAR SI SE ALCANZÓ EL THRESHOLD ─────────────────
        mensaje_threshold = ""
        if perro_actualizado["fondos_acumulados"] >= THRESHOLD_LIBERACION:
            mensaje_threshold = (
                f"\n\n🎉 **¡THRESHOLD ALCANZADO!**\n"
                f"**{perro['nombre']}** acumuló {perro_actualizado['fondos_acumulados']} SYS.\n"
                f"💸 El agente libera los fondos automáticamente.\n"
                f"🛒 Una tienda recibirá el pago para entregar comida."
            )
            # Aquí iría la lógica real de liberación del escrow
        
        return {
            "exito": True,
            "mensaje": (
                f"✅ **¡Comida registrada por el agente!**\n\n"
                f"🐕 Perro: **{perro['nombre']}**\n"
                f"🍖 Comidas hoy: {perro_actualizado['comidas_hoy']}/{LIMITE_COMIDAS_DIARIAS}\n"
                f"💰 Fondos acumulados: {perro_actualizado['fondos_acumulados']} SYS\n"
                f"👤 Tu saldo: {padrino_actualizado['saldo_sys']} SYS\n"
                f"🔗 En blockchain: `{tx_hash[:20]}...`"
                f"{mensaje_threshold}"
            ),
            "tx_hash": tx_hash
        }
    
    def ver_estado_perro(self, dog_id):
        """Muestra el estado actual de un perro."""
        perro = obtener_perro(dog_id)
        
        if not perro:
            return f"❌ No existe un perro con ID `{dog_id}`."
        
        porcentaje = (perro["fondos_acumulados"] / THRESHOLD_LIBERACION) * 100
        barra = self._barra_progreso(porcentaje)
        
        return (
            f"🐕 **{perro['nombre']}**\n"
            f"📍 Ubicación: {perro['ubicacion']}\n"
            f"🍖 Comidas hoy: {perro['comidas_hoy']}/{LIMITE_COMIDAS_DIARIAS}\n"
            f"🍽️ Total comidas: {perro['total_comidas']}\n"
            f"💰 Fondos: {perro['fondos_acumulados']:.1f}/{THRESHOLD_LIBERACION} SYS\n"
            f"{barra} {porcentaje:.0f}%"
        )
    
    def ver_todos_perros(self):
        """Lista todos los perros registrados."""
        perros = obtener_todos_perros()
        
        if not perros:
            return "🐾 No hay perros registrados aún. Sé el primero en registrar uno con `/registrar_perro`"
        
        mensaje = "🐕 **Perros registrados en RescuePaw:**\n\n"
        for dog_id, perro in perros.items():
            mensaje += f"• `{dog_id}` — **{perro['nombre']}** ({perro['ubicacion']}) — {perro['fondos_acumulados']:.1f} SYS\n"
        
        return mensaje
    
    def _barra_progreso(self, porcentaje):
        """Genera una barra de progreso visual."""
        llenos = int(porcentaje / 10)
        vacios = 10 - llenos
        return "▓" * llenos + "░" * vacios