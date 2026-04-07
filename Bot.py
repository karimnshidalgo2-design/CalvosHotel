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

cursor.execute("""
CREATE TABLE IF NOT EXISTS mensajes (
    canal_id INTEGER,
    mensaje_id INTEGER
)
""")

conn.commit()

# =========================
# FUNCIONES DB
# =========================

def crear_libros_db(tipos):
    for tipo in tipos:
        for nivel in range(1, 6):
            cursor.execute(
                "SELECT 1 FROM libros WHERE tipo=? AND nivel=?",
                (tipo.lower(), nivel)
            )
            if cursor.fetchone() is None:
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
# READY
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

    for tipo in tipos:
        niveles = libros_estado[tipo.lower()]
        linea = " | ".join(["🟢" if e else "🔴" for e in niveles])
        mensaje += f"**{tipo.upper()}**\n{linea}\n\n"

    msg = await ctx.send(mensaje)

    cursor.execute("DELETE FROM mensajes WHERE canal_id=?", (ctx.channel.id,))
    cursor.execute(
        "INSERT INTO mensajes (canal_id, mensaje_id) VALUES (?, ?)",
        (ctx.channel.id, msg.id)
    )
    conn.commit()

# =========================
# SET
# =========================

@bot.command()
async def set(ctx, tipo, nivel: int):
    await ctx.message.delete()

    tipo = tipo.lower()
    libros_estado = obtener_libros()

    if tipo not in libros_estado:
        await ctx.send("Ese libro no existe")
        return

    if nivel < 1 or nivel > 5:
        await ctx.send("Nivel inválido")
        return

    actualizar_libro(tipo, nivel, True)
    libros_estado = obtener_libros()

    cursor.execute("SELECT mensaje_id FROM mensajes WHERE canal_id=?", (ctx.channel.id,))
    data = cursor.fetchone()

    if not data:
        await ctx.send("Primero usa !crear_libros")
        return

    mensaje_id = data[0]
    msg = await ctx.channel.fetch_message(mensaje_id)

    contenido = msg.content.split("\n")

    for i, linea in enumerate(contenido):
        if linea.strip() == f"**{tipo.upper()}**":
            nueva_linea = " | ".join(["🟢" if e else "🔴" for e in libros_estado[tipo]])
            contenido[i + 1] = nueva_linea
            break

    await msg.edit(content="\n".join(contenido))

# =========================
# QUITAR
# =========================

@bot.command()
async def quitar(ctx, tipo, nivel: int):
    await ctx.message.delete()

    tipo = tipo.lower()
    libros_estado = obtener_libros()

    if tipo not in libros_estado:
        await ctx.send("Ese libro no existe")
        return

    if nivel < 1 or nivel > 5:
        await ctx.send("Nivel inválido")
        return

    actualizar_libro(tipo, nivel, False)
    libros_estado = obtener_libros()

    cursor.execute("SELECT mensaje_id FROM mensajes WHERE canal_id=?", (ctx.channel.id,))
    data = cursor.fetchone()

    if not data:
        await ctx.send("Primero usa !crear_libros")
        return

    mensaje_id = data[0]
    msg = await ctx.channel.fetch_message(mensaje_id)

    contenido = msg.content.split("\n")

    for i, linea in enumerate(contenido):
        if linea.strip() == f"**{tipo.upper()}**":
            nueva_linea = " | ".join(["🟢" if e else "🔴" for e in libros_estado[tipo]])
            contenido[i + 1] = nueva_linea
            break

    await msg.edit(content="\n".join(contenido))

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

    if not miembros:
        await ctx.send("No hay miembros con rol Calvos")
        return

    random.shuffle(miembros)

    mensaje = "📋 **TAREAS DEL DÍA**\n\n"

    for i, arg in enumerate(args):
        if ":" not in arg:
            await ctx.send(f"Formato incorrecto: {arg}")
            return

        nombre, cantidad = arg.split(":")
        persona = miembros[i % len(miembros)]
        mensaje += f"🔹 **{nombre.capitalize()} ({cantidad})** → {persona.mention}\n"

    await ctx.send(mensaje)

# =========================
# RANDOM
# =========================

@bot.command()
async def ya(ctx):
    await ctx.send("Ya Chepe")

@bot.command()
async def chupalo(ctx):
    await ctx.send("Chupalo Crazy")

@bot.command()
async def mamelo(ctx):
    await ctx.send("mamelo")

@bot.command()
async def sunny(ctx):
    await ctx.send("Es lo mismo")

@bot.command()
async def henry(ctx):
    await ctx.send("Que onda muchachos")

# =========================
# TOKEN
# =========================

bot.run(os.getenv("DISCORD_TOKEN"))