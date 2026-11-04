#!/bin/sh
set -eu
runtime="$HOME/.local/share/chatgpt-liquid-glass/26.1029.61003/app-theme-aware/ChatGPT"
stock_asar="/usr/lib/chatgpt/resources/app.asar"
expected="a28793c2e1c41331903d7aa035d62e385ae81fd0719548f28dec2995d253a713"
if [ ! -x "$runtime" ] || [ ! -f "$stock_asar" ] || [ "$(sha256sum "$stock_asar" | cut -d ' ' -f 1)" != "$expected" ]; then
    printf '%s\n' 'ChatGPT changed since this glass patch was tested; opening the original app.' >&2
    exec /usr/bin/chatgpt "$@"
fi
exec "$runtime" "$@"
