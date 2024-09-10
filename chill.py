import gdown
import os
import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Enlace de Google Drive a los archivos binarios de FFmpeg
google_drive_url_ffmpeg = 'https://drive.google.com/uc?id=YOUR_FILE_ID_FFMPEG'
google_drive_url_ffplay = 'https://drive.google.com/uc?id=YOUR_FILE_ID_FFPLAY'
google_drive_url_ffprobe = 'https://drive.google.com/uc?id=YOUR_FILE_ID_FFPROBE'

# Directorio para guardar los binarios de FFmpeg
ffmpeg_bin_path = 'ffmpeg_bin'
ffmpeg_executable = 'ffmpeg_bin/ffmpeg'
ffplay_executable = 'ffmpeg_bin/ffplay'
ffprobe_executable = 'ffmpeg_bin/ffprobe'

# Descargar y preparar FFmpeg
def setup_ffmpeg():
    if not os.path.exists(ffmpeg_bin_path):
        os.makedirs(ffmpeg_bin_path)
        print(f'Descargando FFmpeg...')
        
        # Descargar binarios de FFmpeg
        gdown.download(google_drive_url_ffmpeg, os.path.join(ffmpeg_bin_path, 'ffmpeg'), quiet=False)
        gdown.download(google_drive_url_ffplay, os.path.join(ffmpeg_bin_path, 'ffplay'), quiet=False)
        gdown.download(google_drive_url_ffprobe, os.path.join(ffmpeg_bin_path, 'ffprobe'), quiet=False)
        
        # Hacer los archivos ejecutables
        os.chmod(ffmpeg_executable, 0o755)
        os.chmod(ffplay_executable, 0o755)
        os.chmod(ffprobe_executable, 0o755)
        
        print(f'FFmpeg y herramientas asociadas están listas.')
    else:
        print('FFmpeg ya está configurado.')

@bot.event
async def on_ready():
    setup_ffmpeg()
    print(f'Bot {bot.user.name} está listo y conectado!')

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
    'extract_flat': True,
}

ffmpeg_options = {
    'executable': ffmpeg_executable,
    'options': '-vn',
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

async def connect_and_play(channel):
    try:
        voice_client = discord.utils.get(bot.voice_clients, guild=channel.guild)

        if not voice_client:
            voice_client = await channel.connect()

        while True:
            if not voice_client.is_playing():
                player = await YTDLSource.from_url(YOUTUBE_URL, loop=bot.loop, stream=True)
                voice_client.play(player)
            await asyncio.sleep(5)
    except discord.errors.ConnectionClosed as e:
        print(f"Error de conexión: {e}. Reintentando en 5 segundos...")
        await asyncio.sleep(5)
        await connect_and_play(channel)

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} está listo y conectado!')
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    
    if channel:
        await connect_and_play(channel)

# Iniciar el bot
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)
