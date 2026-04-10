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
    lista_id INTEGER,
    tipo TEXT,
    nivel INTEGER,
    estado INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS mensajes (
    lista_id INTEGER,
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
async def crear_libros(ctx, lista_id: int, *tipos):
    await ctx.message.delete()

    # borrar solo esa lista
    cursor.execute("DELETE FROM libros WHERE lista_id=?", (lista_id,))

    for tipo in tipos:
        for i in range(1,6):
            cursor.execute(
                "INSERT INTO libros VALUES (?, ?, ?, ?)",
                (lista_id, tipo.lower(), i, 0)
            )

    conn.commit()

    # construir mensaje
    mensaje = ""
    for tipo in tipos:
        linea = "🔴 | 🔴 | 🔴 | 🔴 | 🔴"
        mensaje += f"**{tipo.upper()}**\n{linea}\n\n"

    msg = await ctx.send(mensaje)

    cursor.execute("DELETE FROM mensajes WHERE lista_id=?", (lista_id,))
    cursor.execute(
        "INSERT INTO mensajes VALUES (?, ?, ?)",
        (lista_id, ctx.channel.id, msg.id)
    )
    conn.commit()
# =========================
# SET
# =========================

@bot.command()
async def set(ctx, lista_id: int, tipo, nivel: int):
    await ctx.message.delete()

    tipo = tipo.lower()

    cursor.execute("""
    SELECT estado FROM libros 
    WHERE lista_id=? AND tipo=? AND nivel=?
    """, (lista_id, tipo, nivel))

    if not cursor.fetchone():
        await ctx.send("Ese libro no existe en esa lista")
        return

    cursor.execute("""
    UPDATE libros SET estado=1 
    WHERE lista_id=? AND tipo=? AND nivel=?
    """, (lista_id, tipo, nivel))

    conn.commit()

    # reconstruir SOLO esa lista
    cursor.execute("""
    SELECT tipo, nivel, estado FROM libros WHERE lista_id=?
    """, (lista_id,))
    data = cursor.fetchall()

    libros = {}
    for tipo, nivel, estado in data:
        if tipo not in libros:
            libros[tipo] = [False]*5
        libros[tipo][nivel-1] = bool(estado)

    mensaje = ""
    for t, niveles in libros.items():
        linea = " | ".join(["🟢" if e else "🔴" for e in niveles])
        mensaje += f"**{t.upper()}**\n{linea}\n\n"

    # editar SOLO ese mensaje
    cursor.execute("""
    SELECT mensaje_id FROM mensajes WHERE lista_id=?
    """, (lista_id,))
    msg_id = cursor.fetchone()[0]

    msg = await ctx.channel.fetch_message(msg_id)
    await msg.edit(content=mensaje)

# =========================
# QUITAR
# =========================

@bot.command()
async def quitar(ctx, lista_id: int, tipo, nivel: int):
    await ctx.message.delete()

    tipo = tipo.lower()

    cursor.execute("""
    UPDATE libros SET estado=0 
    WHERE lista_id=? AND tipo=? AND nivel=?
    """, (lista_id, tipo, nivel))

    conn.commit()

    # reconstruir igual que set
    cursor.execute("""
    SELECT tipo, nivel, estado FROM libros WHERE lista_id=?
    """, (lista_id,))
    data = cursor.fetchall()

    libros = {}
    for tipo, nivel, estado in data:
        if tipo not in libros:
            libros[tipo] = [False]*5
        libros[tipo][nivel-1] = bool(estado)

    mensaje = ""
    for t, niveles in libros.items():
        linea = " | ".join(["🟢" if e else "🔴" for e in niveles])
        mensaje += f"**{t.upper()}**\n{linea}\n\n"

    cursor.execute("""
    SELECT mensaje_id FROM mensajes WHERE lista_id=?
    """, (lista_id,))
    msg_id = cursor.fetchone()[0]

    msg = await ctx.channel.fetch_message(msg_id)
    await msg.edit(content=mensaje)
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
# Reinciar el bot
# =========================

@bot.command()
async def reiniciar(ctx):
    await ctx.message.delete()

    # 🔒 verificar rol Supremo
    if not any(role.name == "Supremo" for role in ctx.author.roles):
        return

    # 🔥 poner TODO en rojo
    cursor.execute("UPDATE libros SET estado = 0")
    conn.commit()

    # 🔥 obtener todas las listas
    cursor.execute("SELECT lista_id FROM mensajes WHERE canal_id=?", (ctx.channel.id,))
    listas = cursor.fetchall()

    for (lista_id,) in listas:

        # reconstruir cada lista
        cursor.execute("""
        SELECT tipo, nivel, estado FROM libros WHERE lista_id=?
        """, (lista_id,))
        data = cursor.fetchall()

        libros = {}
        for tipo, nivel, estado in data:
            if tipo not in libros:
                libros[tipo] = [False]*5
            libros[tipo][nivel-1] = bool(estado)

        mensaje = ""
        for t, niveles in libros.items():
            linea = " | ".join(["🟢" if e else "🔴" for e in niveles])
            mensaje += f"**{t.upper()}**\n{linea}\n\n"

        # editar mensaje correspondiente
        cursor.execute("""
        SELECT mensaje_id FROM mensajes WHERE lista_id=? AND canal_id=?
        """, (lista_id, ctx.channel.id))
        msg_id = cursor.fetchone()[0]

        try:
            msg = await ctx.channel.fetch_message(msg_id)
            await msg.edit(content=mensaje)
        except:
            pass


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

@bot.command()
async def gigi(ctx):
    await ctx.send("habemus gigi")

# =========================
# TOKEN
# =========================

bot.run(os.getenv("DISCORD_TOKEN"))
