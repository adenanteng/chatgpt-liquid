# Agent entry point: ChatGPT Liquid

Read [README.md](README.md), [docs/MAINTAINER.md](docs/MAINTAINER.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and [docs/ASAR-INSPECTION.md](docs/ASAR-INSPECTION.md) before maintaining this integration. Read the implementation and affected tests as well; documentation versions are a baseline, not current-machine proof.

## Non-negotiable behavior

- Preserve background-only transparency: one 50% light/dark base, one additional 20% sidebar tint, and solid text/controls/media. Blur/refraction belong to Hyprglass.
- Keep the stock package untouched. Work in a user-local application copy, with original launcher fallback when the package fingerprint changes.
- Inspect every new package's constructor, backdrop/theme behavior, bundle layout, and loading hooks. Never support a new version by changing only the label/hash or disabling compatibility assertions.
- Keep native transparency, transparent native background, and scoped renderer CSS coordinated. CSS alone cannot fix an opaque native surface.
- Preserve sandboxing, context isolation, navigation/account/security checks, and all unrelated application behavior. Do not ship a debugger port or diagnostic code.
- Keep exact patch-match checks, JS syntax checks, ASAR offset/integrity rebuilding, build metadata, launcher fingerprint guard, backups, and rollback.
- Do not run preparation under `python -O`: compatibility assertions would be disabled.
- Stop the copied runtime before rebuilding it. Do not silently kill an application holding user work. If this is the app hosting the current agent/chat, prepare the replacement and let the user restart it after the handoff.
- Inspect existing installation state and user launcher changes. Restore the old recorded launchers before reinstalling; do not delete the record merely to bypass a guard.
- Do not install/rebuild/rollback the live app just to validate a documentation change.
- Use temporary profiles/homes for fixtures. Live account probes must inspect only necessary structure/style metadata, not messages, cookies, tokens, storage, or request bodies.
- Distinguish a Node stub smoke test, browser fixture, real app launch, actual rendered view, and reboot validation. Do not claim one proves all the others.
- Preserve the owner-controlled push workflow: commit requested maintenance locally, then provide push commands unless the user explicitly authorizes publishing.
- Exclude application copies, ASAR archives, profiles, diagnostics, and unsanitized screenshots from public commits. Review staged files and ignore rules.

## First actions

Inspect Git status and current package version/fingerprint, read `prepare.py`, `launch.sh`, `install.py`, `rollback.py`, both relevant test scripts, and the CSS. Follow the update matrix in the maintainer guide. After any native/bundle update, revise `check-window.py` to execute the new extracted functions rather than preserving stale minified names.

## Completion report

State exact package/hash, native patch scope, CSS changes, tests and limits, installed runtime/launcher version, preserved rollback baseline, whether the application was actually restarted, whether diagnostics were removed, and local versus pushed commits.
