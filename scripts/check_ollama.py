#!/usr/bin/env python3
"""Verify Ollama is reachable and the requested model is available."""

import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_HOST = "http://127.0.0.1:11434"


def fetch_tags(host):
    url = f"{host.rstrip('/')}/api/tags"
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.load(resp)


def main():
    parser = argparse.ArgumentParser(description="Check Ollama availability and models.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument(
        "--model",
        action="append",
        default=[],
        help="Model name to verify (repeatable).",
    )
    args = parser.parse_args()

    try:
        data = fetch_tags(args.host)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"❌ Ollama not reachable at {args.host}: {exc}")
        print("   Start the Ollama app or run: ollama serve")
        sys.exit(1)

    names = {m.get("name") for m in data.get("models", [])}
    print(f"✅ Ollama reachable — {len(names)} model(s) installed")
    for name in sorted(names):
        print(f"   - {name}")

    missing = [m for m in args.model if m not in names]
    if args.model and missing:
        print(f"❌ Missing model(s): {', '.join(missing)}")
        print("   Pull with: ollama pull <model>")
        sys.exit(2)

    if args.model:
        print(f"✅ All requested models present: {', '.join(args.model)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
