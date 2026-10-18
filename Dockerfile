FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg unzip espeak && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY app_bundle.zip /app/app_bundle.zip
RUN unzip -q /app/app_bundle.zip -d /app && pip install --no-cache-dir -r /app/requirements.txt
COPY deploy_patch.py /app/deploy_patch.py
RUN python /app/deploy_patch.py
COPY deploy_seed.py /app/deploy_seed.py
RUN python /app/deploy_seed.py
RUN espeak -v es -s 135 -a 150 -w /app/demo_assets/narracion_demo.wav "Una señal apareció sin explicación. Nadie conocía su origen. En los archivos encontramos una pista olvidada. Y entonces, la transmisión volvió a comenzar."
RUN mkdir -p /data/projects
ENV PYTHONUNBUFFERED=1 STUDIO_DATA_DIR=/data/projects
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
