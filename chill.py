import discord
from discord.ext import commands
import youtube_dl
import os
import asyncio
from dotenv import load_dotenv

# Configuración del bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)
VOICE_CHANNEL_NAME = '24/7'  # Reemplaza con el nombre del canal de voz

# Configuración de youtube_dl
youtube_dl.utils.bug_reports_message = lambda: ''
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
        queue.append(player)  # Agrega el video a la cola

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
        await ctx.send('La cola de reproducción está vacía.')

@bot.command(name='stop', help='Detiene la reproducción de música.')
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

# Iniciar el bot
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)
