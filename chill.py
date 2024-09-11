import discord
from discord.ext import commands
import youtube_dl
import os
import asyncio

# Configuración del bot
# Configuración del bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

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

# Comando para unirse a un canal de voz y empezar a reproducir música
@bot.command(name='play', help='Reproduce música desde YouTube.')
async def play(ctx, *, url: str = 'https://www.youtube.com/watch?v=jfKfPfyJRdk'):  # URL predeterminada de Lofi
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("¡Debes estar en un canal de voz para usar este comando!")
            return

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: print(f'Error al reproducir: {e}') if e else None)
    await ctx.send(f'Ahora reproduciendo: {player.title}')

# Comando para detener la reproducción
@bot.command(name='stop', help='Detiene la reproducción de música.')
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

@bot.event
async def on_ready():
    print(f'{bot.user} ha iniciado sesión.')
# Iniciar el bot
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)
