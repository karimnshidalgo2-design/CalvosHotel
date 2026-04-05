import discord
from discord.ext import commands
import random
import json
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "libros.json"

libros_estado = {}
mensaje_id = None

# =========================
# GUARDAR / CARGAR
# =========================

def guardar_datos():
    data = {
        "libros_estado": libros_estado,
        "mensaje_id": mensaje_id
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def cargar_datos():
    global libros_estado, mensaje_id
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            libros_estado = data.get("libros_estado", {})
            mensaje_id = data.get("mensaje_id", None)


# =========================
# EVENTO READY
# =========================

@bot.event
async def on_ready():
    cargar_datos()
    print(f"Bot conectado como {bot.user}")


# =========================
# CREAR LIBROS
# =========================

@bot.command()
async def crear_libros(ctx, *tipos):
    global libros_estado, mensaje_id

    await ctx.message.delete()

    libros_estado = {}

    for tipo in tipos:
        libros_estado[tipo.lower()] = [False] * 5

    nuevo_mensaje = ""

    for tipo, niveles in libros_estado.items():
        linea = " | ".join(["🟢" if estado else "🔴" for estado in niveles])
        nuevo_mensaje += f"**{tipo.upper()}**\n{linea}\n\n"

    msg = await ctx.send(nuevo_mensaje)
    mensaje_id = msg.id

    guardar_datos()


# =========================
# SET LIBRO
# =========================

@bot.command()
async def set(ctx, tipo, nivel: int):
    global libros_estado, mensaje_id

    await ctx.message.delete()

    tipo = tipo.lower()

    if tipo not in libros_estado:
        await ctx.send("Ese libro no existe")
        return

    if nivel < 1 or nivel > 5:
        await ctx.send("Nivel inválido (1-5)")
        return

    libros_estado[tipo][nivel - 1] = True

    canal = ctx.channel
    mensaje = await canal.fetch_message(mensaje_id)

    nuevo_mensaje = ""

    for t, niveles in libros_estado.items():
        linea = " | ".join(["🟢" if estado else "🔴" for estado in niveles])
        nuevo_mensaje += f"**{t.upper()}**\n{linea}\n\n"

    await mensaje.edit(content=nuevo_mensaje)

    guardar_datos()


# =========================
# QUITAR LIBRO
# =========================

@bot.command()
async def quitar(ctx, tipo, nivel: int):
    global libros_estado, mensaje_id

    await ctx.message.delete()

    tipo = tipo.lower()

    if tipo not in libros_estado:
        await ctx.send("Ese libro no existe")
        return

    if nivel < 1 or nivel > 5:
        await ctx.send("Nivel inválido (1-5)")
        return

    libros_estado[tipo][nivel - 1] = False

    canal = ctx.channel
    mensaje = await canal.fetch_message(mensaje_id)

    nuevo_mensaje = ""

    for t, niveles in libros_estado.items():
        linea = " | ".join(["🟢" if estado else "🔴" for estado in niveles])
        nuevo_mensaje += f"**{t.upper()}**\n{linea}\n\n"

    await mensaje.edit(content=nuevo_mensaje)

    guardar_datos()


# =========================
# SISTEMA DE TAREAS
# =========================

@bot.command()
async def tareas(ctx, *args):
    rol_calvos = discord.utils.get(ctx.guild.roles, name="Calvos")

    if not rol_calvos:
        await ctx.send("No encontré el rol Calvos")
        return

    miembros = [m for m in ctx.guild.members if rol_calvos in m.roles and not m.bot]

    if not miembros:
        await ctx.send("No hay miembros con rol Calvos")
        return

    random.shuffle(miembros)

    mensaje = "📋 **TAREAS DEL DÍA**\n\n"

    total_miembros = len(miembros)

    for i, arg in enumerate(args):
        try:
            nombre, cantidad = arg.split(":")
            cantidad = int(cantidad)
        except:
            await ctx.send(f"Formato incorrecto en: {arg}")
            return

        if i < total_miembros:
            persona = miembros[i]
        else:
            persona = miembros[i % total_miembros]

        mensaje += f"🔹 **{nombre.capitalize()} ({cantidad})** → {persona.mention}\n"

    mensaje += "\n📸 Suban evidencia cuando terminen"

    await ctx.send(mensaje)


# =========================
# COMANDOS MEME
# =========================

@bot.command()
async def ya(ctx):
    await ctx.send("Ya chepe")


@bot.command()
async def chupalo(ctx):
    await ctx.send("Chupalo crazy")


# =========================
# TOKEN
# =========================

import os
bot.run(os.getenv("DISCORD_TOKEN"))