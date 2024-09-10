import discord
from discord.ext import commands
from discord.utils import get
import yt_dlp as youtube_dl
import os
from dotenv import load_dotenv

# Cargar el token desde el archivo .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configuración del bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Configuración del canal de voz específico por ID y lista de canciones chill
VOICE_CHANNEL_ID = 123456789012345678  # Reemplaza con la ID de tu canal de voz específico
chill_playlist = [
    "https://www.youtube.com/watch?v=jfKfPfyJRdk",  # Lofi hip hop radio
    "https://www.youtube.com/watch?v=rUxyKA_-grg",  # Lofi Chill Music Mix
    "https://www.youtube.com/watch?v=DWcJFNfaw9c",  # Coffee Jazz Music
]

# Inicializa la cola de reproducción con la lista de reproducción chill
song_queue = chill_playlist.copy()
current_song = None  # Variable para mantener la canción actual

# Configura yt-dlp para extraer audio
ytdl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,  # Evita muchos mensajes de depuración
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # Evita restricciones regionales
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

@bot.event
async def on_ready():
    print(f'Conectado como {bot.user}!')

    # Conectar al canal de voz específico
    for guild in bot.guilds:
        channel = guild.get_channel(VOICE_CHANNEL_ID)
        if isinstance(channel, discord.VoiceChannel):
            voice_client = get(bot.voice_clients, guild=guild)
            if voice_client is None:
                voice_client = await channel.connect()
            await play_next_song(guild, voice_client)
            break
    else:
        print(f"El canal de voz con ID '{VOICE_CHANNEL_ID}' no se encontró en ninguno de los servidores.")

async def play_next_song(guild, voice_client):
    global current_song  # Utilizar la variable global para la canción actual

    if len(song_queue) > 0:
        url = song_queue.pop(0)  # Extrae la primera canción de la cola y la elimina

        # Descargar la canción con yt-dlp
        with youtube_dl.YoutubeDL(ytdl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                url2 = info['url']
                current_song = info['title']  # Actualizar la canción actual
            except Exception as e:
                print(f"Error al extraer la URL de la canción: {e}")
                await play_next_song(guild, voice_client)  # Intenta reproducir la siguiente canción
                return
        
        if not voice_client.is_playing():
            # Reproduce la canción
            def after_playing(error):
                if error:
                    print(f"Error en la reproducción: {error}")
                bot.loop.create_task(play_next_song(guild, voice_client))

            try:
                print(f"Intentando reproducir: {current_song}")
                voice_client.play(discord.FFmpegPCMAudio(url2, **ffmpeg_options), after=after_playing)
            except Exception as e:
                print(f"Error al intentar reproducir: {e}")
                await play_next_song(guild, voice_client)
        
        # Enviar mensaje de que la canción se está reproduciendo (opcional)
        channel = discord.utils.get(guild.text_channels, name='general')  # Cambia 'general' por el nombre de tu canal de texto
        if channel:
            await channel.send(f"🎶 Reproduciendo: {current_song}")
    else:
        # Reinicia la lista de reproducción cuando termine
        song_queue.extend(chill_playlist)
        await play_next_song(guild, voice_client)

@bot.command(name='play', help='Reproduce una canción desde YouTube o continúa la lista de reproducción.')
async def play(ctx, url: str = None):
    voice_client = get(bot.voice_clients, guild=ctx.guild)
    
    if voice_client and voice_client.is_connected():
        if url:
            song_queue.append(url)
            await ctx.send(f"Agregada a la cola: {url}")
        if not voice_client.is_playing():
            await play_next_song(ctx.guild, voice_client)
    else:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            voice_client = await channel.connect()
            await ctx.send(f"Conectado al canal de voz: {channel.name}")
            if url:
                song_queue.append(url)
                await ctx.send(f"Agregada a la cola: {url}")
            await play_next_song(ctx.guild, voice_client)
        else:
            await ctx.send("Debes estar en un canal de voz o conectar el bot primero.")

@bot.command(name='queue', help='Muestra la lista de reproducción actual.')
async def queue(ctx):
    if len(song_queue) == 0:
        await ctx.send("La lista de reproducción está vacía.")
    else:
        queue_list = '\n'.join([f"{i+1}. {url}" for i, url in enumerate(song_queue)])
        await ctx.send(f"Lista de reproducción actual:\n{queue_list}")

@bot.command(name='nowplaying', help='Muestra la canción que se está reproduciendo actualmente.')
async def now_playing(ctx):
    if current_song:
        await ctx.send(f"🎶 Ahora reproduciendo: {current_song}")
    else:
        await ctx.send("No hay ninguna canción reproduciéndose actualmente.")

@bot.command(name='stop', help='Detiene la reproducción de música y desconecta al bot del canal de voz')
async def stop(ctx):
    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        voice_client.stop()  # Detiene la reproducción de música
        await voice_client.disconnect()  # Desconecta del canal de voz
        await ctx.send("Detenido y desconectado del canal de voz.")
    else:
        await ctx.send("El bot no está conectado a ningún canal de voz.")

# Iniciar el bot
bot.run(TOKEN)
