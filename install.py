from pathlib import Path
import hashlib,json,shutil,datetime,subprocess
base=Path(__file__).resolve().parent
home=Path.home();data=home/'.local/share/chatgpt-liquid-glass';state=home/'.local/state/chatgpt-liquid-glass'
info=json.loads((data/'26.1029.61003/build-info.json').read_text())
assert hashlib.sha256(Path('/usr/lib/chatgpt/resources/app.asar').read_bytes()).hexdigest()==info['original_asar_sha256'],'Installed ChatGPT changed; do not install this launcher.'
assert not (state/'install-state.json').exists(),'Local launcher is already installed; inspect it before reinstalling.'
backup=state/'backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True)
stock=Path('/usr/share/applications/chatgpt.desktop').read_text()
lines=stock.splitlines();assert sum(line.startswith('Exec=') for line in lines)==1
entry='\n'.join('Exec='+str(home/'.local/bin/chatgpt-liquid-glass')+' %U' if line.startswith('Exec=') else line for line in lines)+'\n'
files=[(home/'.local/bin/chatgpt-liquid-glass',(base/'launch.sh').read_bytes(),0o755),(home/'.local/share/applications/chatgpt.desktop',entry.encode(),0o644),(home/'.local/bin/chatgpt-liquid-glass-rollback',(base/'rollback.sh').read_bytes(),0o755)]
records=[]
for path,content,mode in files:
 old=None
 if path.exists():old=backup/path.name;shutil.copy2(path,old)
 records.append({'path':str(path),'backup':str(old) if old else None,'installed_sha256':hashlib.sha256(content).hexdigest()})
try:
 for path,content,mode in files:
  path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_name(path.name+'.glass-tmp');temp.write_bytes(content);temp.chmod(mode);temp.replace(path)
 shutil.copy2(base/'rollback.py',data/'rollback.py')
 (state/'install-state.json').write_text(json.dumps({'files':records,'version':info['version']},indent=2)+'\n')
except BaseException:
 for item in records:
  path=Path(item['path'])
  if item['backup']:shutil.copy2(item['backup'],path)
  else:path.unlink(missing_ok=True)
 raise
subprocess.run(['update-desktop-database',str(home/'.local/share/applications')],check=False)
print('Local ChatGPT glass launcher installed. Original package and running session unchanged.')
print('Rollback:',home/'.local/bin/chatgpt-liquid-glass-rollback')
print('Backup:',backup)
