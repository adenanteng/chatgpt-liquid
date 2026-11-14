#!/bin/sh
set -eu
runtime="$HOME/.local/share/chatgpt-liquid-glass/26.1111.21308/app-theme-aware/ChatGPT"
stock_asar="/usr/lib/chatgpt/resources/app.asar"
expected="904779f81a2e952cdac544375835bb730c727c5c7b4d3b71028c81855ff6088a"
if [ ! -x "$runtime" ] || [ ! -f "$stock_asar" ] || [ "$(sha256sum "$stock_asar" | cut -d ' ' -f 1)" != "$expected" ]; then
    printf '%s\n' 'ChatGPT changed since this glass patch was tested; opening the original app.' >&2
    exec /usr/bin/chatgpt "$@"
fi
exec "$runtime" "$@"
