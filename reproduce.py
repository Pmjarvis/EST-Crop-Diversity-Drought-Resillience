"""Rebuild the published analyses. Install requirements.txt and restore source data before raw or all."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
STAGES = {
    "raw": """
        src.crops.countries src.crops.crops src.crops.controls src.crops.quality
        src.climate.geometry src.climate.cropland src.climate.aggregate:--per-crop src.climate.events
        src.climate.mapspam_area src.crops.trade src.crops.prices src.crops.calories
        src.climate.wet_events src.climate.heat src.climate.exposure_pre src.climate.exposure_season
        src.crops.trade_matrix src.india.clean src.india.geo src.india.climate src.india.extended
    """,
    "national": """
        src.metrics.all src.validation.hit_rate src.validation.case_studies src.metrics.wet
        src.metrics.heat src.metrics.panel src.metrics.oos src.metrics.portfolio src.metrics.calorie_faces
        src.crops.buffers src.climate.analysis.response_paradox src.climate.analysis.spatial_and_flash
        src.metrics.exposure_diversity src.metrics.severity src.crops.supply_diversity
    """,
    "district": "src.india.panel src.india.conley src.india.kharif src.india.kharif_crops",
    "figures": "src.climate.figures src.crops.figures src.explorer",
    "extensions": "future_work:all",
    "verify": "future_work:verify",
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=["all", *STAGES])
    args = p.parse_args()
    stages = ["raw", "national", "district", "figures"] if args.stage == "all" else [args.stage]
    env = dict(os.environ, USE_DUMMY="0", OPENBLAS_NUM_THREADS="1")
    # Extensions compare against the byte-frozen originals. Rebuild those studies first when running all.
    if args.stage == "all":
        stages.insert(0, "extensions")
    for stage in stages:
        for module in STAGES[stage].split():
            print(f"Running {module}", flush=True)
            subprocess.run([sys.executable, "-m", *module.split(":")], cwd=ROOT, env=env, check=True)


if __name__ == "__main__":
    main()
