#!/usr/bin/env bash
set -euo pipefail

URL="https://www.sintef.no/contentassets/1338af68996841d3922bc8e87adc430c/pdp_100.zip"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW="$ROOT/data/raw"
TMP="$ROOT/tmp/li_lim_download"

mkdir -p "$RAW"
rm -rf "$TMP"
mkdir -p "$TMP"

curl -L "$URL" -o "$TMP/pdp_100.zip"
unzip -q "$TMP/pdp_100.zip" -d "$TMP"

for f in lc101 lr101 lrc101; do
    src="$(find "$TMP" -type f -name "${f}.txt" | head -1)"
    if [[ -z "$src" ]]; then
        echo "ERROR: ${f}.txt not found" >&2
        exit 1
    fi
    cp "$src" "$RAW/${f}.txt"
done

rm -rf "$TMP"
echo "Li & Lim instances saved in data/raw/"
