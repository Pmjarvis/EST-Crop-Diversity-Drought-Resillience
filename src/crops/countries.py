
import geopandas as gpd
import pandas as pd

from ..common import paths
from ..common.contract import YEAR_MAX, YEAR_MIN, validate
from . import faostat

NE_ZIP = paths.RAW / "naturalearth" / "ne_10m_admin_0_countries.zip"
AREA_HARVESTED = 5312


MERGED = {
    15: "BLX", 255: "BLX", 256: "BLX",     
    186: "SCG", 272: "SCG", 273: "SCG",    
    206: "SDX", 276: "SDX", 277: "SDX",    
}
MERGED_INFO = {
    "BLX": ("Belgium-Luxembourg", "Europe & Central Asia", "BEL;LUX"),
    "SCG": ("Serbia and Montenegro", "Europe & Central Asia", "SRB;MNE"),
    "SDX": ("Sudan (former)", "Sub-Saharan Africa", "SDN;SSD"),
}
CHINA_AGGREGATE = 351  


def ne_table():
    
    ne = gpd.read_file(f"zip://{NE_ZIP}", ignore_geometry=True)
    ne = ne[(ne["ISO_N3_EH"] != "-99") & (ne["ISO_A3_EH"] != "-99")].copy()
    
    ne["main"] = ne["ADM0_A3"] == ne["ISO_A3_EH"]
    ne = ne.sort_values("main", ascending=False).drop_duplicates("ISO_N3_EH")
    return ne.rename(columns={"ISO_N3_EH": "m49", "ISO_A3_EH": "iso3", "REGION_WB": "region"})[["m49", "iso3", "region"]]


def area_map():
    
    qcl = faostat.read(faostat.QCL, [AREA_HARVESTED, 5510])
    areas = qcl[qcl["Element Code"] == AREA_HARVESTED].groupby(["Area Code", "Area Code (M49)", "Area"])["Year"] \
        .agg(first_year="min", last_year="max").reset_index()
    areas.columns = ["area_code", "m49", "area", "first_year", "last_year"]
    areas["m49"] = areas["m49"].str.strip("'")
    areas = areas[areas["area_code"] != CHINA_AGGREGATE].merge(ne_table(), on="m49", how="left")
    merged = areas["area_code"].map(MERGED)
    areas["iso3"] = merged.fillna(areas["iso3"])
    areas.loc[merged.notna(), "region"] = areas.loc[merged.notna(), "iso3"].map(lambda k: MERGED_INFO[k][1])
    return areas


def main():
    areas = area_map()
    unmapped = areas[areas["iso3"].isna()]
    print(f"FAOSTAT areas with no iso3 in Natural Earth (dropped): {unmapped['area'].tolist()}")
    areas = areas.dropna(subset=["iso3"])

    rows = []
    for iso3, g in areas.groupby("iso3", sort=True):
        if iso3 in MERGED_INFO:
            name, region, members = MERGED_INFO[iso3]
        else:
            assert len(g) == 1, f"{iso3}: several FAOSTAT areas map to it: {g['area'].tolist()}"
            name, region, members = g["area"].iloc[0], g["region"].iloc[0], ""
        rows.append((iso3, name, region, members))
    countries = pd.DataFrame(rows, columns=["iso3", "name", "region", "member_iso3"])

    span = areas.groupby("iso3").agg(first_year=("first_year", "min"), last_year=("last_year", "max"))
    partial = span[(span["first_year"] > YEAR_MIN) | (span["last_year"] < YEAR_MAX)]
    print(f"entities whose crop series starts or stops inside {YEAR_MIN}-{YEAR_MAX} (kept; quality.py decides):")
    print(partial.to_string() if len(partial) else "  none")

    validate(countries, "countries")
    assert countries["region"].notna().all() and countries["name"].notna().all()
    assert {"BLX", "SCG", "SDX", "CHN", "TWN"} <= set(countries["iso3"])
    assert not {"BEL", "LUX", "SRB", "MNE", "SDN", "SSD"} & set(countries["iso3"])
    paths.CLEAN.mkdir(parents=True, exist_ok=True)
    countries.to_csv(paths.COUNTRIES, index=False)
    print(f"\ncountries.csv: {len(countries)} entities, {countries['region'].nunique()} regions, "
          f"{(countries['member_iso3'] != '').sum()} merged")
    print(countries["region"].value_counts().to_string())


if __name__ == "__main__":
    main()
