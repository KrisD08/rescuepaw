import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from agente import AgenteRescuePaw
import aiohttp
import requests

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

agente = AgenteRescuePaw()

# ------------------ PREFIX SOLO CON MENCIÓN ------------------
async def get_prefix(bot, message):
    prefixes = [f"<@!{bot.user.id}> ", f"<@{bot.user.id}> "]
    for prefix in prefixes:
        if message.content.startswith(prefix):
            return prefix
    return ""  

bot = commands.Bot(command_prefix=get_prefix, intents=intents)

# ------------------ READY ------------------
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

# ------------------ FUNCIONES AUXILIARES ------------------
async def buscar_imagen_perro():
    """
    Retorna una imagen aleatoria de perro usando Dog CEO API
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dog.ceo/api/breeds/image/random") as resp:
                data = await resp.json()
                return data.get("message")
    except:
        return None

# ------------------ COMANDOS --------------------
@bot.command(name="registrar")
async def cmd_registrar(ctx):
    resultado = agente.registrar_nuevo_padrino(
        user_id=ctx.author.id,
        nombre=ctx.author.display_name
    )
    # Manejo tx_hash None
    tx_hash = resultado.get("tx_hash")
    if tx_hash:
        tx_text = f"🔗 {tx_hash[:20]}..."
    else:
        tx_text = "⚠️ No se generó transacción (fondos insuficientes)"

    embed = discord.Embed(
        title="🐾 RescuePaw — Registro de Padrino",
        description=f"{resultado['mensaje']}\n{tx_text}",
        color=0x8B4513 if resultado["exito"] else 0xFF0000
    )
    await ctx.send(embed=embed)

@bot.command(name="registrar_perro")
async def cmd_registrar_perro(ctx, nombre: str, *, ubicacion: str):
    foto_url = None
    if ctx.message.attachments:
        foto_url = ctx.message.attachments[0].url
    else:
        foto_url = await buscar_imagen_perro()
    
    if not foto_url:
        await ctx.send("❌ No encontré una imagen del perro. Por favor adjunta una foto.")
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

# ------------------- OTROS COMANDOS (alimentar, estado, perros, mi_perfil, ayuda) --------------------
# Puedes copiar el mismo código de antes; no se modifica

# ------------------- EVENTO on_message para texto libre ------------------
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Procesa comandos si empiezan con la mención
    await bot.process_commands(message)

    # Texto libre con mención del bot
    if bot.user in message.mentions:
        texto = message.content.replace(f"<@!{bot.user.id}>", "").replace(f"<@{bot.user.id}>", "").strip()
        if not texto:
            return
        
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
                {"role": "system", "content": "Eres el agente autónomo de RescuePaw Labs. Respondes en español de forma breve y amigable."},
                {"role": "user", "content": texto}
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

# ------------------- INICIO DEL BOT ------------------
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ ERROR: Falta el DISCORD_TOKEN en el archivo .env")
    else:
        bot.run(token)