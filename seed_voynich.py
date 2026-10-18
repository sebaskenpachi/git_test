"""Inicializa el primer proyecto Voynich en el volumen persistente.
Las imágenes son folios públicos (Beinecke/Yale, servidos por Wikimedia Commons).
Si una descarga falla, emplea gráficos abstractos, nunca páginas falsas.
La voz ESpeak es PROVISIONAL y se reemplazará por el MP3 de Revoicer.
"""
from __future__ import annotations
import hashlib, io, json, os, random, subprocess, sys, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from renderer import RenderScene, render_video, probe_duration

STORE = Path(os.environ.get("STUDIO_DATA_DIR", "/data/projects"))
PILOT_ID = hashlib.sha256(b"notodoencaja-voynich-pilot-01").hexdigest()[:32]
ROOT = STORE / PILOT_ID
IMAGES = ROOT / "assets"
OUTPUTS = ROOT / "exports"
MANIFEST = ROOT / "manifest.json"
PAGES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 36, 48, 75, 100, 145, 175]
SCENE_NAMES = [
    "01 · El libro", "02 · Primera página", "03 · La escritura",
    "04 · Un extraño alfabeto", "05 · Botánica", "06 · Plantas imposibles",
    "07 · Detalle de las ilustraciones", "08 · Una colección de símbolos",
    "09 · Líneas repetidas", "10 · Dibujo y palabra",
    "11 · Nuevos indicios", "12 · La pregunta",
    "13 · Patrones", "14 · Hipótesis", "15 · Lo que sabemos",
    "16 · El misterio permanece",
]
NARRATION = (
    "Mira esta página. Parece un manuscrito medieval, pero nadie ha demostrado "
    "una traducción aceptada de sus palabras. Es el manuscrito Voynich. "
    "Sus folios contienen plantas extrañas, figuras y diagramas, acompañados "
    "por una escritura que se repite siguiendo patrones difíciles de explicar. "
    "El pergamino ha sido estudiado y su antigüedad puede investigarse. "
    "Eso no significa que conozcamos el significado de sus signos. "
    "Hay hipótesis sobre lenguas desconocidas, códigos e incluso textos sin mensaje. "
    "Sin embargo, ninguna explicación ha logrado convencer a los especialistas. "
    "La verdadera pregunta no es solo qué podría decir el libro. "
    "Es cómo reconoceríamos una traducción auténtica, si algún día apareciera. "
    "En No Todo Encaja comenzamos por mirar las pruebas."
)
MOTIONS = ["zoom_in", "pan_right", "zoom_out", "pan_left"]

def log(*items):
    print("[VOYNICH SEED]", *items, flush=True)

def save(data):
    tmp = MANIFEST.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(MANIFEST)

def fetch_page(number):
    address = "https://commons.wikimedia.org/wiki/Special:FilePath/Voynich_Manuscript_(" + str(number) + ").jpg?width=1200"
    req = urllib.request.Request(address, headers={
        "User-Agent": "NoTodoEncajaStudio/0.2 (documentary production; source Wikimedia Commons)",
        "Accept": "image/avif,image/webp,image/png,image/jpeg,image/*"
    })
    try:
        with urllib.request.urlopen(req, timeout=13) as r:
            raw = r.read(9 * 1024 * 1024)
        image = Image.open(io.BytesIO(raw)).convert("RGB")
        if min(image.size) < 300: return None
        return image
    except Exception as exc:
        log("Folio", number, "sin descarga:", type(exc).__name__, str(exc)[:100])
        return None

