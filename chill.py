import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import youtube_dl

# Cargar el token desde el archivo .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

ytdl_format_options = {
    'format': 'bapest',
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

ffmpeg_format_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_format_options), data=data)

@bot.command(name='play', help='Reproduce una canción de YouTube')
async def play(ctx, url):
    try:
        server = ctx.message.guild
        voice_channel = server.voice_client

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=bot.loop)
            voice_channel.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send('**Now playing:** {}'.format(player.title))
    except:
        await ctx.send("El bot no está conectado a un canal de voz.")

@bot.command(name='queue', help='Muestra la cola de reproducción actual')
async def queue(ctx):
    voice = ctx.voice_client
    if voice:
        await ctx.send('**Queue:** {}'.format(voice.source.data.get('title')))
    else:
        await ctx.send("El bot no está conectado a un canal de voz.")

@bot.command(name='skip', help='Salta la canción actual')
async def skip(ctx):
    voice = ctx.voice_client
    if voice:
        await voice.stop()
        await ctx.send("**Skipped:** {}".format(voice.source.data.get('title')))
    else:
        await ctx.send("El bot no está conectado a un canal de voz.")

@bot.command(name='stop', help='Detiene la reproducción de música')
async def stop(ctx):
    voice = ctx.voice_client
    if voice:
        await voice.stop()
        await ctx.send("**Stopped:** {}".format(voice.source.data.get('title')))
    else:
        await ctx.send("El bot no está conectado a un canal de voz.")

@bot.event
async def on_ready():
    channel = bot.get_channel(1282832608375341086)  # Reemplaza con el ID del canal de voz
    await channel.connect()
    print(f'{bot.user} has connected to Discord!')
    
# Iniciar el bot
bot.run(TOKEN)
