from pathlib import Path
p = Path("/app/app.py")
source = p.read_text()
needle = '    password = os.environ.get("STUDIO_PASSWORD", "")'
replacement = '    if request.url.path == "/api/health":\n        return await call_next(request)\n' + needle
if needle not in source: raise RuntimeError("No compatible health middleware found")
p.write_text(source.replace(needle, replacement, 1))
