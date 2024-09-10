import os
import discord
from discord.ext import commands
import youtube_dl
import asyncio
from dotenv import load_dotenv

# Cargar el token desde el archivo .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configuración del bot
# Configuración de intents para permitir la lectura de contenido de mensajes
intents = discord.Intents.default()
intents.message_content = True  # Activar la intención de contenido de mensajes

bot = commands.Bot(command_prefix='!', intents=intents)

# Reemplaza con el ID de tu canal de voz
VOICE_CHANNEL_ID = 1282832608375341086  # ID del canal de voz donde el bot debe unirse
YOUTUBE_URL = 'https://www.youtube.com/watch?v=jfKfPfyJRdk'  # Enlace a una transmisión en vivo de música chill

# Configuración de yt-dlp y FFmpeg
ytdl_format_options = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'noplaylist': True,
    'quiet': True,
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} está listo y conectado!')
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    
    if channel:
        await connect_and_play(channel)


async def connect_and_play(channel):
    try:
        voice_client = discord.utils.get(bot.voice_clients, guild=channel.guild)

        if not voice_client:
            voice_client = await channel.connect()

        while True:
            if not voice_client.is_playing():
                player = await YTDLSource.from_url(YOUTUBE_URL, loop=bot.loop, stream=True)
                voice_client.play(player)
            await asyncio.sleep(5)  # Esperar un poco antes de verificar nuevamente
    except discord.errors.ConnectionClosed as e:
        print(f"Error de conexión: {e}. Reintentando en 5 segundos...")
        await asyncio.sleep(5)
        await connect_and_play(channel)  # Reconectar


@bot.event
async def on_voice_state_update(member, before, after):
    # Si el bot se desconecta del canal, volver a conectarlo
    if member == bot.user and before.channel is not None and after.channel is None:
        await asyncio.sleep(5)  # Esperar un poco antes de intentar reconectar
        channel = bot.get_channel(VOICE_CHANNEL_ID)
        await connect_and_play(channel)

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
