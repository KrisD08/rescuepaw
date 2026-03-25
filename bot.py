# bot.py
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from agente import AgenteRescuePaw

load_dotenv()

# ── CONFIGURACIÓN DEL BOT ─────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
agente = AgenteRescuePaw()
# ──────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"🐾 RescuePaw Bot conectado como {bot.user}")
    print(f"🤖 Agente autónomo activo en zkSYS Testnet")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="🐕 perros callejeros en Lima"
        )
    )

# ────────────────────────────────────────────────────────────────
# COMANDO: /registrar
# Un estudiante se registra como padrino
# ────────────────────────────────────────────────────────────────
@bot.command(name="registrar")
async def cmd_registrar(ctx):
    """Regístrate como padrino de RescuePaw."""
    resultado = agente.registrar_nuevo_padrino(
        user_id=ctx.author.id,
        nombre=ctx.author.display_name
    )
    
    embed = discord.Embed(
        title="🐾 RescuePaw — Registro de Padrino",
        description=resultado["mensaje"],
        color=0x8B4513 if resultado["exito"] else 0xFF0000
    )
    await ctx.send(embed=embed)

# ────────────────────────────────────────────────────────────────
# COMANDO: /registrar_perro <nombre> <ubicacion>
# Registra un perro (adjunta foto)
# ────────────────────────────────────────────────────────────────
@bot.command(name="registrar_perro")
async def cmd_registrar_perro(ctx, nombre: str, *, ubicacion: str):
    """
    Registra un perro callejero.
    Uso: /registrar_perro Manchita Los Olivos
    Adjunta una foto del perro al mensaje.
    """
    # Verificar si hay foto adjunta
    foto_url = None
    if ctx.message.attachments:
        foto_url = ctx.message.attachments[0].url
    
    if not foto_url:
        await ctx.send("❌ Por favor adjunta una foto del perro al mensaje.")
        return
    
    msg_espera = await ctx.send("🤖 El agente está analizando la foto...")
    
    resultado = agente.registrar_nuevo_perro(
        nombre=nombre,
        ubicacion=ubicacion,
        foto_url=foto_url,
        registrado_por=ctx.author.id
    )
    
    await msg_espera.delete()
    
    embed = discord.Embed(
        title="🐕 RescuePaw — Registro de Perro",
        description=resultado["mensaje"],
        color=0x8B4513 if resultado["exito"] else 0xFF0000
    )
    if foto_url and resultado["exito"]:
        embed.set_thumbnail(url=foto_url)
    
    await ctx.send(embed=embed)

# ────────────────────────────────────────────────────────────────
# COMANDO: /alimentar <dog_id>
# Un padrino reporta que alimentó a un perro
# ────────────────────────────────────────────────────────────────
@bot.command(name="alimentar")
async def cmd_alimentar(ctx, dog_id: str):
    """
    Reporta que alimentaste a un perro.
    Uso: /alimentar dog_001
    Adjunta una foto del momento (opcional pero recomendado).
    """
    foto_url = None
    if ctx.message.attachments:
        foto_url = ctx.message.attachments[0].url
    
    msg_espera = await ctx.send("🤖 El agente está verificando el compliance...")
    
    resultado = agente.procesar_alimentacion(
        dog_id=dog_id.lower(),
        user_id=ctx.author.id,
        foto_url=foto_url
    )
    
    await msg_espera.delete()
    
    color = 0x228B22 if resultado["exito"] else 0xFF0000
    embed = discord.Embed(
        title="🍖 RescuePaw — Registro de Comida",
        description=resultado["mensaje"],
        color=color
    )
    embed.set_footer(text="Agente autónomo RescuePaw | zkSYS Testnet")
    
    await ctx.send(embed=embed)

# ────────────────────────────────────────────────────────────────
# COMANDO: /estado <dog_id>
# Ver el estado de un perro
# ────────────────────────────────────────────────────────────────
@bot.command(name="estado")
async def cmd_estado(ctx, dog_id: str):
    """
    Ver el estado de un perro.
    Uso: /estado dog_001
    """
    mensaje = agente.ver_estado_perro(dog_id.lower())
    
    embed = discord.Embed(
        title="📊 RescuePaw — Estado del Perro",
        description=mensaje,
        color=0x8B4513
    )
    await ctx.send(embed=embed)

