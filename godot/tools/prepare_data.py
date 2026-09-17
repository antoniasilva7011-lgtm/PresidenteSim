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

GEOJSON_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
RASTER_URL = "https://www.naturalearthdata.com/download/50m/raster/NE2_50M_SR.zip"
GEOJSON_OUT = DATA / "world.geojson"
TEXTURE_OUT = DATA / "world_texture.jpg"

print(f"Downloading Natural Earth world countries -> {GEOJSON_OUT}")
with urllib.request.urlopen(GEOJSON_URL, timeout=60) as response:
    payload = response.read()

parsed = json.loads(payload.decode("utf-8"))
if parsed.get("type") != "FeatureCollection" or not parsed.get("features"):
    raise SystemExit("Invalid GeoJSON downloaded")

for feature in parsed["features"]:
    props = feature.get("properties", {})
    feature["properties"] = {
        "ADMIN": props.get("ADMIN") or props.get("NAME") or "Unknown",
        "ADM0_A3": props.get("ADM0_A3") or props.get("ISO_A3") or "",
        "ISO_A2": props.get("ISO_A2") or "",
        "CONTINENT": props.get("CONTINENT") or "",
        "REGION_UN": props.get("REGION_UN") or "",
    }

GEOJSON_OUT.write_text(
    json.dumps(parsed, ensure_ascii=False, separators=(",", ":")),
    encoding="utf-8",
)
print(f"Prepared {len(parsed['features'])} map features ({GEOJSON_OUT.stat().st_size / 1024:.1f} KiB)")

print(f"Downloading Natural Earth II shaded relief -> {TEXTURE_OUT}")
with urllib.request.urlopen(RASTER_URL, timeout=180) as response:
    raster_zip = response.read()

with zipfile.ZipFile(io.BytesIO(raster_zip)) as archive:
    tif_names = [name for name in archive.namelist() if name.lower().endswith((".tif", ".tiff"))]
    if not tif_names:
        raise SystemExit("Natural Earth raster ZIP did not contain a TIFF image")
    with archive.open(tif_names[0]) as tif_file:
        with Image.open(tif_file) as image:
            image = image.convert("RGB")
            image = image.resize((2048, 1024), Image.Resampling.LANCZOS)
            image.save(TEXTURE_OUT, "JPEG", quality=84, optimize=True, progressive=True)

print(f"Prepared physical texture ({TEXTURE_OUT.stat().st_size / 1024 / 1024:.2f} MiB)")