def create_frame(index, folio, source):
    random.seed(70123 + index)
    W,H = 1280,720
    bg = Image.new("RGB", (W,H), (8 + index % 4, 17 + index % 3, 26 + index % 7))
    d = ImageDraw.Draw(bg)
    for j in range(0, W, 4):
        level = int(j / W * (8 + index % 9))
        d.line((j,0,j,H), fill=(7+level,17+level,28+level))
    accent = [(153,119,72),(70,120,133),(124,87,108),(121,139,95)][index%4]
    for j in range(12):
        yy = 36 + j * 56
        shift = ((index*53 + j*31) % 140)
        d.line((40+shift, yy, 385 + shift, yy + (index%5-2)*8), fill=tuple(c//3 for c in accent), width=1)
    if source is not None:
        folio = source.copy()
        folio.thumbnail((730,650),Image.Resampling.LANCZOS)
        # La posición cambia para evitar la repetición de encuadre.
        cx = [465,575,650,510,590][index%5]
        x,y = cx - folio.width//2, (H-folio.height)//2
        d.rectangle((x-12,y-12,x+folio.width+12,y+folio.height+12),
                    fill=(27,27,26),outline=accent,width=2)
        bg.paste(folio,(x,y))
    else:
        # Fondo científico abstracto; NO representa un folio auténtico.
        center = (W//2 + (index%3-1)*80,H//2)
        for j in range(20):
            rr = 30 + 14*j
            theta = (j*19 + 17*index) * 0.0174533
            import math
            xx = center[0] + int(rr*math.cos(theta))
            yy = center[1] + int(rr*math.sin(theta))
            d.ellipse((xx-9,yy-9,xx+9,yy+9),outline=accent,width=2)
            if j:
                d.line((xx,yy,center[0],center[1]),fill=tuple(c//2 for c in accent),width=2)
        d.ellipse((center[0]-140,center[1]-140,center[0]+140,center[1]+140),outline=accent,width=3)
    # Añadir geometría editorial fuera del folio: NO son subtítulos.
    for j in range(5):
        x0 = 65+(index*71+j*83)%220
        y0 = 90+j*117
        d.ellipse((x0,y0,x0+6+j%3*2,y0+6+j%3*2),fill=accent)
    d.line((48,52,320,52),fill=accent,width=3)
    d.line((960,660,1230,660),fill=accent,width=3)
    return bg

def main():
    if os.environ.get("NTE_SEED_VOYNICH", "1") != "1": return
    IMAGES.mkdir(parents=True,exist_ok=True)
    OUTPUTS.mkdir(parents=True,exist_ok=True)
    if MANIFEST.exists():
        try:
            previous = json.loads(MANIFEST.read_text("utf-8"))
            if previous.get("status") in ("ready","rendered") and len(previous.get("storyboard",[]))>=12:
                log("Proyecto ya creado:", PILOT_ID, "estado", previous.get("status"))
                if previous.get("status")=="rendered": return
                data=previous
            else: data=None
        except Exception: data=None
    else: data=None
    if data is None:
        data = {"id":PILOT_ID,"name":"El manuscrito Voynich · Piloto 01",
                "created":datetime.now(timezone.utc).isoformat(),"assets":[],
                "storyboard":[],"audio_id":None,"status":"preparing",
                "description":"16 encuadres originales de folios auténticos cuando están disponibles; voz ESpeak de prueba. Sin subtítulos incrustados.",
                "source":"Beinecke Rare Book & Manuscript Library (Yale University) · reproducciones Wikimedia Commons"}
        save(data)
        log("Iniciando 16 composiciones distintas")
        for i, folio_num in enumerate(PAGES):
            page=fetch_page(folio_num)
            shot=create_frame(i,folio_num,page)
            key=hashlib.md5(("voynich-frame-"+str(i)).encode()).hexdigest()
            fname=key+".jpg"
            shot.save(IMAGES/fname,quality=86,optimize=True)
            from app import visual_fingerprint
            sig=visual_fingerprint(shot)
            record={"id":key,"kind":"image","name":SCENE_NAMES[i]+(" · folio real" if page else " · gráfica original"),
                    "url":f"/api/projects/{PILOT_ID}/assets/{key}",
                    "duration":None,"fingerprint":sig}
            data["assets"].append(record)
            data["storyboard"].append({"asset_id":key,"title":SCENE_NAMES[i],
                                      "duration":3.0 if i%4 else 3.7,"motion":MOTIONS[i%4]})
            save(data)
            log("Escena", i+1, "/16", "folio" if page else "gráfica alternativa")
        audio_id=hashlib.md5(b"voynich-temporary-narration").hexdigest()
        audio=IMAGES/(audio_id+".wav")
        subprocess.run(["espeak","-v","es","-s","143","-a","165","-w",str(audio),NARRATION],
                       check=True,timeout=40)
        length=probe_duration(audio)
        data["audio_id"]=audio_id
        data["assets"].append({"id":audio_id,"kind":"audio",
                               "name":"VOZ PROVISIONAL · reemplazar por Revoicer",
                               "url":f"/api/projects/{PILOT_ID}/assets/{audio_id}",
                               "duration":round(length,2),"fingerprint":None})
        data["status"]="ready"
        save(data)
        log("Proyecto cargado",PILOT_ID,"segundos",round(length,2))
    dest=OUTPUTS/"documental_1a2b3c4d.mp4"
    if not dest.is_file():
        try:
            scene_objs=[RenderScene(image=IMAGES/(scene["asset_id"]+".jpg"),
                                    duration=scene["duration"],motion=scene["motion"])
                       for scene in data["storyboard"]]
            # Corte cinematográfico en la prueba para limitar RAM y cómputo.
            render_video(scenes=scene_objs,
                         audio=IMAGES/(data["audio_id"]+".wav"),
                         output=dest,resolution="720p",transition="cut",auto_sync=True,
                         progress=lambda p,st: log("Render",p,st))
            data["status"]="rendered"
            data["export_url"]=f"/api/projects/{PILOT_ID}/exports/{dest.name}"
            save(data)
            log("MP4 TERMINADO",data["export_url"])
        except Exception as exc:
            data["render_error"]=str(exc)[-500:]
            data["status"]="ready"
            save(data)
            log("Error de render:",str(exc)[-500:])
    else:
        data["status"]="rendered"
        data["export_url"]=f"/api/projects/{PILOT_ID}/exports/{dest.name}"
        save(data)

if __name__=="__main__":
    main()
