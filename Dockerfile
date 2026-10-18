FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg unzip espeak && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY app_bundle.zip /app/app_bundle.zip
RUN unzip -q app_bundle.zip -d /app && pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/demo_assets
RUN python - <<'PY'
from PIL import Image,ImageDraw
from pathlib import Path
p=Path('/app/demo_assets')
labels=['Una señal imposible','Un corredor perdido','La evidencia','La transmisión']
colors=[(7,27,42),(16,42,36),(57,38,29),(30,21,55)]
for i,(name,color) in enumerate(zip(labels,colors),1):
 im=Image.new('RGB',(1280,720),color)
 d=ImageDraw.Draw(im)
 for k in range(16):
  d.ellipse((200-k*8,50+k*8,1080+k*8,670-k*8),outline=(45+i*30,80+i*25,75+i*22),width=3)
 d.text((100,340),name,fill=(235,235,220))
 im.save(p/(f'{i:02d}_escena.jpg'),quality=88)
PY
RUN espeak -v es -s 135 -a 150 -w /app/demo_assets/narracion_demo.wav "Una señal apareció sin explicación. Nadie conocía su origen. En los archivos encontramos una pista olvidada. Y entonces, la transmisión volvió a comenzar."
ENV PYTHONUNBUFFERED=1 STUDIO_DATA_DIR=/data/projects
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
