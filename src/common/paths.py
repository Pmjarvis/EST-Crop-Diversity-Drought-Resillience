import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
USE_DUMMY = os.environ.get("USE_DUMMY") == "1"

RAW = ROOT / "data" / "raw"
CLEAN_REAL = ROOT / "data" / "clean"
OUT_REAL = ROOT / "outputs"
CLEAN_DUMMY = ROOT / "data" / "dummy"
OUT_DUMMY = ROOT / "outputs" / "dummy"

CLEAN = CLEAN_DUMMY if USE_DUMMY else CLEAN_REAL
OUT = OUT_DUMMY if USE_DUMMY else OUT_REAL

COUNTRIES = CLEAN / "countries.csv"
CROPS = CLEAN / "crops.parquet"
CONTROLS = CLEAN / "controls.parquet"
QUALITY = CLEAN / "quality.csv"
CLIMATE = CLEAN / "climate.parquet"
EVENTS = CLEAN / "events.csv"
COUNTRIES_GEOJSON = CLEAN / "countries.geojson"

METRICS = OUT / "metrics.parquet"
CROP_ANOMALIES = OUT / "crop_anomalies.parquet"
STATS_DIR = OUT / "stats"
VALIDATION_DIR = OUT / "validation"


FIGURES = ROOT / "figures"
EXPLORER = ROOT / "explorer"

NATIONAL = OUT / "metrics_national.parquet"


def fig_dir(owner):
    d = FIGURES / owner / "dummy" if USE_DUMMY else FIGURES / owner
    d.mkdir(parents=True, exist_ok=True)
    return d
