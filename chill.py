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


# Lista de reproducción global y la lista de repetición
queue = []
repeat_list = [
    "https://www.youtube.com/watch?v=jfKfPfyJRdk&pp=ygUFY2hpbGw%3D"
]  # Esta es la lista de canciones que se repetirá al final

# Función para reconectar al canal de voz 24/7 si el bot es desconectado
async def ensure_voice_connection():
    while True:
        for guild in bot.guilds:
            channel = discord.utils.get(guild.voice_channels, name=VOICE_CHANNEL_NAME)
            if channel and not bot.voice_clients:
                await channel.connect()
        await asyncio.sleep(30)  # Verifica cada 30 segundos si sigue conectado

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    # Iniciar el proceso de reconexión al canal 24/7
    bot.loop.create_task(ensure_voice_connection())

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
        queue.insert(0, player)  # Agrega el video al inicio de la cola para darle prioridad

        if not ctx.voice_client.is_playing():
            await play_next(ctx)  # Reproduce el siguiente video en la cola
        else:
            await ctx.send(f'Video añadido a la cola: {player.title}')

async def play_next(ctx):
    if len(queue) > 0:
        player = queue.pop(0)  # Obtén el primer video en la cola
        ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop).result())
        await ctx.send(f'Ahora reproduciendo: {player.title}')
    else:
        # Si la cola está vacía, reproducir la lista de repetición
        if len(repeat_list) > 0:
            player = await YTDLSource.from_url(repeat_list[0], loop=bot.loop, stream=True)
            queue.extend([await YTDLSource.from_url(url, loop=bot.loop, stream=True) for url in repeat_list[1:]])
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop).result())
            await ctx.send(f'Ahora reproduciendo: {player.title}')
        else:
            await ctx.send('La lista de reproducción está vacía.')

@bot.command(name='stop', help='Detiene la reproducción de música.')
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()  # Solo detiene la reproducción sin desconectar del canal

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

@bot.command(name='next', help='Salta a la siguiente canción en la cola.')
async def next(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()  # Detiene la canción actual, activando el "after" para reproducir la siguiente.

@bot.command(name='addrepeat', help='Agrega una canción a la lista de repetición.')
async def add_to_repeat_list(ctx, *, url: str):
    repeat_list.append(url)
    await ctx.send(f"Agregada a la lista de repetición: {url}")

@bot.command(name='removerepeat', help='Muestra la lista de repetición y permite eliminar una canción usando emojis.')
async def remove_from_repeat_list(ctx):
    if not repeat_list:
        await ctx.send("La lista de repetición está vacía.")
        return

    # Muestra las canciones en la lista de repetición
    repeat_list_message = '\n'.join(f"{i+1}. {url}" for i, url in enumerate(repeat_list))
    message = await ctx.send(f"Lista de repetición:\n{repeat_list_message}\nReacciona con el número correspondiente para eliminar una canción.")

    # Reacciones de números del 1 al número de canciones en la lista
    for i in range(len(repeat_list)):
        await message.add_reaction(f"{i+1}\u20E3")  # 1️⃣, 2️⃣, etc.

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in [f"{i+1}\u20E3" for i in range(len(repeat_list))]

    try:
        reaction, _ = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        index = int(reaction.emoji[0]) - 1  # Obtiene el índice a partir del emoji
        removed_song = repeat_list.pop(index)
        await ctx.send(f"Canción eliminada de la lista de repetición: {removed_song}")
    except asyncio.TimeoutError:
        await ctx.send("No se recibió una respuesta a tiempo. No se eliminó ninguna canción.")

# Iniciar el bot
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)
