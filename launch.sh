#!/bin/sh
set -eu
runtime="$HOME/.local/share/chatgpt-liquid-glass/26.1013.40934/app-theme-aware/ChatGPT"
stock_asar="/usr/lib/chatgpt/resources/app.asar"
expected="127889637eca45c38ab9dd0487043ad7d59c9c1c265551f1754e483ba24584a6"
if [ ! -x "$runtime" ] || [ ! -f "$stock_asar" ] || [ "$(sha256sum "$stock_asar" | cut -d ' ' -f 1)" != "$expected" ]; then
    printf '%s\n' 'ChatGPT changed since this glass patch was tested; opening the original app.' >&2
    exec /usr/bin/chatgpt "$@"
fi
exec "$runtime" "$@"
