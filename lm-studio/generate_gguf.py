#!/usr/bin/env python3
"""generate_gguf.py - Generate mcptool.gguf from metadata and source code."""

import json
import struct
from pathlib import Path

GGUF_MAGIC = b"GGUF"
GGUF_VERSION = 3


def generate_gguf(metadata_path: str, output_path: str):
    """Generate a GGUF file with metadata embedded."""
    
    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    with open(output_path, "wb") as f:
        # Write magic number
        f.write(GGUF_MAGIC)
        
        # Write version (little-endian uint32)
        struct.pack_into("<I", f.write(0), 4, GGUF_VERSION)
        
        # Encode metadata to JSON bytes
        metadata_bytes = json.dumps(metadata).encode("utf-8")
        
        # Write KV pair count and length
        kv_count = len(metadata_bytes)
        f.write(kv_count.to_bytes(4, 'little'))
        
        # Write metadata bytes
        f.write(metadata_bytes)

    print(f"✅ Generated {output_path} ({kv_count:,} bytes of metadata)")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate mcptool GGUF file")
    parser.add_argument(
        "--metadata", 
        default=None,
        help="Path to gguf.json (defaults to same directory as script)"
    )
    parser.add_argument(
        "--output", 
        default=None,
        help="Output path for GGUF file"
    )
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    if args.metadata:
        metadata_path = args.metadata
    else:
        metadata_path = script_dir / "mcptool.gguf.json"
    
    if not args.output:
        output_path = script_dir / "mcptool.gguf"
    else:
        output_path = Path(args.output)
    
    generate_gguf(str(metadata_path), str(output_path))