# ────────────────────────────────────────────────────────────────
# COMANDO: /perros
# Ver todos los perros registrados
# ────────────────────────────────────────────────────────────────
@bot.command(name="perros")
async def cmd_perros(ctx):
    """Lista todos los perros registrados."""
    mensaje = agente.ver_todos_perros()
    
    embed = discord.Embed(
        title="🐕 RescuePaw — Perros Registrados",
        description=mensaje,
        color=0x8B4513
    )
    embed.set_footer(text="Usa /alimentar <dog_id> para ayudar")
    await ctx.send(embed=embed)

# ────────────────────────────────────────────────────────────────
# COMANDO: /mi_perfil
# Ver tu saldo y estadísticas como padrino
# ────────────────────────────────────────────────────────────────
@bot.command(name="mi_perfil")
async def cmd_mi_perfil(ctx):
    """Ver tu perfil como padrino."""
    from base_datos import obtener_padrino
    padrino = obtener_padrino(ctx.author.id)
    
    if not padrino:
        await ctx.send("❌ No estás registrado. Usa `/registrar` primero.")
        return
    
    embed = discord.Embed(
        title=f"👤 Perfil de {padrino['nombre']}",
        color=0x8B4513
    )
    embed.add_field(name="💰 Saldo SYS (testnet)", value=f"{padrino['saldo_sys']} SYS", inline=True)
    embed.add_field(name="🍖 Comidas aportadas", value=str(padrino["comidas_aportadas"]), inline=True)
    embed.set_footer(text="RescuePaw Labs | zkSYS Testnet")
    
    await ctx.send(embed=embed)

# ────────────────────────────────────────────────────────────────
# COMANDO: /ayuda
# ────────────────────────────────────────────────────────────────
@bot.command(name="ayuda")
async def cmd_ayuda(ctx):
    """Muestra todos los comandos disponibles."""
    embed = discord.Embed(
        title="🐾 RescuePaw Labs — Comandos",
        description="Agente autónomo para ayudar perros callejeros en Lima",
        color=0x8B4513
    )
    embed.add_field(
        name="👤 `/registrar`",
        value="Regístrate como padrino y recibe 10 SYS de prueba",
        inline=False
    )
    embed.add_field(
        name="🐕 `/registrar_perro <nombre> <ubicacion>`",
        value="Registra un perro callejero (adjunta foto)",
        inline=False
    )
    embed.add_field(
        name="🍖 `/alimentar <dog_id>`",
        value="Reporta que alimentaste a un perro (adjunta foto)",
        inline=False
    )
    embed.add_field(
        name="📊 `/estado <dog_id>`",
        value="Ver el estado y fondos acumulados de un perro",
        inline=False
    )
    embed.add_field(
        name="📋 `/perros`",
        value="Ver todos los perros registrados",
        inline=False
    )
    embed.add_field(
        name="👤 `/mi_perfil`",
        value="Ver tu saldo y comidas aportadas",
        inline=False
    )
    embed.set_footer(text="🔗 Todos los eventos se registran en zkSYS Testnet")
    await ctx.send(embed=embed)

# ────────────────────────────────────────────────────────────────
# CHAT EN LENGUAJE NATURAL (Chatbot AI Proxy)
# ────────────────────────────────────────────────────────────────
@bot.event
async def on_message(ctx):
    await bot.process_commands(ctx)
    
    if ctx.author == bot.user:
        return
    
    if ctx.content.startswith("/"):
        return

    api_key = os.getenv("OPENROUTER_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openrouter/auto",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres el agente autónomo de RescuePaw Labs. "
                    "Ayudas a conectar estudiantes universitarios con perros callejeros en Lima, Perú. "
                    "Respondes en español, de forma amigable y breve. "
                    "Sabes sobre: registro de perros, sistema de donaciones con blockchain zkSYS, "
                    "comandos disponibles: /registrar, /registrar_perro, /alimentar, /estado, /perros, /mi_perfil. "
                    "Si te preguntan cómo ayudar, explica el sistema brevemente y sugiere usar /ayuda."
                )
            },
            {
                "role": "user",
                "content": ctx.content
            }
        ]
    }
    
    try:
        async with ctx.channel.typing():
            import requests as req
            response = req.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )
            print(f"[DEBUG] Status: {response.status_code}")
            print(f"[DEBUG] Respuesta: {response.text}")
            
            data = response.json()
            respuesta = data["choices"][0]["message"]["content"]
            await ctx.channel.send(respuesta)
    except Exception as e:
        print(f"[ERROR chat] {e}")
        await ctx.channel.send("⚠️ Error interno del agente. Intenta de nuevo.")

# ────────────────────────────────────────────────────────────────
# INICIAR EL BOT
# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ ERROR: Falta el DISCORD_TOKEN en el archivo .env")
    else:
        bot.run(token)