# ASAR and UI inspection laboratory

This guide recreates the investigation method without the original workstation's scratch files or agent tooling. Production code lives in the repository root. Everything created below is a **temporary local diagnostic artifact**, not an additional installed service or shipped debugger.

Read [ARCHITECTURE.md](ARCHITECTURE.md) for native semantics and [MAINTAINER.md](MAINTAINER.md) before installing anything. Commands assume Bash and the repository root. Do not run them with sudo or Python optimization.

## 1. Start read-only

Record the package version, source archive SHA-256, Git status, active executable, current launcher, and installation record. Do not print profiles or conversation contents. Keep extracted application code outside Git and do not attach it to public issues.

A version label is insufficient: distro rebuilds can change the archive without changing the internal application version. The source checksum is a compatibility boundary, not a value to replace merely because a guard failed.

## 2. Recreate a minimal ASAR inspector

The following standard-library script reads the inspected pickle-prefixed ASAR layout. It lists packed JavaScript/CSS bundle names, reports package identity/main, or extracts **one explicitly named packed file to one explicitly chosen output**. It refuses links and unpacked entries; those need separate inspection of the package's `app.asar.unpacked` directory. This is not a general ASAR implementation.

```bash
export LIQUID_TRIAL_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/liquid-inspection.XXXXXX")"
cat > "$LIQUID_TRIAL_ROOT/inspect-asar.py" <<'PYCODE'
from pathlib import Path
import argparse
import hashlib
import json
import struct

parser = argparse.ArgumentParser()
parser.add_argument('archive', type=Path)
parser.add_argument('--list', action='store_true')
parser.add_argument('--extract')
parser.add_argument('--out', type=Path)
args = parser.parse_args()
if bool(args.extract) != bool(args.out):
    parser.error('--extract and --out must be supplied together')

archive_size = args.archive.stat().st_size
with args.archive.open('rb') as stream:
    prefix = stream.read(16)
    if len(prefix) != 16:
        raise SystemExit('Truncated ASAR header')
    marker, header_size, pickle_size, json_size = struct.unpack('<4I', prefix)
    if not (marker == 4 and header_size == pickle_size + 4
            and 0 < json_size < header_size < 20_000_000
            and 16 + json_size <= 8 + header_size <= archive_size):
        raise SystemExit('Unexpected ASAR header; inspect the new format')
    tree = json.loads(stream.read(json_size))
data_start = 8 + header_size

def entries(node, prefix=''):
    for name, entry in node.get('files', {}).items():
        path = prefix + name
        if 'files' in entry:
            yield from entries(entry, path + '/')
        else:
            yield path, entry

files = dict(entries(tree))

def read_packed(name):
    entry = files[name]
    if 'link' in entry or entry.get('unpacked') or 'offset' not in entry:
        raise SystemExit('Not a packed regular file: ' + name)
    offset, size = int(entry['offset']), int(entry['size'])
    if offset < 0 or size < 0 or data_start + offset + size > archive_size:
        raise SystemExit('Packed file lies outside the archive: ' + name)
    with args.archive.open('rb') as stream:
        stream.seek(data_start + offset)
        payload = stream.read(size)
    if len(payload) != size:
        raise SystemExit('Truncated packed file: ' + name)
    return payload

with args.archive.open('rb') as stream:
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        digest.update(chunk)
package = json.loads(read_packed('package.json'))
print(json.dumps({'sha256': digest.hexdigest(), 'name': package.get('name'),
                  'version': package.get('version'), 'main': package.get('main'),
                  'entries': len(files), 'data_start': data_start}, indent=2))
if args.list:
    for name in sorted(files):
        if name.endswith(('.js', '.cjs', '.mjs', '.css')):
            print(name)
if args.extract:
    payload = read_packed(args.extract)
    with args.out.open('xb') as stream:
        stream.write(payload)
    print('Extracted', args.extract, 'to', args.out)
PYCODE
python3 "$LIQUID_TRIAL_ROOT/inspect-asar.py" /usr/lib/chatgpt/resources/app.asar --list
```

Extract the currently supported native bundle:

```bash
python3 "$LIQUID_TRIAL_ROOT/inspect-asar.py" \
  /usr/lib/chatgpt/resources/app.asar \
  --extract '.vite/build/early-bootstrap-226-2f6bd181558008cf.js' \
  --out "$LIQUID_TRIAL_ROOT/native.js"
```

