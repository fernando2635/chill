import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import os
import asyncio
import requests
from dotenv import load_dotenv

# Configuración del bot con intents
intents = discord.Intents.default()
intents.message_content = True  # Necesario para acceder al contenido del mensaje
intents.guilds = True
intents.voice_states = True  # Permite al bot escuchar los estados de voz
bot = commands.Bot(command_prefix='!', intents=intents)
VOICE_CHANNEL_NAME = '24/7'  # Reemplaza con el nombre del canal de voz

# Configuración de yt_dlp
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}
ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


# Cola de reproducción global
queue = []
REPEAT_URL = "https://www.youtube.com/watch?v=jfKfPfyJRdk&pp=ygUFY2hpbGw%3D"

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

    # Buscar el canal de voz por nombre y conectarse
    for guild in bot.guilds:
        channel = discord.utils.get(guild.voice_channels, name=VOICE_CHANNEL_NAME)
        if channel:
            await channel.connect()
            print(f"Bot conectado al canal de voz: {channel.name}")
            break
    else:
        print(f"No se encontró un canal de voz con el nombre '{VOICE_CHANNEL_NAME}'.")

@bot.command(name='play', help='Reproduce música desde YouTube.')
async def play(ctx, *, url: str = 'https://www.youtube.com/watch?v=jfKfPfyJRdk'):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("¡Debes estar en un canal de voz para usar este comando!")
            return

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        
        # Detener la reproducción actual si está en curso
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        # Limpiar la cola y agregar el nuevo video
        queue.clear()
        queue.append(player)
        
        await play_next(ctx)  # Reproduce la canción actual

async def play_next(ctx):
    if len(queue) > 0:
        player = queue.pop(0)  # Obtén el primer video en la cola
        ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop).result())
        await ctx.send(f'Ahora reproduciendo: {player.title}')
    else:
        # Reproducir la canción de repetición al final
        await play_from_url(ctx, REPEAT_URL)

async def play_from_url(ctx, url):
    player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
    ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop).result())
    await ctx.send(f'Ahora reproduciendo: {player.title}')

@bot.command(name='next', help='Reproduce el siguiente video en la cola.')
async def next(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await play_next(ctx)
    else:
        await ctx.send("No hay nada reproduciéndose actualmente.")

@bot.command(name='stop', help='Detiene la reproducción de música.')
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

@bot.command(name='queue', help='Muestra la lista de reproducción.')
async def show_queue(ctx):
    if not queue:
        await ctx.send("La cola de reproducción está vacía.")
    else:
        queue_list = '\n'.join(f'{i + 1}. {item.title}' for i, item in enumerate(queue))
        await ctx.send(f'Lista de reproducción:\n{queue_list}')

@bot.command(name='ping', help='Verifica la conexión a Internet.')
async def ping(ctx):
    try:
        response = requests.get('https://www.google.com/', timeout=5)
        if response.status_code == 200:
            await ctx.send("Conexión a Internet está funcionando.")
        else:
            await ctx.send("Problema con la conexión a Internet.")
    except requests.RequestException:
        await ctx.send("No se pudo conectar a Internet.")

# Iniciar el bot
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)
