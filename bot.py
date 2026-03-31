import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from agente import AgenteRescuePaw

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
agente = AgenteRescuePaw()

@bot.event
async def on_ready():
    print(f"🐾 RescuePaw Bot conectado como {bot.user}")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="🐕 perros callejeros en Lima"
        )
    )

# ─────────────────────────────────────────────
# REGISTRAR PADRINO
# ─────────────────────────────────────────────
@bot.command(name="registrar")
async def cmd_registrar(ctx):
    resultado = agente.registrar_nuevo_padrino(
        user_id=ctx.author.id,
        nombre=ctx.author.display_name
    )

    embed = discord.Embed(
        title="🐾 Registro de Padrino",
        description=resultado["mensaje"],
        color=0x8B4513 if resultado["exito"] else 0xFF0000
    )
    await ctx.send(embed=embed)

# ─────────────────────────────────────────────
# REGISTRAR PERRO (AUTOMÁTICO)
# ─────────────────────────────────────────────
@bot.command(name="registrar_perro")
async def cmd_registrar_perro(ctx, nombre: str, *, ubicacion: str):

    msg_espera = await ctx.send("🤖 Buscando un perro para ti...")

    resultado = agente.registrar_nuevo_perro(
        nombre=nombre,
        ubicacion=ubicacion,
        registrado_por=ctx.author.id
    )

    await msg_espera.delete()

    embed = discord.Embed(
        title="🐕 Nuevo Perro Registrado",
        description=resultado["mensaje"],
        color=0x8B4513 if resultado["exito"] else 0xFF0000
    )

    if resultado["exito"]:
        embed.set_image(url=resultado["foto_url"])

    await ctx.send(embed=embed)

# ─────────────────────────────────────────────
# ALIMENTAR
# ─────────────────────────────────────────────
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
        title="🍖 Registro de Comida",
        description=resultado["mensaje"],
        color=0x228B22 if resultado["exito"] else 0xFF0000
    )

    await ctx.send(embed=embed)

# ─────────────────────────────────────────────
# OTROS COMANDOS (IGUAL)
# ─────────────────────────────────────────────
@bot.command(name="estado")
async def cmd_estado(ctx, dog_id: str):
    mensaje = agente.ver_estado_perro(dog_id.lower())
    await ctx.send(mensaje)

@bot.command(name="perros")
async def cmd_perros(ctx):
    mensaje = agente.ver_todos_perros()
    await ctx.send(mensaje)

@bot.command(name="mi_perfil")
async def cmd_mi_perfil(ctx):
    from base_datos import obtener_padrino
    padrino = obtener_padrino(ctx.author.id)

    if not padrino:
        await ctx.send("❌ Usa `/registrar` primero.")
        return

    await ctx.send(
        f"👤 {padrino['nombre']}\n"
        f"💰 {padrino['saldo_sys']} SYS\n"
        f"🍖 {padrino['comidas_aportadas']} comidas"
    )
# ─────────────────────────────────────────────
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Mantener comandos normales
    await bot.process_commands(message)

    # 👉 Detectar si mencionan al bot
    if bot.user not in message.mentions:
        return

    # Limpiar mención
    contenido = message.content.replace(f"<@{bot.user.id}>", "")
    contenido = contenido.replace(f"<@!{bot.user.id}>", "")
    contenido = contenido.strip()

    if not contenido:
        await message.channel.send("🐾 Usa: @RescuePaw ayuda")
        return

    partes = contenido.split()
    comando = partes[0].lower()

    # ───────────────
    # REGISTRAR
    # ───────────────
    if comando == "registrar":
        resultado = agente.registrar_nuevo_padrino(
            user_id=message.author.id,
            nombre=message.author.display_name
        )
        await message.channel.send(resultado["mensaje"])

    # ───────────────
    # REGISTRAR PERRO
    # ───────────────
    elif comando == "registrar_perro":

        if len(partes) < 3:
            await message.channel.send("❌ Uso: @RescuePaw registrar_perro <nombre> <ubicacion>")
            return

        nombre = partes[1]
        ubicacion = " ".join(partes[2:])

        msg = await message.channel.send("🤖 Buscando perro...")

        resultado = agente.registrar_nuevo_perro(
            nombre=nombre,
            ubicacion=ubicacion,
            registrado_por=message.author.id
        )

        await msg.delete()

        embed = discord.Embed(
            title="🐕 Nuevo Perro",
            description=resultado["mensaje"],
            color=0x8B4513
        )

        if resultado["exito"]:
            embed.set_image(url=resultado["foto_url"])

        await message.channel.send(embed=embed)

    # ───────────────
    # ALIMENTAR
    # ───────────────
    elif comando == "alimentar":

        if len(partes) < 2:
            await message.channel.send("❌ Uso: @RescuePaw alimentar <dog_id>")
            return

        dog_id = partes[1]

        foto_url = None
        if message.attachments:
            foto_url = message.attachments[0].url

        resultado = agente.procesar_alimentacion(
            dog_id=dog_id,
            user_id=message.author.id,
            foto_url=foto_url
        )

        await message.channel.send(resultado["mensaje"])

    # ───────────────
    # PERROS
    # ───────────────
    elif comando == "perros":
        await message.channel.send(agente.ver_todos_perros())

    # ───────────────
    # ESTADO
    # ───────────────
    elif comando == "estado":

        if len(partes) < 2:
            await message.channel.send("❌ Uso: @RescuePaw estado <dog_id>")
            return

        await message.channel.send(
            agente.ver_estado_perro(partes[1])
        )

    # ───────────────
    # PERFIL
    # ───────────────
    elif comando == "mi_perfil":
        from base_datos import obtener_padrino

        padrino = obtener_padrino(message.author.id)

        if not padrino:
            await message.channel.send("❌ No estás registrado")
            return

        await message.channel.send(
            f"👤 {padrino['nombre']}\n"
            f"💰 {padrino['saldo_sys']} SYS\n"
            f"🍖 {padrino['comidas_aportadas']}"
        )

    # ───────────────
    # AYUDA
    # ───────────────
    elif comando == "ayuda":
        await message.channel.send(
            "🐾 Comandos:\n"
            "@RescuePaw registrar\n"
            "@RescuePaw registrar_perro nombre ubicacion\n"
            "@RescuePaw alimentar dog_id\n"
            "@RescuePaw perros\n"
            "@RescuePaw estado dog_id\n"
            "@RescuePaw mi_perfil"
        )

    else:
        await message.channel.send("❓ Comando no reconocido")
# ─────────────────────────────────────────────
if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))