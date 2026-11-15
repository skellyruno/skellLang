"""Filename-based defense against accidentally committed source/key artifacts."""
from pathlib import PurePosixPath
import subprocess
import sys

def main() -> int:
    tracked = subprocess.run(["git", "ls-files", "-z"],
                             capture_output=True, check=True).stdout
    for item in tracked.split(b"\x00"):
        if not item:
            continue
        path = item.decode("utf-8", "surrogateescape").replace("\\", "/")
        parts = [x.lower() for x in PurePosixPath(path).parts]
        name = parts[-1]
        if (name.startswith(".env")
                or name.endswith((".pem", ".p12", ".skellkey",
                                  ".plaintext.tmp", ".key", ".skellbackup"))
                or (name.endswith(".skell") and
                    any(p in ("private", "secrets", "protected") for p in parts))):
            print("ERROR: tracked private source/key path forbidden", file=sys.stderr)
            return 1
    print("Tracked private artifact filename scan: clear")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
