"""SkellLang CLI: plaintext v0.1 and explicitly unlocked SkellCipher."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from . import SkellLangError, compile_file, export_json, export_from_studio

def _prompt_recovery(confirm: bool) -> str:
    """Read recovery secret only from a real terminal, never args or stdin pipes."""
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        raise ValueError("Recovery requires a private interactive terminal")
    from getpass import getpass
    value = getpass("Offline recovery passphrase: ")
    if confirm and value != getpass("Confirm recovery passphrase: "):
        raise ValueError("Recovery confirmation does not match")
    return value


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
    create.add_argument("--i-understand-no-recovery", "--i-understand-recovery-required",
                        dest="i_understand_no_recovery", action="store_true")
    encrypt = subs.add_parser("cipher-encrypt", help="Encrypt validated source")
    encrypt.add_argument("source", type=Path)
    encrypt.add_argument("destination", type=Path)
    encrypt.add_argument("--key-id", required=True)
    verify = subs.add_parser("cipher-check", help="Authorized in-memory compile")
    verify.add_argument("source", type=Path)
    verify.add_argument("--native", action="store_true", help="Check authenticated native control source")
    rotate = subs.add_parser("cipher-rotate", help="Rotate encrypted source")
    rotate.add_argument("source", type=Path)
    rotate.add_argument("destination", type=Path)
    rotate.add_argument("--new-key-id", required=True)
    backup = subs.add_parser("cipher-backup", help="Export authenticated offline recovery backup")
    backup.add_argument("key_id")
    backup.add_argument("destination", type=Path)
    restore = subs.add_parser("cipher-restore", help="Import an offline recovery backup")
    restore.add_argument("source", type=Path)
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
                    "create and verify offline backup before using irreplaceable sources")
            vault = WindowsCredentialVault()
            if args.action == "cipher-key-create":
                vault.create(args.key_id)
                print("SkellCipher: experimental Windows vault key created")
            elif args.action == "cipher-encrypt":
                encrypt_file(args.source, args.destination, args.key_id,
                             vault.resolve(args.key_id))
                print("SkellCipher: encrypted file created; source plaintext remains on disk")
            elif args.action == "cipher-check":
                if args.native:
                    from .cipher import compile_encrypted_native_file
                    compile_encrypted_native_file(args.source, vault.resolve)
                else:
                    compile_encrypted_file(args.source, vault.resolve)
                print("SkellCipher: authorized in-memory compilation passed")
            elif args.action == "cipher-backup":
                from .recovery import backup_to_file
                backup_to_file(args.destination, args.key_id, vault.resolve(args.key_id),
                               _prompt_recovery(confirm=True))
                print("SkellCipher: offline encrypted recovery backup created and verified")
            elif args.action == "cipher-restore":
                from .recovery import restore_from_file
                recovered_id, recovered_key = restore_from_file(
                    args.source, _prompt_recovery(confirm=False))
                vault.import_key(recovered_id, recovered_key)
                print("SkellCipher: authenticated key restored into Windows vault")
            elif args.action == "cipher-rotate":
                rotate_file(args.source, args.destination, vault.resolve,
                            args.new_key_id, vault.resolve(args.new_key_id))
                print("SkellCipher: ciphertext rotated; original file preserved")
        return 0
    except ImportError:
        print("SkellLang error: install the optional Windows crypto dependencies with pip install skelllang[windows]", file=sys.stderr)
        return 1
    except (SkellLangError, OSError, ValueError) as exc:
        print("SkellLang error:", str(exc), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
