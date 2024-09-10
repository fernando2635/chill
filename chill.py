import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# Cargar el token desde el archivo .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
# Reemplaza 'YOUR_VOICE_CHANNEL_ID' con el ID del canal de voz donde el bot reproducirá música
VOICE_CHANNEL_ID = 1282832608375341086


# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# URL de una estación de radio de música lofi/jazz
RADIO_URL = "https://mytuner-radio.com/es/emisora/smooth-jazz-instrumental-479346/"

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if channel:
        await play_radio(channel)
    else:
        print(f"El canal con ID {VOICE_CHANNEL_ID} no existe. Verifica el ID.")

async def play_radio(channel):
    # Conectar al canal de voz
    voice_client = await channel.connect()
    
    # Reproduce la música en bucle
    while True:
        try:
            voice_client.play(discord.FFmpegPCMAudio(RADIO_URL))
            while voice_client.is_playing():
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Error al reproducir música: {e}")
            await asyncio.sleep(5)  # Espera antes de intentar de nuevo

@bot.command(name='stop')
async def stop(ctx):
    # Comando para desconectar el bot del canal de voz
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Bot desconectado del canal de voz.")
    else:
        await ctx.send("No estoy en ningún canal de voz.")
# Iniciar el bot
bot.run(TOKEN)
