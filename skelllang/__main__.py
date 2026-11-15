"""SkellLang CLI: plaintext v0.1 and explicitly unlocked SkellCipher."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from . import SkellLangError, compile_file, export_json, export_from_studio

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="skelllang")
    subs = parser.add_subparsers(dest="action", required=True)
    check = subs.add_parser("check", help="Validate plaintext .skell")
    check.add_argument("source", type=Path)
    export = subs.add_parser("export", help="Create Studio JSON without overwrite")
    export.add_argument("source", type=Path)
    export.add_argument("destination", type=Path)
    reverse = subs.add_parser("from-studio", help="Convert Studio design to .skell")
    reverse.add_argument("project", type=Path)
    reverse.add_argument("destination", type=Path)
    create = subs.add_parser("cipher-key-create", help="EXPERIMENTAL Windows vault key")
    create.add_argument("key_id")
    create.add_argument("--i-understand-no-recovery", action="store_true")
    encrypt = subs.add_parser("cipher-encrypt", help="Encrypt validated source")
    encrypt.add_argument("source", type=Path)
    encrypt.add_argument("destination", type=Path)
    encrypt.add_argument("--key-id", required=True)
    verify = subs.add_parser("cipher-check", help="Authorized in-memory compile")
    verify.add_argument("source", type=Path)
    rotate = subs.add_parser("cipher-rotate", help="Rotate encrypted source")
    rotate.add_argument("source", type=Path)
    rotate.add_argument("destination", type=Path)
    rotate.add_argument("--new-key-id", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "check":
            compile_file(args.source)
            print("SkellLang 0.1: valid")
        elif args.action == "export":
            export_json(args.source, args.destination)
            print("SkellLang 0.1: exported JSON")
        elif args.action == "from-studio":
            export_from_studio(args.project, args.destination)
            print("SkellLang 0.1: exported source")
        else:
            from .cipher import (CipherError, encrypt_file, compile_encrypted_file, rotate_file)
            from .windows_keys import WindowsCredentialVault
            if args.action == "cipher-key-create" and not args.i_understand_no_recovery:
                raise CipherError(
                    "Key creation blocked without --i-understand-no-recovery; "
                    "no safe independent recovery exists")
            vault = WindowsCredentialVault()
            if args.action == "cipher-key-create":
                vault.create(args.key_id)
                print("SkellCipher: experimental Windows vault key created")
            elif args.action == "cipher-encrypt":
                encrypt_file(args.source, args.destination, args.key_id,
                             vault.resolve(args.key_id))
                print("SkellCipher: encrypted file created; source plaintext remains on disk")
            elif args.action == "cipher-check":
                compile_encrypted_file(args.source, vault.resolve)
                print("SkellCipher: authorized in-memory compilation passed")
            elif args.action == "cipher-rotate":
                rotate_file(args.source, args.destination, vault.resolve,
                            args.new_key_id, vault.resolve(args.new_key_id))
                print("SkellCipher: ciphertext rotated; original file preserved")
        return 0
    except (SkellLangError, OSError, ValueError) as exc:
        print("SkellLang error:", str(exc), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