For a newer package, inspect the reported main entry and its imports first. The old hashed bundle name may no longer exist. Extract the actual file named by that chain; do not assume the largest chunk owns native windows.

Search local extracted code by behavior:

```bash
rg -o 'BrowserWindow|WebContentsView|setBackgroundColor|did-finish-load|insertCSS|sandbox|contextIsolation|nodeIntegration|shouldAlwaysUseOpaqueWindowSurface' "$LIQUID_TRIAL_ROOT/native.js"
```

Minified files often occupy one enormous line. Avoid printing an entire matching line. This bounded-context recipe reports at most two snippets per token:

```bash
python3 - "$LIQUID_TRIAL_ROOT/native.js" <<'PYCODE'
from pathlib import Path
import sys
source = Path(sys.argv[1]).read_text()
for token in ('BrowserWindow', 'WebContentsView', 'setBackgroundColor',
              'did-finish-load', 'shouldAlwaysUseOpaqueWindowSurface'):
    cursor = 0
    for number in range(2):
        index = source.find(token, cursor)
        if index < 0:
            break
        print('\nTOKEN', token, 'OFFSET', index)
        print(source[max(0, index - 180):index + 320])
        cursor = index + len(token)
PYCODE
```

Read enough surrounding code to understand options, scope, registration, theme changes, and lifetime. Bounded snippets are a navigation aid, not a substitute for that review. Keep proprietary excerpts local; public documentation should explain semantics and narrow anchors rather than redistributing bundles.

## 3. Native-port checklist

1. Trace the primary appearance identifier through the original BrowserWindow options.
2. Verify the Linux-primary transparent constructor override and forced-opaque-surface policy together.
3. Preserve secondary-window behavior; inject user CSS only into primary contents after loading.
4. Read original lifecycle/security/preload behavior around the hook and leave it intact.
5. Update `check-window.py` for the actual constructor, loading hook, and policy method in the new bundle.

After adapting exact anchors, use normal `prepare.py` and `check-window.py`; the latter must extract the new code rather than execute a stale hand-written approximation. Keep source hash/version assertions and one-match checks. Unknown syntax, changed ASAR integrity, or changed runtime resources require inspection, not a bypass.

## 4. Diagnose a CSS issue without reading conversations

Try the HTML theme fixture first. If the real application differs, inspect only necessary structural metadata. An opaque rectangle may be painted by an ancestor, sibling, sticky element, mask, gradient, pseudo-element, SVG, or a different renderer document. A transparent clicked element alone does not prove its surroundings are transparent.

The expression below returns tags, structural class names, rectangles, color/opacity and mask/background categories around the bottom-center composer. It deliberately excludes text, form values, URLs, cookies, storage, requests, and account identifiers. Background image URLs are classified rather than returned. Review class names locally before sharing diagnostic output.

Save as `$LIQUID_TRIAL_ROOT/evaluate.js`:

```javascript
(() => {
  const x = Math.round(innerWidth * 0.5);
  const y = Math.max(0, innerHeight - 60);
  const records = [];
  const seen = new Set();
  const category = value => {
    if (!value || value === "none") return "none";
    return value.includes("gradient(") ? "gradient" : "image-or-other";
  };
  function add(element, reason) {
    if (!element || seen.has(element) || records.length >= 100) return;
    seen.add(element);
    const style = getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    const pseudo = name => {
      const item = getComputedStyle(element, name);
      return {background: item.backgroundColor,
              image: category(item.backgroundImage),
              opacity: item.opacity,
              mask: category(item.maskImage)};
    };
    records.push({reason, tag: element.tagName,
      classes: typeof element.className === "string"
        ? element.className.slice(0, 240) : "",
      bounds: [rect.x, rect.y, rect.width, rect.height].map(Math.round),
      background: style.backgroundColor, image: category(style.backgroundImage),
      opacity: style.opacity, position: style.position,
      pointerEvents: style.pointerEvents, mask: category(style.maskImage),
      before: pseudo("::before"), after: pseudo("::after")});
  }
  for (const element of document.elementsFromPoint(x, y)) {
    for (let ancestor = element; ancestor; ancestor = ancestor.parentElement) {
      add(ancestor, "hit-or-ancestor");
    }
  }
  // Hit testing omits pointer-events:none backplates: inspect geometry too.
  for (const element of document.querySelectorAll("body *")) {
    const rect = element.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0
        && rect.left <= x && rect.right >= x
        && rect.top <= y && rect.bottom >= y) add(element, "geometry-overlap");
    if (records.length >= 100) break;
  }
  return {viewport: [innerWidth, innerHeight], point: [x, y], records};
})()
```

