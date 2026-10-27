from pathlib import Path
import hashlib,json,shutil,subprocess
state=Path.home()/'.local/state/chatgpt-liquid-glass/install-state.json'
if not state.exists():raise SystemExit('No local glass launcher installation is recorded.')
info=json.loads(state.read_text())
for item in info['files']:
    path=Path(item['path'])
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()!=item['installed_sha256']:
        raise SystemExit('Launcher changed after installation; refusing to overwrite: '+str(path))
for item in info['files']:
    path=Path(item['path'])
    if item['backup']:shutil.copy2(item['backup'],path)
    else:path.unlink(missing_ok=True)
subprocess.run(['update-desktop-database',str(Path.home()/'.local/share/applications')],check=False)
state.rename(state.with_name('install-state.restored.json'))
print('Original ChatGPT launcher restored. Quit ChatGPT fully and reopen it; your profile and conversations were not moved.')
