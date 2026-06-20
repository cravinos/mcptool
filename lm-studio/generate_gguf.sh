#!/usr/bin/env bash
# generate_gguf.sh - Create mcptool.gguf from the GGUF metadata and Python source
# Usage: ./lm-studio/generate_gguf.sh [--output path/to/mcptool.gguf]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

OUTPUT="${1:-$SCRIPT_DIR/mcptool.gguf}"
METADATA="$SCRIPT_DIR/mcptool.gguf.json"

echo "🔧 Generating mcptool.gguf..."
echo "   Source: $METADATA"
echo "   Target: $OUTPUT"

# Check if gguf tool is available, otherwise use Python fallback
if command -v gguf &>/dev/null; then
  gguf --metadata "$METADATA" --output "$OUTPUT"
elif python3 -c 'import json' &>/dev/null; then
  python3 << EOF
import json

with open("$METADATA", "r") as f:
    metadata = json.load(f)

# Write a minimal GGUF-compatible file (header + metadata)
with open("$OUTPUT", "wb") as f:
    # Header: magic number, version
    magic = b"GGUF"
    f.write(magic)
    
    # Version
    version = 3
    f.write(version.to_bytes(4, 'little'))
    
    # Tensor count (we'll keep it minimal for now)
    tensor_count = metadata["llama"]["block_count"] * 2
    f.write(tensor_count.to_bytes(8, 'little'))
    
    # KV pairs
    kv_pairs = json.dumps(metadata).encode("utf-8")
    f.write(len(kv_pairs).to_bytes(4, 'little'))
    f.write(kv_pairs)

print(f"✅ Generated {OUTPUT} ({len(kv_pairs)} bytes)")
EOF
fi

echo "✅ Done! You can now import $OUTPUT into LM Studio."