This point-based probe is intentionally bounded. Adjust the point to the problematic region, and narrow the traversal for a very large document. It does not enumerate another embedded renderer automatically. Never substitute a full `outerHTML`, `textContent`, conversation export, or profile dump.

## 5. Optional temporary native probe

Use this only when fixtures cannot explain a real-view bug. It is **not installed by the project**. It samples one selected renderer once per second for at most 60 ticks and overwrites one private JSON file. No debugger port is needed. Full DOM traversal can cause overhead; stop the trial when evidence is sufficient.

Save this complete helper as `$LIQUID_TRIAL_ROOT/probe-main.js`:

```javascript
function sampleLiquidStructure(webContents) {
  if (process.platform !== "linux"
      || !process.env.LIQUID_PROBE_FILE
      || !process.env.LIQUID_PROBE_OUTPUT) return;
  let remaining = 60;
  let busy = false;
  const timer = setInterval(async () => {
    if (--remaining <= 0) clearInterval(timer);
    if (busy || webContents.isDestroyed()) return;
    busy = true;
    try {
      const fs = await import("node:fs");
      const expression = fs.readFileSync(process.env.LIQUID_PROBE_FILE, "utf8");
      const metadata = await webContents.executeJavaScript(expression);
      fs.writeFileSync(process.env.LIQUID_PROBE_OUTPUT,
        JSON.stringify(metadata, null, 2), {mode: 0o600});
    } catch {
      // A loading/destroyed document can be unavailable during a sample.
    } finally {
      busy = false;
    }
  }, 1000);
  webContents.once("destroyed", () => clearInterval(timer));
}
```

Create a scratch preparer from the **currently reviewed** production patcher. The following command copies only preparation code/styles, redirects the runtime, adds the diagnostic helper after normal patch construction, and runs another syntax check. It does not edit production files or launch an application:

```bash
python3 - <<'PYCODE'
from pathlib import Path
import os
import re
import shutil

repo = Path.cwd()
trial = Path(os.environ['LIQUID_TRIAL_ROOT']).resolve()
if trial == repo or repo in trial.parents:
    raise SystemExit('Use a private temporary directory outside the repository')
source = (repo / 'prepare.py').read_text()
source, count = re.subn(r'^app=.+$',
    "app=Path(os.environ['LIQUID_TRIAL_ROOT'])/'runtime/app-theme-aware'",
    source, flags=re.M)
assert count == 1, 'Review changed runtime-path assignment'
anchor = 'mods={main_name:raw.encode()}'
assert source.count(anchor) == 1, 'Review changed build layout'
instrumentation = '''
probe_function=(base/'probe-main.js').read_text()
probe_anchor='let j=O.webContents;'
assert raw.count(probe_anchor)==1, 'Review diagnostic target'
raw=raw.replace(probe_anchor,probe_function+'\\n'+probe_anchor+'if(process.platform==="linux"&&u==="primary")sampleLiquidStructure(j);')
subprocess.run(['node', '--check', '--input-type=module'],input=raw,text=True,check=True)
'''
source = source.replace(anchor, instrumentation + '\n' + anchor)
(trial / 'prepare-trial.py').write_text(source)
for name in ['glass.css']:
    shutil.copy2(repo / name, trial / name)
print('Created scratch preparer:', trial / 'prepare-trial.py')
PYCODE
python3 "$LIQUID_TRIAL_ROOT/prepare-trial.py"
```

This recipe deliberately checks its own anchor counts. If production code changed, reinspect and adapt it. Do not loosen the assertions or redirect it to the production runtime to make it run. The scratch build metadata contains diagnostic code and must never be used by `install.py`.

Before a trial launch, fully quit the normal application through its UI and verify the actual executable/process state. The trial uses the normal application code and can use its **real profile**: temporary executable placement does not isolate accounts or single-instance locks. Do not run both copies together. If the current app hosts the maintenance conversation, hand off the restart to the user.

The optional launch command is:

