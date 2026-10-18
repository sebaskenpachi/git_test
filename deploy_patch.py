"""Extensión de la interfaz para abrir el proyecto Voynich ya preparado."""
from pathlib import Path
app = Path("/app/app.py")
s = app.read_text("utf-8")
check = '    password = os.environ.get("STUDIO_PASSWORD", "")'
allow = '    if request.url.path == "/api/health":\n        return await call_next(request)\n'
if allow not in s:
    if check not in s: raise RuntimeError("Middleware not found")
    s=s.replace(check,allow+check,1)
extra = '''
@app.get("/api/studio/voynich")
def get_voynich():
    import hashlib
    identifier = hashlib.sha256(b"notodoencaja-voynich-pilot-01").hexdigest()[:32]
    return read_manifest(identifier)

'''
if '@app.get("/api/studio/voynich")' not in s:
    s += '\n' + extra
app.write_text(s, "utf-8")
html=Path("/app/static/index.html")
h=html.read_text("utf-8")
if 'id="loadVoynich"' not in h:
    h=h.replace('<button class="btn ghost" id="loadDemo">', '<button class="btn ghost" id="loadVoynich">✦ Piloto Voynich</button><button class="btn ghost" id="loadDemo">',1)
html.write_text(h,"utf-8")
js=Path("/app/static/app.js")
t=js.read_text("utf-8")
inject = """
  async function openVoynich() {
    const doc = await api('/api/studio/voynich');
    if(!doc.storyboard || !doc.storyboard.length) throw new Error('El piloto se está preparando. Intenta de nuevo en un minuto.');
    if(state.playing) pause();
    state.projectId=doc.id;
    state.assets=doc.assets||[];
    state.selected=0;
    state.currentPreviewIndex=-1;
    state.currentTime=0;
    restoreSettings({scenes:doc.storyboard, audioId:doc.audio_id,
                     resolution:'720p',transition:'cut',autoSync:true});
    bindAudio(); persist(); paint();
    toast('Piloto Voynich cargado: '+doc.storyboard.length+' escenas diferentes.');
  }
"""
if 'async function openVoynich()' not in t:
    marker='  function bindEvents() {'
    if marker not in t: raise RuntimeError('JS marker missing')
    t=t.replace(marker,inject+'\n'+marker,1)
    marker2="    $('loadDemo').addEventListener('click',async()=>"
    replacement="""    $('loadVoynich').addEventListener('click',async()=>{try{await openVoynich();}catch(e){toast(e.message,true);}});
"""
    if marker2 not in t: raise RuntimeError('loadDemo marker missing')
    t=t.replace(marker2,replacement+marker2,1)
    marker3='    bindEvents();\n    try {'
    if marker3 not in t: raise RuntimeError('init marker missing')
    t=t.replace(marker3,"""    bindEvents();
    if(new URLSearchParams(location.search).get('project') === 'voynich'){
      try { await openVoynich(); return; } catch(e) { toast('Piloto preparándose: '+e.message,true); }
    }
    try {""",1)
js.write_text(t,"utf-8")
