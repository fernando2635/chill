import discord
from discord.ext import commands
import lavalink
import os
from dotenv import load_dotenv

# Cargar el token desde el archivo .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configuración del bot

# Configuración de tu bot (token, prefijo, etc.)
bot = commands.Bot(command_prefix="!")

# Configuración de Lavalink
lavalink.add_node('tu_host', tu_puerto, 'password', 'https://tu_lavalink', 'tu_region')

# Evento para conectar Lavalink al bot
@bot.event
async def on_voice_state_update(member, before, after):
    # Lógica para conectar y desconectar Lavalink según la actividad de voz
    # ...

# Comando de reproducción
@bot.command()
async def play(ctx, *, query):
    # Lógica para buscar y reproducir la música
    # ...

# Otros comandos (pausa, reanudar, saltar, etc.)
# ...

# ... (código anterior)

@bot.command()
async def play(ctx, *, query):
    voice_channel = ctx.author.voice.channel
    if not voice_channel:
        await ctx.send("Necesitas estar en un canal de voz")
        return

    voice = get_voice_client(ctx)
    if not voice:
        voice = await voice_channel.connect()

    await ctx.send(f"Buscando: {query}")
    results = await voice.search_yt(query, 1)
    if results['loadType'] == 'LOAD_FAILED':
        await ctx.send("No se encontró la canción")
    else:
        await voice.play(results['tracks'][0])
        await ctx.send(f"Reproduciendo: {results['tracks'][0]['info']['title']}")

# ... (otros comandos)
    
# Iniciar el bot
bot.run(TOKEN)
