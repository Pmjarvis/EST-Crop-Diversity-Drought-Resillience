"""Package or restore the publisher-verified compressed ERA5 objects used in the analysis."""
import argparse
import base64
import csv
import gzip
import hashlib
import json
import os
import shutil
import tarfile
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "future_work/era5_source_objects.csv.gz"
BASES = {
    "arco": "https://storage.googleapis.com/gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3",
    "weatherbench": "https://storage.googleapis.com/weatherbench2/datasets/era5/1959-2023_01_10-1h-240x121_equiangular_with_poles_conservative.zarr",
}
RELEASE = "https://github.com/Pmjarvis/EST-Crop-Diversity-Drought-Resillience/releases/download/raw-era5-v1"
PART_BYTES = 768 * 1024**2


def groups():
    with gzip.open(LEDGER, "rt") as f:
        rows = list(csv.DictReader(f))
    if len({(r["archive"], r["key"]) for r in rows}) != len(rows):
        raise ValueError("Duplicate hourly object in ledger")
    parts, part, size = [], [], 0
    for row in rows:
        n = int(row["bytes"])
        if part and size + n > PART_BYTES:
            parts.append(part)
            part, size = [], 0
        part.append(row)
        size += n
    return parts + [part]


def key(row):
    return f"{row['archive']}/2m_temperature/{row['key']}"


def asset(index):
    return f"era5-{index:03d}.tar"


def verify(data, row):
    if len(data) != int(row["bytes"]) or hashlib.md5(data).digest() != base64.b64decode(row["md5_base64"]):
        raise ValueError(f"Publisher checksum mismatch for {key(row)}")


def fetch(url, file):
    for attempt in range(6):
        try:
            with urlopen(Request(url, headers={"User-Agent": "crop-diversity-data-archive"}), timeout=120) as source, file.open("wb") as out:
                shutil.copyfileobj(source, out, 1024 * 1024)
            return
        except OSError:
            if attempt == 5:
                raise
            time.sleep(2**attempt)


def materialize(row, temp):
    path = temp / key(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    fetch(f"{BASES[row['archive']]}/2m_temperature/{row['key']}?generation={row['generation']}", path)
    verify(path.read_bytes(), row)
    return path


def pack(index, rows, out):
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        temp = Path(tmp)
        with ThreadPoolExecutor(max_workers=12) as pool:
            files = list(pool.map(lambda row: materialize(row, temp), rows))
        partial = temp / asset(index)
        with tarfile.open(partial, "w", format=tarfile.USTAR_FORMAT) as archive:
            for row, file in zip(rows, files, strict=True):
                member = tarfile.TarInfo(key(row))
                member.size = int(row["bytes"])
                with file.open("rb") as src:
                    archive.addfile(member, src)
        partial.replace(out / asset(index))


def restore(index, rows, out):
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        tmp = Path(tmp)
        archive_path = tmp / asset(index)
        fetch(f"{RELEASE}/{asset(index)}", archive_path)
        with tarfile.open(archive_path, "r:") as archive:
            for member, row in zip(archive, rows, strict=True):
                if not member.isfile() or member.name != key(row) or member.size != int(row["bytes"]):
                    raise ValueError("Unexpected archive member")
                data = archive.extractfile(member).read()
                verify(data, row)
                target = out / key(row)
                target.parent.mkdir(parents=True, exist_ok=True)
                partial = tmp / "verified-object"
                partial.write_bytes(data)
                os.replace(partial, target)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("list", "pack", "restore"))
    parser.add_argument("--part", type=int)
    parser.add_argument("--out", type=Path, default=ROOT / "future_work/local/raw/era5_objects")
    args = parser.parse_args()
    parts = groups()
    if args.mode == "list":
        print(json.dumps([{"asset": asset(i), "objects": len(p), "bytes": sum(int(r["bytes"]) for r in p)} for i, p in enumerate(parts)]))
    else:
        if args.part is not None and not 0 <= args.part < len(parts):
            parser.error("Part index outside the source inventory")
        for i in range(len(parts)) if args.part is None else (args.part,):
            (pack if args.mode == "pack" else restore)(i, parts[i], args.out)
