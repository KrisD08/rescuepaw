import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from agente import AgenteRescuePaw
import aiohttp
import re
import requests

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

# command_prefix=None para que solo funcione con mención
bot = commands.Bot(command_prefix=None, intents=intents)

agente = AgenteRescuePaw()

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

async def buscar_imagen_perro(nombre):
    url = f"https://duckduckgo.com/?q={nombre}+perro&iax=images&ia=images"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            html = await resp.text()
            urls = re.findall(r'"image":"(https://[^"]+)"', html)
            if urls:
                return urls[0]
    return None

# ------------------ COMANDOS --------------------

@bot.command(name="registrar")
async def cmd_registrar(ctx):
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

@bot.command(name="registrar_perro")
async def cmd_registrar_perro(ctx, nombre: str, *, ubicacion: str):
    foto_url = None
    if ctx.message.attachments:
        foto_url = ctx.message.attachments[0].url
    else:
        foto_url = await buscar_imagen_perro(nombre)
    
    if not foto_url:
        await ctx.send("❌ No encontré una imagen del perro. Por favor adjunta una foto o usa un nombre diferente.")
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
        title="🐕 RescuePaw — Nuevo Perro",
        description=resultado["mensaje"],
        color=0x8B4513 if resultado["exito"] else 0xFF0000
    )
    if resultado["exito"]:
        embed.set_thumbnail(url=foto_url)
    else:
        embed.add_field(name="❌ Error", value="Error IA detectando perro")
    await ctx.send(embed=embed)

@bot.command(name="alimentar")
async def cmd_alimentar(ctx, dog_id: str):
    foto_url = None
    if ctx.message.attachments:
        foto_url = ctx.message.attachments[0].url
    
    msg_espera = await ctx.send("🤖 Verificando...")
    resultado = agente.procesar_alimentacion(
        dog_id=dog_id.lower(),
        user_id=ctx.author.id,
        foto_url=foto_url
    )
    await msg_espera.delete()
    embed = discord.Embed(
        title="🍖 RescuePaw — Registro de Comida",
        description=resultado["mensaje"],
        color=0x228B22 if resultado["exito"] else 0xFF0000
    )
    embed.set_footer(text="Agente autónomo RescuePaw | zkSYS Testnet")
    await ctx.send(embed=embed)

@bot.command(name="estado")
async def cmd_estado(ctx, dog_id: str):
    mensaje = agente.ver_estado_perro(dog_id.lower())
    embed = discord.Embed(
        title="📊 RescuePaw — Estado del Perro",
        description=mensaje,
        color=0x8B4513
    )
    await ctx.send(embed=embed)

@bot.command(name="perros")
async def cmd_perros(ctx):
    mensaje = agente.ver_todos_perros()
    embed = discord.Embed(
        title="🐕 RescuePaw — Perros Registrados",
        description=mensaje,
        color=0x8B4513
    )
    embed.set_footer(text="Usa @RescuePaw alimentar <dog_id> para ayudar")
    await ctx.send(embed=embed)

@bot.command(name="mi_perfil")
async def cmd_mi_perfil(ctx):
    from base_datos import obtener_padrino
    padrino = obtener_padrino(ctx.author.id)
    if not padrino:
        await ctx.send("❌ No estás registrado. Usa `@RescuePaw registrar` primero.")
        return
    embed = discord.Embed(
        title=f"👤 Perfil de {padrino['nombre']}",
        color=0x8B4513
    )
    embed.add_field(name="💰 Saldo SYS (testnet)", value=f"{padrino['saldo_sys']} SYS", inline=True)
    embed.add_field(name="🍖 Comidas aportadas", value=str(padrino["comidas_aportadas"]), inline=True)
    embed.set_footer(text="RescuePaw Labs | zkSYS Testnet")
    await ctx.send(embed=embed)

@bot.command(name="ayuda")
async def cmd_ayuda(ctx):
    embed = discord.Embed(
        title="🐾 RescuePaw Labs — Comandos",
        description="Agente autónomo para ayudar perros callejeros en Lima",
        color=0x8B4513
    )
    embed.add_field(name="👤 `@RescuePaw registrar`", value="Regístrate como padrino y recibe 10 SYS de prueba", inline=False)
    embed.add_field(name="🐕 `@RescuePaw registrar_perro <nombre> <ubicacion>`", value="Registra un perro callejero (imagen automática o adjunta)", inline=False)
    embed.add_field(name="🍖 `@RescuePaw alimentar <dog_id>`", value="Reporta que alimentaste a un perro (adjunta foto opcional)", inline=False)
    embed.add_field(name="📊 `@RescuePaw estado <dog_id>`", value="Ver estado y fondos acumulados de un perro", inline=False)
    embed.add_field(name="📋 `@RescuePaw perros`", value="Ver todos los perros registrados", inline=False)
    embed.add_field(name="👤 `@RescuePaw mi_perfil`", value="Ver tu saldo y comidas aportadas", inline=False)
    embed.set_footer(text="🔗 Todos los eventos se registran en zkSYS Testnet")
    await ctx.send(embed=embed)

# -------- EVENTO ON_MESSAGE para comandos y texto libre ---------

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Procesa comandos normalmente
    await bot.process_commands(message)

    # Detecta si el bot fue mencionado y no es un comando
    if bot.user in message.mentions:
        # Extraemos solo el texto sin la mención
        texto = message.content.replace(f"<@!{bot.user.id}>", "").strip()

        # Si el mensaje es vacío o es un comando, no hacemos nada más
        if not texto or texto.split()[0].lower() in [cmd.name for cmd in bot.commands]:
            return

        # Si tenemos texto libre, respondemos con IA proxy
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            await message.channel.send("⚠️ No tengo la API key configurada para responder consultas.")
            return

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "openrouter/free",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Eres el agente autónomo de RescuePaw Labs. "
                        "Ayudas a conectar estudiantes universitarios con perros callejeros en Lima, Perú. "
                        "Respondes en español, de forma amigable y breve. "
                        "Sabes sobre: registro de perros, sistema de donaciones con blockchain zkSYS, "
                        "comandos disponibles: registrar, registrar_perro, alimentar, estado, perros, mi_perfil, ayuda. "
                        "Si te preguntan cómo ayudar, explica el sistema brevemente y sugiere usar ayuda."
                    )
                },
                {
                    "role": "user",
                    "content": texto
                }
            ]
        }

        try:
            async with message.channel.typing():
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=15
                )
                data = response.json()
                respuesta = data["choices"][0]["message"]["content"]
                await message.channel.send(respuesta)
        except Exception as e:
            print(f"[ERROR chat] {e}")
            await message.channel.send("⚠️ Error interno del agente. Intenta de nuevo.")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ ERROR: Falta el DISCORD_TOKEN en el archivo .env")
    else:
        bot.run(token)