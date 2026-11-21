"""Restore packaged original data. Use git lfs pull first. Add --hourly to restore hourly ERA5."""
import argparse
import csv
import gzip
import hashlib
import os
import shutil
import tarfile
import tempfile
from pathlib import Path

from climate_mirror import ROOT, inventory, restore
from era5_mirror import groups, restore as restore_hourly


def unpack(ledger, root):
    archive = ledger.with_suffix(".tar.gz")
    with ledger.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if len({r["path"] for r in rows}) != len(rows):
        raise ValueError(f"Repeated path in {ledger.name}")
    with tarfile.open(archive, "r|gz") as source:
        for member, row in zip(source, rows, strict=True):
            rel = Path(row["path"])
            dest = root / rel
            if (row["archive"] != archive.name or not member.isfile() or member.name != rel.as_posix()
                or member.size != int(row["bytes"]) or rel.is_absolute() or ".." in rel.parts
                or not dest.resolve().is_relative_to(root.resolve())):
                raise ValueError(f"Unexpected member in {archive.name}: {member.name}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            with source.extractfile(member) as stream, tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as output:
                temp = Path(output.name)
                try:
                    digest = hashlib.sha256()
                    while data := stream.read(1024 * 1024):
                        digest.update(data)
                        output.write(data)
                    if digest.hexdigest() != row["sha256"]:
                        raise ValueError(f"Checksum mismatch for {rel}")
                    output.close()
                    os.replace(temp, dest)
                finally:
                    temp.unlink(missing_ok=True)
    print(f"Restored {len(rows)} files from {archive.name}", flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--local-only", action="store_true", help="restore the Git LFS packages only")
    p.add_argument("--hourly", action="store_true", help="also download the 41.06 GB of hourly temperature objects")
    p.add_argument("--root", type=Path, default=ROOT)
    args = p.parse_args()
    if args.local_only and args.hourly:
        p.error("--hourly needs access to the ERA5 release")
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    for ledger in sorted((ROOT / "archive_data").glob("*.csv")):
        unpack(ledger, root)
    for original in (root / "data/raw/cru").glob("*.nc.gz"):
        dest = original.with_suffix("")
        with gzip.open(original) as src, tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as output:
            temp = Path(output.name)
            try:
                shutil.copyfileobj(src, output, length=1024 * 1024)
                output.close()
                os.replace(temp, dest)
            finally:
                temp.unlink(missing_ok=True)
    if not args.local_only:
        for name, rows in inventory().items():
            restore(name, rows, root)
    if args.hourly:
        for index, rows in enumerate(groups()):
            restore_hourly(index, rows, root / "future_work/local/raw/era5_objects")


if __name__ == "__main__":
    main()
