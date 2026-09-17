#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import pathlib
import urllib.request
import zipfile

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

GEOJSON_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_map_units.geojson"
ADMIN1_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson"
RASTER_URL = "https://naturalearth.s3.amazonaws.com/50m_raster/NE2_50M_SR.zip"
GEOJSON_OUT = DATA / "world.geojson"
BRAZIL_STATES_OUT = DATA / "brazil_states.geojson"
TEXTURE_OUT = DATA / "world_texture.jpg"


def download(url: str, timeout: int) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "PresidenteSim-GitHubActions/0.6 (+https://github.com/antoniasilva7011-lgtm/PresidenteSim)",
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


print(f"Downloading Natural Earth admin-0 map units -> {GEOJSON_OUT}")
payload = download(GEOJSON_URL, 60)
parsed = json.loads(payload.decode("utf-8"))
if parsed.get("type") != "FeatureCollection" or not parsed.get("features"):
    raise SystemExit("Invalid GeoJSON downloaded")

for feature in parsed["features"]:
    props = feature.get("properties", {})
    feature["properties"] = {
        "ADMIN": props.get("ADMIN") or props.get("NAME_LONG") or props.get("NAME") or "Unknown",
        "SOVEREIGNT": props.get("SOVEREIGNT") or props.get("ADMIN") or "Unknown",
        "SOV_A3": props.get("SOV_A3") or props.get("ADM0_A3") or props.get("ISO_A3") or "",
        "ADM0_A3": props.get("ADM0_A3") or props.get("ISO_A3") or "",
        "GEOUNIT": props.get("GEOUNIT") or props.get("NAME_LONG") or props.get("NAME") or "Unknown",
        "GU_A3": props.get("GU_A3") or props.get("ADM0_A3") or props.get("ISO_A3") or "",
        "NAME_PT": props.get("NAME_PT") or "",
        "NAME_EN": props.get("NAME_EN") or "",
        "TYPE": props.get("TYPE") or "",
        "HOMEPART": props.get("HOMEPART", 1),
        "MIN_LABEL": props.get("MIN_LABEL", 3),
        "LABEL_X": props.get("LABEL_X"),
        "LABEL_Y": props.get("LABEL_Y"),
        "ISO_A2": props.get("ISO_A2") or "",
        "CONTINENT": props.get("CONTINENT") or "",
        "REGION_UN": props.get("REGION_UN") or "",
    }

GEOJSON_OUT.write_text(json.dumps(parsed, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"Prepared {len(parsed['features'])} map units ({GEOJSON_OUT.stat().st_size / 1024:.1f} KiB)")

print(f"Downloading Natural Earth admin-1 subdivisions -> {BRAZIL_STATES_OUT}")
admin1_payload = download(ADMIN1_URL, 120)
admin1 = json.loads(admin1_payload.decode("utf-8"))
if admin1.get("type") != "FeatureCollection":
    raise SystemExit("Invalid admin-1 GeoJSON downloaded")

br_features = []
for feature in admin1.get("features", []):
    props = feature.get("properties", {})
    adm0 = str(props.get("adm0_a3") or props.get("ADM0_A3") or props.get("iso_a2") or props.get("ISO_A2") or "")
    if adm0 not in {"BRA", "BR"}:
        continue
    name = props.get("name_pt") or props.get("name") or props.get("name_en") or "Estado"
    postal = props.get("postal") or props.get("iso_3166_2") or ""
    feature["properties"] = {
        "NAME": name,
        "POSTAL": postal,
        "TYPE": props.get("type_pt") or props.get("type_en") or props.get("type") or "Estado",
        "ADM0_A3": "BRA",
    }
    br_features.append(feature)

brazil_states = {"type": "FeatureCollection", "features": br_features}
BRAZIL_STATES_OUT.write_text(json.dumps(brazil_states, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"Prepared {len(br_features)} Brazil subdivisions ({BRAZIL_STATES_OUT.stat().st_size / 1024:.1f} KiB)")

print(f"Downloading Natural Earth II shaded relief -> {TEXTURE_OUT}")
raster_zip = download(RASTER_URL, 180)
with zipfile.ZipFile(io.BytesIO(raster_zip)) as archive:
    tif_names = [name for name in archive.namelist() if name.lower().endswith((".tif", ".tiff"))]
    if not tif_names:
        raise SystemExit("Natural Earth raster ZIP did not contain a TIFF image")
    with archive.open(tif_names[0]) as tif_file:
        with Image.open(tif_file) as image:
            image = image.convert("RGB")
            image = image.resize((2048, 1024), Image.Resampling.LANCZOS)
            image.save(TEXTURE_OUT, "JPEG", quality=86, optimize=True, progressive=True)

print(f"Prepared physical texture ({TEXTURE_OUT.stat().st_size / 1024 / 1024:.2f} MiB)")
