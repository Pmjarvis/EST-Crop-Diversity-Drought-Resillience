"""Verify the scientific files used in the delivered presentation."""
import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "future_work/baseline.csv"


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify():
    with MANIFEST.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        path = ROOT / row["path"]
        if not path.is_file() or path.stat().st_size != int(row["bytes"]) or digest(path) != row["sha256"]:
            raise ValueError(f"Presentation file missing or changed: {row['path']}")
    print(f"Verified {len(rows)} presentation files.")
    return len(rows)


if __name__ == "__main__":
    verify()
