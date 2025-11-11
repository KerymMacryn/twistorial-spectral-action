#!/usr/bin/env python3
"""
scripts/check_checksums.py

Simple SHA256 checksum verifier for the repository release artifacts.

Expected format for CHECKSUMS.txt (one entry per line, separated by whitespace):
<sha256>  relative/path/to/file.ext

Examples:
d2d2f0...  notebooks/data/table_8_1.csv
a3b34c...  figures/Fig_8_1.png

Usage:
    python scripts/check_checksums.py            # looks for CHECKSUMS.txt in repo root
    python scripts/check_checksums.py --file PATH_TO_CHECKSUMS
    python scripts/check_checksums.py --verbose

Exit code:
    0  all files present and matched
    1  any file missing or any mismatch occurred
"""

from __future__ import annotations
import argparse
import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, Tuple

DEFAULT_CHECKSUMS = "CHECKSUMS.txt"
BUFFER_SIZE = 65536  # 64 KiB

def compute_sha256(path: Path) -> str:
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            data = f.read(BUFFER_SIZE)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()

def parse_checksums(path: Path) -> Dict[Path, str]:
    """
    Parse a CHECKSUMS.txt file.
    Accepts lines with: <sha256> <whitespace> <path>
    Ignores empty lines and lines starting with #.
    Returns a mapping from file Path (relative to CHECKSUMS file parent) -> expected sha256
    """
    mapping: Dict[Path, str] = {}
    parent = path.parent
    with path.open("r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                print(f"Warning: skipping malformed line {lineno} in {path}: {raw.strip()}", file=sys.stderr)
                continue
            expected = parts[0]
            # Join remaining parts as path in case filename contains spaces (rare)
            file_rel = " ".join(parts[1:])
            file_path = (parent / file_rel).resolve()
            mapping[file_path] = expected.lower()
    return mapping

def check_all(mapping: Dict[Path, str], verbose: bool = False) -> Tuple[int, int]:
    """
    Returns (n_ok, n_total). Prints status for each file.
    """
    n_ok = 0
    n_total = 0
    for file_path, expected in sorted(mapping.items(), key=lambda x: str(x[0])):
        n_total += 1
        if not file_path.exists():
            print(f"MISSING: {file_path}", file=sys.stderr)
            continue
        try:
            found = compute_sha256(file_path)
        except Exception as e:
            print(f"ERROR reading {file_path}: {e}", file=sys.stderr)
            continue
        if found.lower() == expected.lower():
            n_ok += 1
            if verbose:
                print(f"OK     : {file_path}  {found}")
            else:
                print(f"OK     : {file_path}")
        else:
            print(f"MISMATCH: {file_path}", file=sys.stderr)
            print(f"    expected: {expected}", file=sys.stderr)
            print(f"    found   : {found}", file=sys.stderr)
    return n_ok, n_total

def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify SHA256 checksums listed in CHECKSUMS.txt")
    parser.add_argument("--file", "-f", default=DEFAULT_CHECKSUMS, help="Path to CHECKSUMS.txt (default: CHECKSUMS.txt)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print computed hashes for OK files")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only print summary and errors")
    args = parser.parse_args(argv)

    checksums_path = Path(args.file)
    if not checksums_path.exists():
        print(f"ERROR: checksum file not found: {checksums_path}", file=sys.stderr)
        sys.exit(1)

    mapping = parse_checksums(checksums_path)
    if not mapping:
        print(f"ERROR: no entries found in {checksums_path}", file=sys.stderr)
        sys.exit(1)

    if not args.quiet:
        print(f"Verifying {len(mapping)} files listed in {checksums_path}...\n")

    n_ok, n_total = check_all(mapping, verbose=args.verbose)

    if not args.quiet:
        print()
        print(f"Summary: {n_ok} / {n_total} files matched")
    if n_ok == n_total:
        print("ALL OK")
        sys.exit(0)
    else:
        print("SOME FILES FAILED (missing or checksum mismatch)", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
