from pathlib import Path
import json,struct,subprocess

def read(archive,name):
 with archive.open('rb') as f:
  _,b,_,d=struct.unpack('<4I',f.read(16));n=json.loads(f.read(d))
  for part in name.split('/'):n=n['files'][part]
  f.seek(8+b+int(n['offset']));return f.read(n['size']).decode()
base=Path.home()/'.local/share'
s=read(base/'chatgpt-liquid-glass/26.1111.21308/app-theme-aware/resources/app.asar','.vite/build/early-bootstrap-226-2f6bd181558008cf.js')
a=s.index('O=new eZ.BrowserWindow({...M');b=s.index(';',a)
constructor=s[a:b]+';'
a=s.index('let j=O.webContents;');b=s.index('O.webContents.once("did-finish-load"',a)
hook=s[a:b]
a=s.index('shouldAlwaysUseOpaqueWindowSurface(e){');b=s.index('applyWindowBackdrop(e,t,r){',a)
method=s[a:b]
js='''const {EventEmitter}=require('node:events');const assert=require('node:assert/strict');
function create(u){let O;const M={backgroundColor:'#ffffff'},writes=[];const eZ={BrowserWindow:class{constructor(options){this.options=options;this.webContents=new EventEmitter();this.webContents.insertCSS=(css)=>{writes.push(css);return Promise.resolve('key')};}}};
'''+constructor+hook+'''
O.webContents.emit('did-finish-load');return {F:O,writes};}
const main=create('primary'),other=create('secondary');assert.equal(main.F.options.transparent,true);assert.equal(main.F.options.backgroundColor,'#00000000');assert.equal(main.writes.length,1);assert.equal(other.F.options.transparent,undefined);assert.equal(other.writes.length,0);
class Policy{'''+method+'''}assert.equal(new Policy().shouldAlwaysUseOpaqueWindowSurface('primary'),false);
console.log('ChatGPT main-only native window + CSS hook smoke check passed.');'''
subprocess.run(['node'],input=js,text=True,check=True)
