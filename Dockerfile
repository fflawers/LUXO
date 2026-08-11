FROM python:3.11-slim

# Configurar entorno para evitar bloqueos interactivos en la instalación
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema operativo (Audio, OpenCV, etc)
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    portaudio19-dev \
    libasound2-dev \
    alsa-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo en el contenedor
WORKDIR /app

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de la aplicación
COPY . .

# Exponer los puertos usados por la aplicación (Servidor Web y Descargas)
EXPOSE 8550
EXPOSE 8553

# Configurar que el host de BD por defecto sea el contenedor 'db' (sobreescribe .env)
ENV DB_HOST=db
ENV USE_SSL=false

# Comando para iniciar la aplicación
CMD ["python", "run_web.py"]
