# Maintainer handoff: ChatGPT Liquid

**Reference date: 2026-11-15.** This is a continuation guide for a maintainer or agent without the original chat. It documents the inspected implementation, not universal compatibility with future packages.

## 1. Baseline and repository boundaries

| Item | Inspected value |
| --- | --- |
| Public repository | `https://github.com/adenanteng/chatgpt-liquid.git` |
| Branch | `main` |
| Pre-handoff maintenance commit | `45ccf1b` |
| Package | `chatgpt-bin 26.1111.21308-1` |
| Internal application version | `26.1111.21308` |
| System application | `/usr/lib/chatgpt/` |
| Stock executable | `/usr/lib/chatgpt/ChatGPT` |
| Patched bundle | `.vite/build/early-bootstrap-226-2f6bd181558008cf.js` |
| User-local runtime | `~/.local/share/chatgpt-liquid-glass/26.1111.21308/app-theme-aware/` |
| Desktop entry override | `~/.local/share/applications/chatgpt.desktop` |

Original `resources/app.asar` SHA-256:

```text
904779f81a2e952cdac544375835bb730c727c5c7b4d3b71028c81855ff6088a
```

The repository owns only integration scripts/styles/docs. System binaries, original application code, copied resources, account profiles, and build archives remain outside Git. [Hyprglass Liquid](https://github.com/adenanteng/hyprglass-liquid) owns optics; [dotfiles](https://github.com/adenanteng/dotfiles) owns the selected daily desktop configuration. Do not overwrite either as an incidental application patch.

## 2. First-session triage

```bash
git status --short --branch
git log -5 --oneline
pacman -Q chatgpt-bin
sha256sum /usr/lib/chatgpt/resources/app.asar
hyprctl hyprglass status
```

Read `prepare.py`, `launch.sh`, `install.py`, `rollback.py`, the styles, and tests. Compare installed launcher content and the installation record before changing them. A correct stock fallback after a package update is intentional, not proof that CSS was lost or that the compositor failed.

Do not dump profile/config directories or arbitrary process command lines. To identify active binaries without exposing arguments:

```bash
python3 - <<'PYCODE'
from pathlib import Path
import os
for proc in Path('/proc').glob('[0-9]*'):
    try:
        executable = os.readlink(proc / 'exe')
        command = (proc / 'cmdline').read_bytes()
        if executable.endswith('/ChatGPT') and b'--type=' not in command:
            print(proc.name, executable)
    except OSError:
        pass
PYCODE
```

Electron can rewrite argv into one combined string, so splitting on NUL and testing only `startswith('--type=')` previously misidentified child processes. Namespace/sandbox restrictions can also hide desktop processes; absence in the wrong context is not proof of termination.

## 3. Runtime and state files

| Path beneath the user home | Purpose |
| --- | --- |
| `.local/bin/chatgpt-liquid-glass` | Installed guarded launcher |
| `.local/bin/chatgpt-liquid-glass-rollback` | Small shell entry point to the installed Python rollback helper |
| `.local/share/chatgpt-liquid-glass/26.1111.21308/app-theme-aware/` | Complete copied runtime, including patched `resources/app.asar` |
| `.local/share/chatgpt-liquid-glass/26.1111.21308/build-info.json` | Version, source/patched archive SHA-256, modified bundle list |
| `.local/share/chatgpt-liquid-glass/rollback.py` | Installed recovery implementation |
| `.local/state/chatgpt-liquid-glass/install-state.json` | Destination paths, optional backup paths, installed checksums, installed version |
| `.local/state/chatgpt-liquid-glass/backups/` | Original launcher/desktop files and locally retained upgrade records |
| `.local/state/chatgpt-liquid-glass/install-state.restored.json` | Record renamed by a completed rollback |

Paths are conventional `$HOME/.local` paths, not general XDG-data/state abstractions. The stock application continues using its own normal profile; these scripts do not relocate or copy it. Absolute paths in local state are recovery data and must not be committed publicly.

## 4. Tool-by-tool contract

| Tool | Input | Output / side effects | Important guard or limit |
| --- | --- | --- | --- |
| `prepare.py` | Inspected stock ASAR and CSS beside the script | User-local runtime, rebuilt ASAR, `build-info.json` | Exact source hash/version/anchor count; copied runtime must be stopped |
| `launch.sh` | Runtime path, installed original archive hash, launch arguments | Exec patched runtime or stock launcher | Checks original package fingerprint and runtime existence, not the patched archive hash on every launch |
| `install.py` | Prepared build metadata and stock desktop entry | Launcher overrides, installed rollback helper, backup and installation record | Original source hash must match; existing active record stops reinstall |
| `rollback.py` | Installation record and backups | Restore/remove recorded overrides; rename record | Refuses changed existing launcher bytes; does not delete runtime or profile |
| `rollback.sh` | User home | Exec installed Python recovery helper | Stable command independent of repository checkout location |
| `check-theme.py` | Current stylesheet and generated local HTML | Disposable Chromium profile and computed-style assertions | Fixture, not the real application's entire DOM; Chrome path is hardcoded |
| `check-window.py` | Prepared runtime ASAR | Node execution of extracted patched functions with Electron stubs | Version/bundle/minified symbol names must be maintained with the patch |

### Preparation algorithm

1. Compute the stock archive SHA-256 and reject an unknown package before writing a runtime.
2. Refuse if an executable from this exact target runtime directory is still running.
3. Read the ASAR pickle header and recursive file table; verify the internal package version.
4. Read the exact main-process bundle and require each native/loading patch anchor exactly once.
5. Embed the CSS with JSON escaping and run Node syntax checking before writing the modified archive.
6. Copy the complete stock application only if that runtime directory does not exist, excluding the packed stock `app.asar` while retaining unpacked resources and native dependencies.
7. Iterate packed files in original offset order. Recompute modified entry size, SHA-256 and block hashes; assign new offsets to every packed entry.
8. Encode a padded JSON header and stream unmodified payload bytes from their original offsets. Write a temporary archive, then replace the target archive.
9. Read back the target bundle, verify its bytes/integrity and the final archive size; write build provenance.

This is a package-specific packer, not a universal ASAR library. It assumes the inspected header/file layout and integrity format. Changes to link/unpacked conventions, compression, encrypted code, or binary-embedded integrity requirements need renewed inspection. Recomputing ASAR metadata does not prove that every future Electron integrity mechanism is satisfied.

The guard does not make an arbitrary partially copied runtime complete. If initial preparation was interrupted, inspect/quarantine only that stopped, unreferenced target directory and build a fresh copy. Reusing an existing same-version directory does not refresh all unchanged binaries/resources. Never reuse it for a different original fingerprint.

### Launcher/installer/recovery behavior

The installer preserves desktop metadata and rewrites the expected executable entries. It writes temporary destination files and replaces each one, then records checksums. It attempts restoration on an exception. This is not a fully atomic multi-file filesystem transaction: a crash/power loss can leave partial files before a state record is written. Compare known targets with timestamped backups if that happens.

Rollback verifies existing destination checksums before changing files. It skips that checksum check for a missing destination. Backups are read when restoring, so check that all referenced backup files are still available before manual recovery; do not assume an arbitrary edited/missing record is safe. The installed recovery helper itself is not one of the recorded launcher targets.

A missing/changed record is a reason to inspect the actual files, not to delete the guard. Repeated rollbacks may replace the previous `install-state.restored.json`; retain separate upgrade-record copies when you need long-term provenance.

## 5. First installation

Review compatibility and prerequisites in the README: Python 3, Node.js, shell/core tools, desktop-file utilities, sufficient space, and a working compositor. All scripts run as the regular user, without `python -O` or sudo. Assertions are part of the current safety checks.

From the checkout, after fully quitting the application:

```bash
python3 prepare.py
python3 check-window.py
python3 check-theme.py
python3 install.py
"$HOME/.local/bin/chatgpt-liquid-glass"
```

Quit/Exit can differ from closing a window to the tray. Do not forcibly stop a user's ongoing task without authorization and checking draft/work state. If this application hosts the current maintenance agent, do not terminate it from under the running tools: prepare/install the replacement and ask the user to reopen it afterward.

That preparation is possible only when the target runtime is not the active copy. If rebuilding the exact active runtime is required, finish source/fixture work first, keep the process guard, and hand off the quit-and-rebuild step. A separate new-version directory can be prepared while the older instance remains open; do not launch the second copy against its profile simultaneously.

The application needs a new native window; compositor reload alone cannot make an already-created opaque native window transparent. Do not run stock and patched instances against the same profile simultaneously.

## 6. Supporting an updated package

### Inventory and preparation

1. Preserve `git diff`, the old runtime, installed launchers, build metadata, installation record, and recovery backups. Do not overwrite a loaded archive or binary.
2. Record installed package version and full original archive checksum; use the inspection recipe in [ASAR-INSPECTION.md](ASAR-INSPECTION.md).
3. Find the actual main entry and bundle by semantic behavior. Hashed bundle names and minified identifiers routinely change.
4. Inspect constructor options, per-theme native background updates, surface policy, loading hooks, and security/lifetime context. Carry the behavior described in [ARCHITECTURE.md](ARCHITECTURE.md).
5. Change exact patch strings and keep their one-match assertions. Do not broaden a search until an unrelated window can match it.
6. Build into a new version/fingerprint-specific runtime directory. Keep the old copy for recovery, without using its old binaries against a new source archive.
7. Revise the extracted-window smoke test to run the new functions. Syntax alone cannot catch a stale but syntactically valid minified variable name.
8. Run applicable checks, then inspect actual views and themes. Treat new-chat and existing-chat composers as different layouts.

### Files that must remain aligned

| Change | Update these together |
| --- | --- |
| Application version/runtime directory | `prepare.py`, `launch.sh`, `install.py`, `check-window.py`, README/handoff baseline |
| Original archive fingerprint | `prepare.py`, `launch.sh`, README/handoff baseline |
| Bundle path/minified anchors | `prepare.py`, `check-window.py`, architecture map |
| CSS selector or material behavior | Stylesheet, theme fixture, actual affected views, explanation of the invariant |
| Desktop actions/identity | `install.py` guard/rewrite, installer verification, README |
| Recovery behavior | `rollback.py`, installed helper, installer fixture if present, documented manual recovery |

Do not use a global replacement to rewrite historical verification into claims about the new build. Current baseline tables and historical evidence need different wording.

### Upgrade an existing recorded installation

Finish preparation and testing before touching active launchers. Preserve an extra copy of the old state record. Then, with the application stopped:

```bash
"$HOME/.local/bin/chatgpt-liquid-glass-rollback"
python3 install.py
"$HOME/.local/bin/chatgpt-liquid-glass"
```

This restores the previous baseline before creating a fresh recorded installation. It preserves the original rollback meaning; reinstalling over the previous override would otherwise back up the patch as though it were the user's original launcher. If an installed file changed, stop and compare it rather than force-overwriting it.

## 7. CSS-only updates

1. Inspect the real element painting the wrong region, including ancestors, sibling backplates, pseudo-elements, background images, masks, and sticky surfaces.
2. Reproduce the state in the fixture, including focus/theme/scroll or old-conversation conditions. Confirm the pre-fix failure is a rendering/style assertion, not a JavaScript or environment failure.
3. Add the narrowest background override and preserve foreground/card/input fills.
4. Run theme and native-hook checks. For a prepared stopped copy, `python3 prepare.py` embeds the new CSS; reopening is required.
5. Do not rerun `install.py` for a CSS-only change. Launch arguments/desktop files need no replacement.

Changing source CSS, a Git commit, or `hyprctl reload` does not hot-update the running Electron document. Temporary live diagnostic styles are not a permanent installation.

## 8. Validation ladder

```bash
python3 check-theme.py
python3 check-window.py
bash -n launch.sh
bash -n rollback.sh
git diff --check
```

`prepare.py` separately performs JS syntax and ASAR reconstruction checks. The ChatGPT theme fixture checks body/sidebar colors and one foreground span through light → dark → light; it does not cover all controls, media, or structural wrappers. ChatGPT currently has no dedicated disposable-home installer test. Claude's separate `check-install.py` and larger renderer fixture do not establish coverage for this repository.

`check-theme.py` runs a local HTML fixture with Google Chrome at `/opt/google/chrome/chrome`, using a temporary profile, headless mode, and `--no-sandbox`. That flag is a limitation of this fixture, not a production launch recommendation. Do not make the real application unsandboxed to obtain the same test result.

`check-window.py` reads the prepared ASAR, extracts targeted functions/expressions, and invokes them under Node with stub Electron objects. It checks the code actually embedded in the runtime, but it does not boot Electron, sign in, exercise OAuth, or inspect the entire app. False confidence from a mocked check was avoided by also separating real-process and real-view evidence.

Live validation should include main window creation, actual executable path, light/dark switching, sidebar contrast, new and existing conversations, scrolling to composer, editing/focus, menus, file dialogs, code blocks, images/video, and secondary windows relevant to the user's workflow. Do not send messages or invoke model/provider actions just to test transparency.

## 9. Troubleshooting decision table

| Symptom | First check | Next action |
| --- | --- | --- |
| Stock application opens after update | Original checksum differs or target runtime missing | Inspect/adapt the new package; keep fallback |
| Correct runtime remains opaque | Native surface + native background + CSS + actual instance | Fully quit/reopen; inspect all layers, not only CSS |
| Foreground becomes transparent | Compositor whole-window opacity or broad CSS opacity | Remove the inappropriate opacity rule; keep background-only material |
| Dark stays dark in light mode | Actual app theme attributes/color-scheme and native theme setter | Fix the owning layer; do not hardcode the entire app to dark |
| Two translucent layers look dirty | Multiple base paints / shell beneath view | Keep one base; clear structural wrappers |
| Only old conversation has black composer rectangle | Sticky backdrop / approval dock / pseudo-element | Reproduce the existing-chat state and clear its outer fill |
| Preparation rejects a version/anchor | Unknown build or changed minified code | Reinspect; never silence the assertion |
| Preparation refuses active runtime | Running exact copied executable or remaining children | Quit normally and verify from correct process namespace |
| Runtime crashes or misses a library | Incomplete/stale copied resources, new package/security mechanism | Restore stock launcher, preserve logs safely, inspect the copy |
| Installation record exists | Already installed | Use the existing launcher or recorded rollback before reinstall |
| Rollback sees edited launcher | User/package changes after install | Compare with backups; preserve subsequent user work |
| Desktop menu still uses stock | Wrong override path or direct binary launch | Check Exec, desktop identity, and menu cache; do not alter account state |
| Glass absent although surfaces are transparent | Compositor/plugin state | Diagnose Hyprglass separately |

## 10. Recovery and safe cleanup

For a normal rollback, quit the app and run the installed `-rollback` command. Then reopen the normal app-menu entry or stock launcher. The application copy and backups deliberately remain for recovery.

If the state record is damaged/missing, inspect the exact expected destinations and timestamped backups. Restore only files whose baseline you can establish; move an uncertain local override into a private recovery directory rather than destroying it. Use the stock executable directly while resolving launcher state.

Do not delete account profiles, run a reset-app-data operation, remove all `.local/share/applications`, remove another version's runtime because its name is unfamiliar, or delete an archive while a process uses it. A stopped unreferenced copy may be archived/quarantined or removed after recovery is confirmed. Build/backup directories can contain proprietary application code and should remain private.

## 11. Repository delivery and next-agent report

Review ignored files and staged diff. Exclude ASARs, binaries, unpacked application resources, caches, profiles, install-state JSON, original/patched archive copies, tokens, conversation exports, and private screenshots. Follow the integration license without redistributing third-party assets.

The owner normally publishes:

```bash
git push origin main
```

A push publishes source; it does not apply the patch locally. Preserve original/local runtime references when reorganizing a checkout: installed launchers do not require the old workspace path.

Report package version/hash; inspected bundle and native semantics; files changed; tests and exact limits; backup/record location; original-package integrity; running executable (or required manual restart); whether live old/new chats were actually checked; whether diagnostics were removed; and local versus pushed commits. Never report a startup or visual check that was not performed.

### ChatGPT-specific recovery caution

The current installer does not explicitly reject an existing destination symlink. Its backup path follows the target's file contents; restoration is not guaranteed to recreate the original symlink relationship. Inspect local desktop/launcher symlinks and preserve them manually before installation. The tested desktop entry has one Exec line. A home directory requiring unusual desktop Exec escaping also needs review: this installer currently writes the launcher path without the quoting used in the Claude installer.

### Recorded 2026-11-15 boundary

The new native anchors, archive integrity, window smoke check, light/dark fixture, and installed launcher/runtime fingerprints passed. The application hosting the maintenance conversation remained the stock executable. The patched build was prepared and installed, but a full user-controlled quit/reopen and live visual validation were still pending at handoff. Do not infer later success from these notes.
