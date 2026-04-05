import discord
from discord.ext import commands
import random
import json
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

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
# AYUDA
# =========================

@bot.command(name="help")
async def ayuda(ctx):
    await ctx.message.delete()

    embed = discord.Embed(
        title="📚 Comandos del Bot — CalvosHotel",
        description="Aquí tienes una guía rápida de todos los comandos disponibles.",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="📖  `!crear_libros tipo1 tipo2 tipo3...`",
        value=(
            "Crea el panel de libros con los tipos indicados.\n"
            "Cada tipo tendrá **5 niveles** en 🔴 (pendiente) por defecto.\n"
            "**Ejemplo:** `!crear_libros fuego agua tierra`"
        ),
        inline=False
    )

    embed.add_field(
        name="🟢  `!set tipo nivel`",
        value=(
            "Marca un nivel de un libro como **completado** (🟢).\n"
            "El nivel debe ser un número del **1 al 5**.\n"
            "**Ejemplo:** `!set fuego 3`"
        ),
        inline=False
    )

    embed.add_field(
        name="🔴  `!quitar tipo nivel`",
        value=(
            "Marca un nivel de un libro como **pendiente** (🔴).\n"
            "El nivel debe ser un número del **1 al 5**.\n"
            "**Ejemplo:** `!quitar agua 2`"
        ),
        inline=False
    )

    embed.add_field(
        name="📋  `!tareas nombre:cantidad nombre:cantidad...`",
        value=(
            "Asigna tareas aleatoriamente a los miembros con rol **Calvos**.\n"
            "Cada argumento sigue el formato `nombre:cantidad`.\n"
            "**Ejemplo:** `!tareas minar:64 talar:32 pescar:16`"
        ),
        inline=False
    )

    embed.set_footer(text="CalvosHotel Bot • Escribe el comando exactamente como se muestra")

    await ctx.send(embed=embed)


# =========================
# TOKEN
# =========================

import os
bot.run(os.getenv("DISCORD_TOKEN"))
