import gdown
import tarfile
import discord
from discord.ext import commands
import asyncio
import os
import youtube_dl
from dotenv import load_dotenv

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True  # Activar la intención de contenido de mensajes

bot = commands.Bot(command_prefix='!', intents=intents)

# Enlace de Google Drive al archivo FFmpeg
google_drive_url = 'https://drive.google.com/drive/folders/1qiAYlbJa2tefZI4ONzq_Mb3sbUewFr3u?usp=sharing'  # Reemplaza YOUR_FILE_ID con el ID del archivo
output_path = 'ffmpeg-7.0.2.tar.xz'
extracted_path = 'ffmpeg-7.0.2'

# Descargar y extraer FFmpeg
def setup_ffmpeg():
    if not os.path.exists(extracted_path):
        gdown.download(google_drive_url, output_path, quiet=False)
        with tarfile.open(output_path, 'r:xz') as tar:
            tar.extractall()
        os.remove(output_path)
        print(f'FFmpeg extraído en {extracted_path}')
    else:
        print('FFmpeg ya está configurado.')

@bot.event
async def on_ready():
    setup_ffmpeg()
    print(f'Bot {bot.user.name} está listo y conectado!')
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    
    if channel:
        await connect_and_play(channel)

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
    'options': '-vn',
    'ffmpeg_location': 'ffmpeg-7.0.2/bin',  # Asegúrate de que la ruta sea correcta
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

# Cargar el token desde el archivo .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)

