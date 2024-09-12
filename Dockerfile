# Usa una imagen base de Python
FROM python:3.9-slim

# Instala FFmpeg y otras dependencias necesarias
RUN apt-get update && apt-get install -y ffmpeg

# Crea un directorio de trabajo para el bot
WORKDIR /app

# Copia los archivos del bot al directorio de trabajo
COPY . .

# Instala las dependencias de Python desde requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade discord.py
RUN pip install yt-dlp
RUN pip install ffmpeg
RUN pip install requests

# Comando para ejecutar el bot de Discord
CMD ["python", "chill.py"]
