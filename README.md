<div align="center">

# ChatGPT Liquid

**A lighter window. The same sharp text.**

Theme-aware transparency for ChatGPT Desktop on Linux, made to complement HyprGlass.

[![License: MIT](https://img.shields.io/badge/License-MIT-a6e3a1?style=flat-square)](LICENSE)
![Platform: Linux](https://img.shields.io/badge/Platform-Linux-89b4fa?style=flat-square)
![Status: Experimental](https://img.shields.io/badge/Status-Experimental-f9e2af?style=flat-square)

[Installation](#installation) · [How it works](#how-it-works) · [Customization](#customization) · [Rollback](#rollback) · [Contributing](#contributing)

</div>

---

ChatGPT Liquid opens the application's background to your desktop while keeping text, icons, and controls at their original opacity. A subtle sidebar tint preserves the distinction between navigation and conversation, and both surfaces follow the app's light and dark themes.

This is an **unofficial, version-specific local patch**, not a ChatGPT client or an application distribution. Bring your own compatible installation. OpenAI does not maintain or endorse this project.

## Features

- **Selective transparency.** The base background is 50% opaque; foreground opacity stays unchanged.
- **A distinct sidebar.** A 20% tint over the base produces approximately 60% combined opacity.
- **Theme-aware surfaces.** Light and dark tints follow the application's CSS color scheme, including system theme selection.
- **Original package preserved.** The patch operates on a separate, user-local copy.
- **Update fallback.** If the package archive changes, the launcher opens the original application.
- **Reversible launcher installation.** Previous launchers are backed up, and rollback checks for subsequent manual edits.

Blur, refraction, and glass-edge rendering come from your compositor and HyprGlass configuration. This project supplies the transparent application surface; it does not install or configure those effects.

## Compatibility

The patch targets a specific Electron build. It is **not a universal patch for every ChatGPT package**.

| Component | Tested configuration |
| --- | --- |
| Distribution | Manjaro Linux |
| Desktop | Hyprland 0.56.2 with HyprGlass |
| Window backend | XWayland |
| Installed package | `chatgpt-bin 26.1013.40934-1` |
| Internal Electron package | `openai-codex-electron`, version `26.1013.40934` |
| Application directory | `/usr/lib/chatgpt` |
| Original desktop entry | `/usr/share/applications/chatgpt.desktop` |

The launcher pins this original `resources/app.asar` SHA-256:

```text
127889637eca45c38ab9dd0487043ad7d59c9c1c265551f1754e483ba24584a6
```

A matching version label alone does not guarantee a matching build. Native Wayland, other package layouts, and newer versions have not been validated.

### Requirements

- The compatible application installed at the paths above.
- Python 3 and Node.js (`node` is used for JavaScript syntax validation).
- `sha256sum`, a POSIX shell, and `update-desktop-database` from `desktop-file-utils`.
- A compositor that supports transparent application windows; HyprGlass provides the intended glass effect.
- Enough free space for a full local application copy: approximately 1.6 GB for the tested package, plus temporary archive space while rebuilding.

No Python packages or npm dependencies are required. Run the scripts as your regular desktop user, **without `sudo` and without Python's `-O` flag**: the patcher uses assertions as compatibility guards.

## Installation

### 1. Get the patch

```bash
git clone https://github.com/adenanteng/chatgpt-liquid.git
cd chatgpt-liquid
```

### 2. Prepare a local copy

Fully quit ChatGPT first. Closing its window may leave the process running.

```bash
python3 prepare.py
```

The patcher checks the internal version and replacement locations, validates the modified JavaScript, rebuilds the ASAR archive, and verifies the resulting payload and integrity metadata. The original installation remains untouched.

### 3. Install the launcher

```bash
python3 install.py
```

The installer creates a user-local desktop entry that takes precedence over the system entry. It keeps the normal application profile; signing in again should not be necessary for an existing profile.

### 4. Open ChatGPT

Open **ChatGPT** from your application launcher, or run:

```bash
~/.local/bin/chatgpt-liquid-glass
```

An already-running instance must exit before the transparent window can take effect. Launching `/usr/bin/chatgpt` directly uses the original installation.

> Already installed? Do not run the installer again over an active installation record. For a CSS-only change, follow [Customization](#customization). To reinstall the launchers, roll back first.

## How it works

```text
Your installed ChatGPT package
              │
              ▼
       prepare.py
       ├─ checks the supported build
       ├─ copies the application locally
       ├─ enables a transparent Linux window surface
       └─ injects glass.css into the primary window
              │
              ▼
       User-local launcher
       ├─ original archive unchanged → opens patched copy
       └─ original archive changed   → opens stock application
```

The patch adjusts Linux Electron window creation, bypasses the primary window's forced opaque-surface policy, and injects CSS after its page loads. Background overrides apply to the primary window. This is not a comprehensive transparency implementation for secondary windows or embedded views.

The application still renders its own content. This project does not reduce whole-window compositor opacity, modify GTK settings, or enable a remote debugging port in the installed launcher.

### Files on disk

The GitHub project is named `chatgpt-liquid`. Runtime and command names retain `chatgpt-liquid-glass` for compatibility with the original local installation.

| Path | Purpose |
| --- | --- |
| `~/.local/share/chatgpt-liquid-glass/26.1013.40934/app-theme-aware/` | Patched application copy |
| `~/.local/share/chatgpt-liquid-glass/26.1013.40934/build-info.json` | Original and patched archive checksums |
| `~/.local/bin/chatgpt-liquid-glass` | Guarded application launcher |
| `~/.local/share/applications/chatgpt.desktop` | User-local desktop entry |
| `~/.local/bin/chatgpt-liquid-glass-rollback` | Rollback command |
| `~/.local/state/chatgpt-liquid-glass/install-state.json` | Installed launcher checksums and backup references |
| `~/.local/state/chatgpt-liquid-glass/backups/` | Previous launcher files, when present |

The repository contains only patch tooling and documentation. Application binaries, ASAR archives, profiles, credentials, and conversations are not included.

## Customization

Edit [`glass.css`](glass.css), then fully quit ChatGPT and rebuild:

```bash
python3 prepare.py
```

Reopen the application using the existing glass launcher. Reinstalling the launcher is unnecessary for a CSS-only change.

The `body` background sets the base alpha:

```css
background-color: light-dark(
  rgba(255, 255, 255, 0.50),
  rgba(36, 36, 36, 0.50)
) !important;
```

The first color is used in light mode; the second is used in dark mode. Lower alpha values reveal more of the desktop. Keep both alpha values equal for consistent transparency across themes.

The sidebar adds its own tint. With a 0.50 base and a 0.20 sidebar overlay, combined opacity is:

```text
1 − (1 − 0.50) × (1 − 0.20) = 0.60
```

Avoid applying `opacity` to the window or root container: it also fades text and other foreground content.

## Rollback

```bash
~/.local/bin/chatgpt-liquid-glass-rollback
```

Then fully quit ChatGPT and reopen it. Rollback restores the previous desktop entry and launcher, or removes them if none existed before installation. Profile data and conversations are not moved or deleted.

Rollback refuses to overwrite launcher files that have changed since installation. Inspect those changes before proceeding; do not delete the state file to bypass the check.

The copied application and backup files remain on disk for recovery. They can be removed manually after rollback once no process is running from the copied application directory.

## Application updates

The original package remains managed by your package manager. When its ASAR checksum changes, the glass launcher falls back to the original application. Transparency will therefore stop applying until the new build has been inspected and supported.

To support another build, a maintainer must inspect its window creation and surface policy, update the exact patch locations and launcher fingerprint, then test the resulting application. **Changing only the version string or checksum is not a compatibility fix.**

## Validation

| Check | Coverage |
| --- | --- |
| Patched JavaScript syntax | Checked by `prepare.py` with Node.js |
| Modified ASAR payload, size, and SHA-256 metadata | Checked after preparation |
| Light → dark → light CSS switching | Browser self-check |
| Background alpha and unchanged foreground opacity | Browser self-check |
| Sign-in and primary shell/sidebar | Previously inspected in an isolated application profile |
| Launcher fallback and rollback | Exercised locally on the tested installation |

Run the theme self-check with Google Chrome installed at `/opt/google/chrome/chrome`:

```bash
python3 check-theme.py
```

It uses a temporary browser profile and a local test page. It does not open your ChatGPT profile. The test currently launches headless Chrome with `--no-sandbox`; it is intended only for this local fixture.

Individual conversation surfaces, embedded tools, media playback, secondary windows, native Wayland, and future application versions are not comprehensively tested. The CSS self-check does not replace an end-to-end visual check of the application.

## Troubleshooting

**The background is still opaque.** Fully quit every ChatGPT instance, then use the glass launcher. Check whether the installed package fingerprint changed; the launcher prints a fallback message to the terminal when it opens the original app.

**Transparency works, but there is no blur or refraction.** Check your compositor and HyprGlass configuration. Transparent pixels alone do not produce a glass effect.

**Light mode still has a dark background.** Confirm that you rebuilt after updating `glass.css` and restarted the application. CSS is embedded into the copied archive during preparation; editing the source file alone does not update a running window.

**Preparation refuses to continue.** Read the failed compatibility guard or running-process warning. Quit the copied application if it is still running. Do not bypass version or patch-location checks for an unknown build.

**Installation reports an existing record.** Use the current launcher, or roll back before reinstalling. The installer intentionally avoids overwriting a recorded installation.

## Project layout

```text
chatgpt-liquid/
├── glass.css          # Theme-aware background overrides
├── prepare.py         # Version-guarded application copy and ASAR patcher
├── install.py         # User-local desktop launcher installation
├── launch.sh          # Original-package fingerprint check and fallback
├── rollback.py        # Restore launcher files using recorded backups
├── rollback.sh        # Installed rollback entry point
├── check-theme.py     # Isolated browser check for theme switching
├── LICENSE
└── README.md
```

## Contributing

Focused fixes and reproducible compatibility reports are welcome. Include the distribution, window backend, application package/version, and the exact failing check. Redact personal information from screenshots and logs.

Never submit application binaries, full ASAR archives, user profiles, tokens, or conversation exports. For a new supported build, include evidence that the original installation remains intact, the patch applies to the expected locations, both themes behave correctly, and rollback still works.

## License and acknowledgments

The original scripts, stylesheet, and documentation in this repository are available under the [MIT License](LICENSE). That license does not apply to ChatGPT, Electron distributions, or any other third-party software copied locally by the scripts.

ChatGPT is an OpenAI product. HyprGlass is a separate project that supplies compositor-side glass effects. This repository is independent of both.
