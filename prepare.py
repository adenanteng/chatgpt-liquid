from pathlib import Path
import json,struct,hashlib,shutil,re,subprocess,os
base=Path(__file__).resolve().parent
source=Path('/usr/lib/chatgpt')
app=Path.home()/'.local/share/chatgpt-liquid-glass/26.1013.40934/app-theme-aware'
archive=source/'resources/app.asar'
for proc in Path('/proc').glob('[0-9]*'):
    try: executable=os.readlink(proc/'exe')
    except OSError: continue
    if executable==str(app/'ChatGPT'):
        raise SystemExit('Quit the local glass copy before rebuilding it.')
with archive.open('rb') as f:
    a,b,c,d=struct.unpack('<4I',f.read(16))
    assert a==4 and d<b<20_000_000,'Unexpected ASAR header'
    tree=json.loads(f.read(d));data_start=8+b

def entries(node,prefix=''):
    for name,value in node.get('files',{}).items():
        if 'files' in value:yield from entries(value,prefix+name+'/')
        else:yield prefix+name,value
files=dict(entries(tree))
def read(name):
    n=files[name]
    with archive.open('rb') as f:
        f.seek(data_start+int(n['offset']));return f.read(n['size'])
pkg=json.loads(read('package.json'))
assert pkg['version']=='26.1013.40934','Untested ChatGPT version; original installation remains unchanged'
main_name='.vite/build/main-CLu1A25j.js'
raw=read(main_name).decode()
old='n===`win32`||n===`linux`?{titleBarStyle:`hidden`,titleBarOverlay:A9(r)}'
new='n===`win32`||n===`linux`?{titleBarStyle:`hidden`,titleBarOverlay:A9(r),...n===`linux`?{transparent:!0,backgroundColor:`#00000000`}:{}}'
assert raw.count(old)==1,'Window constructor changed'
raw=raw.replace(old,new)
old='shouldAlwaysUseOpaqueWindowSurface(e){return'
new='shouldAlwaysUseOpaqueWindowSurface(e){if(process.platform===`linux`&&e===`primary`)return!1;return'
assert raw.count(old)==1,'Opaque-surface policy changed'
raw=raw.replace(old,new)
old='let B=z.webContents;'
css=(base/'glass.css').read_text()
new=old+'if(process.platform===`linux`&&d===`primary`)B.on(`did-finish-load`,()=>{B.insertCSS('+json.dumps(css)+',{cssOrigin:`user`}).catch(e=>console.error(`[local-glass] CSS injection failed`,e));});'
assert raw.count(old)==1,'Window loading hook changed'
raw=raw.replace(old,new)
subprocess.run(['node','--check','--input-type=module'],input=raw,text=True,check=True)
mods={main_name:raw.encode()}
app.parent.mkdir(parents=True,exist_ok=True)
if not app.exists():shutil.copytree(source,app,ignore=lambda directory,names:['app.asar'] if Path(directory)==source/'resources' else [])
packed=sorted(((name,n,int(n['offset'])) for name,n in files.items() if 'offset' in n),key=lambda item:item[2])
old_offsets={name:offset for name,n,offset in packed}
new_offset=0
for name,n,offset in packed:
    data=mods.get(name)
    if data is not None:
        n['size']=len(data)
        if 'integrity' in n:
            integ=n['integrity'];assert integ['algorithm']=='SHA256'
            block=integ['blockSize'];integ['hash']=hashlib.sha256(data).hexdigest()
            integ['blocks']=[hashlib.sha256(data[i:i+block]).hexdigest() for i in range(0,len(data),block)]
    n['offset']=str(new_offset);new_offset+=n['size']
header=json.dumps(tree,separators=(',',':'),ensure_ascii=False).encode()
padding=b'\0'*((-len(header))%4)
pickle=struct.pack('<II',4+len(header)+len(padding),len(header))+header+padding
out=app/'resources/app.asar';temp=out.with_suffix('.asar.tmp')
with archive.open('rb') as src,temp.open('wb') as dst:
    dst.write(struct.pack('<II',4,len(pickle)));dst.write(pickle)
    for name,n,offset in packed:
        if name in mods:dst.write(mods[name])
        else:
            src.seek(data_start+offset);remaining=n['size']
            while remaining:
                chunk=src.read(min(remaining,4*1024*1024));assert chunk,'Unexpected EOF'
                dst.write(chunk);remaining-=len(chunk)
temp.replace(out)
with out.open('rb') as f:
    aa,bb,cc,dd=struct.unpack('<4I',f.read(16));assert aa==4
    check=json.loads(f.read(dd));offset_start=8+bb
    n=dict(entries(check))[main_name];f.seek(offset_start+int(n['offset']));patched=f.read(n['size'])
    assert patched==mods[main_name]
    assert hashlib.sha256(patched).hexdigest()==n['integrity']['hash']
    assert f.seek(0,2)==offset_start+new_offset
(app.parent/'build-info.json').write_text(json.dumps({'version':pkg['version'],'original_asar_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'patched_asar_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'modified_files':list(mods)},indent=2)+'\n')
print('Prepared isolated app:',app)
print('JS syntax and ASAR integrity self-checks passed; original installation unchanged.')
