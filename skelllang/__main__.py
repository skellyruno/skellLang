"""SkellLang v0.1 CLI — plaintext only, no implicit decryption."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from . import SkellLangError, compile_file, export_json, export_from_studio

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="skelllang")
    subs = parser.add_subparsers(dest="action", required=True)
    check = subs.add_parser("check", help="Validate source without modifying it")
    check.add_argument("source", type=Path)
    export = subs.add_parser("export", help="Create validated JSON without overwrite")
    export.add_argument("source", type=Path)
    export.add_argument("destination", type=Path)
    reverse = subs.add_parser("from-studio", help="Convert Studio design to SkellLang")
    reverse.add_argument("project", type=Path)
    reverse.add_argument("destination", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "check":
            compile_file(args.source)
            print("SkellLang 0.1: valid")
        elif args.action == "export":
            export_json(args.source, args.destination)
            print("SkellLang 0.1: exported JSON")
        else:
            export_from_studio(args.project, args.destination)
            print("SkellLang 0.1: exported source")
        return 0
    except (SkellLangError, OSError) as exc:
        print("SkellLang error:", str(exc), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