```bash
LIQUID_PROBE_FILE="$LIQUID_TRIAL_ROOT/evaluate.js" \
LIQUID_PROBE_OUTPUT="$LIQUID_TRIAL_ROOT/structure.json" \
  "$LIQUID_TRIAL_ROOT/runtime/app-theme-aware/ChatGPT"
```

ChatGPT currently uses the tested XWayland setup. Do not silently combine a renderer patch with an untested backend migration. Launching a second instance can forward into an existing stock window instead of running the trial.

Open the affected UI state yourself or ask the user to select it. Do not send messages to test a visual patch. Inspect only `structure.json`; do not collect conversation contents. If multiple selected views exist, this simple probe overwrites the same output, so reduce the hook to the specific affected renderer before drawing conclusions.

For a temporary visual preview, use an inspected narrow `insertCSS` override on the same selected renderer. Track its style key for removal, or close the trial. A live preview is evidence, not a permanent patch: put the final selector into the appropriate source stylesheet, add a fixture case, and rebuild the clean production runtime after quitting the trial.

## 6. Diagnostic removal and production verification

1. Quit the diagnostic copy and verify its main/child processes have exited from the correct process namespace.
2. Keep sanitized findings and exact reproduction steps; extracted source/JSON stay private.
3. Modify the normal source stylesheet/native hooks, not the scratch preparer. Add the relevant regression case.
4. Run normal preparation into the stopped production target, plus theme/native checks and installer checks if relevant.
5. Inspect the modified production bundle for accidental `sampleLiquidStructure`, `LIQUID_PROBE_FILE`, `LIQUID_PROBE_OUTPUT`, temporary evaluation paths, and debugging flags. There must be no diagnostic hook or endpoint.
6. Reopen the normal guarded launcher, verify the actual executable and affected UI, and record what remains unchecked.
7. Remove the temporary directory only after confirming no running process uses it. Do not delete a profile, production runtime, or backup as part of diagnostic cleanup.

Do not enable remote debugging or weaken the app's own debugger protection as a shortcut. A temporary native hook in a private copied runtime preserves the production security policy; shipping it would violate the project contract.

## 7. Tools used during development, and what must survive

| Tool / artifact | Purpose | Long-term dependency? |
| --- | --- | --- |
| `prepare.py`, launcher, installer, rollback | Permanent guarded integration | Yes; version-specific source lives here |
| Theme/native/installer fixtures available in this repo | Repeatable regression evidence | Yes; keep synchronized with real patch code |
| Read-only ASAR header/entry inspector | Find package main, hashes, bundles, exact native snippets | No original scratch file needed; recreate with this guide |
| Temporary copied runtime and bounded native DOM probe | Diagnose computed structural fills in actual UI states | No; private, stopped and removed after diagnosis |
| Temporary style preview | Confirm a selector fixes the visible layer before rebuilding | No; final CSS belongs in the tracked stylesheet |
| OS process/executable checks | Distinguish stock, patched, and trial instance; avoid replacing active runtime | Standard platform tools |
| Local screenshots or metadata JSON | Human confirmation of a specific view | No; inspect/redact privately, never assume public-safe |

Earlier workstation directories named `work/app-update-20261104`, `work/app-update-20261115`, and app-specific glass/update trials held inventory scripts, snippets, probes, and temporary copies. None is a runtime dependency, canonical source, or required public artifact. The repeatable source, contracts, test commands, and reconstruction recipes are in this repository.

## 8. Common investigation mistakes

- Treating a mismatched source hash as an inconvenience rather than unknown code.
- Reusing minified identifiers from the previous release, or testing a hand-written replacement rather than the code embedded in ASAR.
- Checking only ancestors and missing a sticky sibling or a `pointer-events: none` pseudo/backplate.
- Looking only at a new conversation while the bug exists only in older conversation state.
- Painting two translucent bases, then increasing transparency globally to compensate.
- Assuming the trial is isolated because a profile environment variable or Chromium flag was supplied. Verify the app's actual user-data path and single-instance behavior first.
- Inspecting processes from a namespace that cannot see the user's desktop and incorrectly assuming the app exited.
- Rebuilding a copied runtime with stale non-ASAR resources after a partial or same-version different-fingerprint preparation.
- Claiming a headless fixture, mapped window, or user confirmation from an older version proves every current view.

Return to the [maintainer workflow](MAINTAINER.md) for installation and recovery. Record precise evidence and keep production free of investigation code.
