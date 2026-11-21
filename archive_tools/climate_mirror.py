"""Publish or restore the SPEIbase and NOAA gridded inputs at their original project paths."""
import argparse
import csv
import gzip
import hashlib
import json
import shutil
import tarfile
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from era5_mirror import ROOT, fetch

LEDGER = ROOT / "future_work/source_files.csv.gz"
RELEASE = "https://github.com/Pmjarvis/EST-Crop-Diversity-Drought-Resillience/releases/download/raw-climate-v1"


def inventory():
    groups = {}
    with gzip.open(LEDGER, "rt") as stream:
        for row in csv.DictReader(stream):
            path = Path(row["path"])
            if path.parent.name == "spei":
                name = path.name
            elif path.parent.name == "noaa_grid" and path.suffix == ".nc":
                year = path.name.split(".P")[1][:4]
                name = f"noaa-vegetation-{year}.tar"
            else:
                continue
            groups.setdefault(name, []).append(row)
    return groups


def check(path, row):
    if path.stat().st_size != int(row["bytes"]):
        raise ValueError(f"Size mismatch: {path}")
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != row["sha256"]:
            raise ValueError(f"Source checksum mismatch: {path}")


def pack(name, rows, out):
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        tmp = Path(tmp)
        def retrieve(row):
            path = tmp / Path(row["path"]).name
            fetch(row["source_url"], path)
            check(path, row)
            return path
        with ThreadPoolExecutor(max_workers=6) as pool:
            files = list(pool.map(retrieve, rows))
        if name.endswith(".nc"):
            files[0].replace(out / name)
            return
        with tarfile.open(tmp / name, "w", format=tarfile.USTAR_FORMAT) as archive:
            for row, file in zip(rows, files, strict=True):
                member = tarfile.TarInfo(row["path"])
                member.size = int(row["bytes"])
                with file.open("rb") as stream:
                    archive.addfile(member, stream)
        (tmp / name).replace(out / name)


def restore(name, rows, out):
    paths = [out / row["path"] for row in rows]
    if all(path.is_file() for path in paths):
        for path, row in zip(paths, rows, strict=True):
            check(path, row)
        return
    with tempfile.TemporaryDirectory(dir=out) as directory:
        tmp = Path(directory)
        download = tmp / name
        fetch(f"{RELEASE}/{name}", download)
        if name.endswith(".nc"):
            check(download, rows[0])
            paths[0].parent.mkdir(parents=True, exist_ok=True)
            download.replace(paths[0])
            return
        with tarfile.open(download, "r:") as archive:
            for member, row, dest in zip(archive, rows, paths, strict=True):
                if not member.isfile() or member.name != row["path"] or member.size != int(row["bytes"]):
                    raise ValueError(f"Unexpected member in {name}")
                partial = tmp / "checked"
                with archive.extractfile(member) as stream, partial.open("wb") as output:
                    shutil.copyfileobj(stream, output)
                check(partial, row)
                dest.parent.mkdir(parents=True, exist_ok=True)
                partial.replace(dest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["list", "pack", "restore"])
    parser.add_argument("--asset")
    parser.add_argument("--out", type=Path, default=ROOT)
    args = parser.parse_args()
    sets = inventory()
    if args.action == "list":
        print(json.dumps(sorted(sets)))
    else:
        args.out.mkdir(parents=True, exist_ok=True)
        for name in ([args.asset] if args.asset else sorted(sets)):
            (pack if args.action == "pack" else restore)(name, sets[name], args.out)
