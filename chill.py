import discord
from discord.ext import commands
from discord.utils import get
import yt_dlp as youtube_dl  # Usando yt-dlp en lugar de youtube_dl
import os
import requests
import asyncio
from dotenv import load_dotenv

# Cargar el token desde el archivo .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configuración del bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='*', intents=intents)

# Configura youtube_dl para extraer audio
ytdl_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

song_queue = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Reemplaza con URLs válidas
    "https://www.youtube.com/watch?v=3JZ_D3ELwOQ",
]

current_song_index = 0

# Configuración del canal de voz específico por ID y lista de canciones chill
VOICE_CHANNEL_ID = 1282832608375341086  # Reemplaza con la ID de tu canal de voz específico
chill_playlist = [
    "https://www.youtube.com/watch?v=jfKfPfyJRdk",  # Lofi hip hop radio
    "https://www.youtube.com/watch?v=rUxyKA_-grg",  # Lofi Chill Music Mix
    "https://www.youtube.com/watch?v=DWcJFNfaw9c",  # Coffee Jazz Music
    # Agrega más URLs de YouTube con música chill según tus preferencias
]

# Inicializa la cola de reproducción con la lista de reproducción chill
song_queue = chill_playlist.copy()

# Conéctate automáticamente a un canal de voz específico y reproduce música de forma continua
@bot.event
async def on_ready():
    print(f'Conectado como {bot.user}!')

    # Busca el canal de voz específico por su ID
    for guild in bot.guilds:
        channel = guild.get_channel(VOICE_CHANNEL_ID)
        if isinstance(channel, discord.VoiceChannel):
            # Conectar al canal de voz específico
            voice_client = get(bot.voice_clients, guild=guild)
            if voice_client is None:
                await channel.connect()
                voice_client = get(bot.voice_clients, guild=guild)
            await play_next_song(guild, voice_client)
            break
    else:
        print(f"El canal de voz con ID '{VOICE_CHANNEL_ID}' no se encontró en ninguno de los servidores.")

# Función para reproducir la siguiente canción en la cola
async def play_next_song(guild, voice_client):
    if len(song_queue) > 0:
        url = song_queue.pop(0)  # Extrae la primera canción de la cola y la elimina

        # Descargar la canción con yt-dlp
        with youtube_dl.YoutubeDL(ytdl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                url2 = info['url']
                title = info['title']
            except Exception as e:
                print(f"Error al extraer la URL de la canción: {e}")
                await play_next_song(guild, voice_client)  # Intenta reproducir la siguiente canción
                return
        
        # Reproduce la canción
        def after_playing(error):
            if error:
                print(f"Error en la reproducción: {error}")
            # Llama a la siguiente canción después de terminar la reproducción
            bot.loop.create_task(play_next_song(guild, voice_client))

        voice_client.play(discord.FFmpegPCMAudio(url2, **ffmpeg_options), after=after_playing)
        print(f"Reproduciendo: {title}")
        
        # Enviar mensaje de que la canción se está reproduciendo (opcional)
        channel = discord.utils.get(guild.text_channels, name='general')  # Cambia 'general' por el nombre de tu canal de texto
        if channel:
            await channel.send(f"🎶 Reproduciendo: {title}")
    else:
        # Reinicia la lista de reproducción cuando termine
        song_queue.extend(chill_playlist)
        await play_next_song(guild, voice_client)


@bot.command(name='play', help='Reproduce una canción desde YouTube o continúa la lista de reproducción.')
async def play(ctx, url: str = None):
    voice_client = get(bot.voice_clients, guild=ctx.guild)
    
    if voice_client and voice_client.is_connected():
        if url:
            # Agregar URL a la cola y reproducir si está conectado
            song_queue.insert(0, url)
            await ctx.send(f"Agregada a la cola: {url}")
        if not voice_client.is_playing():
            await play_next_song(ctx.guild, voice_client)
    else:
        await ctx.send("El bot no está conectado a un canal de voz.")

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

@bot.command(name='connect', help='Conecta al bot al canal de voz especificado por ID')
async def connect(ctx, channel_id: int):
    # Obtener el canal de voz por su ID
    channel = ctx.guild.get_channel(channel_id)
    if isinstance(channel, discord.VoiceChannel):
        # Si el bot ya está en otro canal de voz, desconéctalo
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        
        # Conectar al canal de voz
        try:
            await channel.connect()
            await ctx.send(f"Conectado al canal de voz: {channel.name}")
        except Exception as e:
            await ctx.send(f"No se pudo conectar al canal de voz: {e}")
            print(f"Error al conectar al canal de voz: {e}")
    else:
        await ctx.send("No se encontró un canal de voz con esa ID.")

@bot.command(name='resume', help='Reanuda la música pausada')
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Música reanudada.")
    else:
        await ctx.send("No hay música pausada para reanudar.")

@bot.command(name='pause', help='Pausa la música actual')
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Música pausada.")
    else:
        await ctx.send("No hay música reproduciéndose para pausar.")


# Comando para desconectar al bot manualmente
@bot.command(name='disconnect', help='Desconecta al bot del canal de voz')
async def disconnect(ctx):
    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send("Desconectado del canal de voz.")
    else:
        await ctx.send("El bot no está conectado a ningún canal de voz.")

@bot.command(name='check_internet', help='Verifica la conexión a Internet')
async def check_internet(ctx):
    try:
        response = requests.get('https://www.google.com', timeout=5)
        if response.status_code == 200:
            await ctx.send("Conexión a Internet: ¡OK!")
        else:
            await ctx.send("Conexión a Internet: Fallo en la solicitud.")
    except requests.ConnectionError:
        await ctx.send("Conexión a Internet: No se puede conectar.")
    except Exception as e:
        await ctx.send(f"Error al verificar la conexión a Internet: {e}")

@bot.command(name='restart', help='Reinicia el bot')
async def restart(ctx):
    await ctx.send("Reiniciando el bot...")
    await bot.logout()  # Cierra la sesión del bot
    os.system('chill.py')  # Reinicia el bot. Reemplaza 'your_script_name.py' con el nombre de tu archivo de bot

# Iniciar el bot
bot.run(TOKEN)
