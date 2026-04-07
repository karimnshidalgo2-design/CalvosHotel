import discord
from discord.ext import commands
import random
import sqlite3
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# BASE DE DATOS
# =========================

conn = sqlite3.connect("libros.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS libros (
    tipo TEXT,
    nivel INTEGER,
    estado INTEGER
)
""")

conn.commit()

# =========================
# FUNCIONES DB
# =========================

def crear_libros_db(tipos):
    cursor.execute("DELETE FROM libros")

    for tipo in tipos:
        for nivel in range(1, 6):
            cursor.execute(
                "INSERT INTO libros (tipo, nivel, estado) VALUES (?, ?, ?)",
                (tipo.lower(), nivel, 0)
            )

    conn.commit()


def obtener_libros():
    cursor.execute("SELECT tipo, nivel, estado FROM libros")
    datos = cursor.fetchall()

    libros = {}

    for tipo, nivel, estado in datos:
        if tipo not in libros:
            libros[tipo] = [False] * 5
        libros[tipo][nivel - 1] = bool(estado)

    return libros


def actualizar_libro(tipo, nivel, valor):
    cursor.execute(
        "UPDATE libros SET estado=? WHERE tipo=? AND nivel=?",
        (1 if valor else 0, tipo, nivel)
    )
    conn.commit()

# =========================
# EVENTO READY
# =========================

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

# =========================
# CREAR LIBROS
# =========================

@bot.command()
async def crear_libros(ctx, *tipos):
    await ctx.message.delete()

    crear_libros_db(tipos)
    libros_estado = obtener_libros()

    mensaje = ""

    for tipo, niveles in libros_estado.items():
        linea = " | ".join(["🟢" if e else "🔴" for e in niveles])
        mensaje += f"**{tipo.upper()}**\n{linea}\n\n"

    await ctx.send(mensaje)

# =========================
# SET
# =========================

@bot.command()
async def set(ctx, tipo, nivel: int):
    await ctx.message.delete()

    libros_estado = obtener_libros()

    tipo = tipo.lower()

    if tipo not in libros_estado:
        await ctx.send("Ese libro no existe")
        return

    if nivel < 1 or nivel > 5:
        await ctx.send("Nivel inválido")
        return

    actualizar_libro(tipo, nivel, True)

    libros_estado = obtener_libros()

    mensaje = ""

    for t, niveles in libros_estado.items():
        linea = " | ".join(["🟢" if e else "🔴" for e in niveles])
        mensaje += f"**{t.upper()}**\n{linea}\n\n"

    await ctx.send(mensaje)

# =========================
# QUITAR
# =========================

@bot.command()
async def quitar(ctx, tipo, nivel: int):
    await ctx.message.delete()

    libros_estado = obtener_libros()

    tipo = tipo.lower()

    if tipo not in libros_estado:
        await ctx.send("Ese libro no existe")
        return

    if nivel < 1 or nivel > 5:
        await ctx.send("Nivel inválido")
        return

    actualizar_libro(tipo, nivel, False)

    libros_estado = obtener_libros()

    mensaje = ""

    for t, niveles in libros_estado.items():
        linea = " | ".join(["🟢" if e else "🔴" for e in niveles])
        mensaje += f"**{t.upper()}**\n{linea}\n\n"

    await ctx.send(mensaje)

# =========================
# TAREAS
# =========================

@bot.command()
async def tareas(ctx, *args):
    rol_calvos = discord.utils.get(ctx.guild.roles, name="Calvos")

    if not rol_calvos:
        await ctx.send("No encontré el rol Calvos")
        return

    miembros = [m for m in ctx.guild.members if rol_calvos in m.roles and not m.bot]

    random.shuffle(miembros)

    mensaje = "📋 **TAREAS DEL DÍA**\n\n"

    for i, arg in enumerate(args):
        nombre, cantidad = arg.split(":")
        persona = miembros[i % len(miembros)]
        mensaje += f"🔹 **{nombre.capitalize()} ({cantidad})** → {persona.mention}\n"

    await ctx.send(mensaje)

# =========================
# COMANDOS RANDOM
# =========================

@bot.command()
async def ya(ctx):
    await ctx.send("Ya Chepe")

@bot.command()
async def chupalo(ctx):
    await ctx.send("Chupalo Crazy")

@bot.command()
async def sunny(ctx):
    await ctx.send("Es lo mismo")

@bot.command()
async def henry(ctx):
    await ctx.send("que onda muchachos")

@bot.command()
async def fran(ctx):
    await ctx.send("Soy gei y no tiene nada de malo")

# =========================
# TOKEN
# =========================

bot.run(os.getenv("DISCORD_TOKEN"))