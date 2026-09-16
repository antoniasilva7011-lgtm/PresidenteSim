#!/usr/bin/env python3
from __future__ import annotations
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
OUT = DATA / "world.geojson"

print(f"Downloading Natural Earth world countries -> {OUT}")
with urllib.request.urlopen(URL, timeout=60) as response:
    payload = response.read()

parsed = json.loads(payload.decode("utf-8"))
if parsed.get("type") != "FeatureCollection" or not parsed.get("features"):
    raise SystemExit("Invalid GeoJSON downloaded")

# Keep only fields PresidenteSim uses at runtime to reduce APK size.
for feature in parsed["features"]:
    props = feature.get("properties", {})
    feature["properties"] = {
        "ADMIN": props.get("ADMIN") or props.get("NAME") or "Unknown",
        "ADM0_A3": props.get("ADM0_A3") or props.get("ISO_A3") or "",
        "ISO_A2": props.get("ISO_A2") or "",
        "CONTINENT": props.get("CONTINENT") or "",
        "REGION_UN": props.get("REGION_UN") or "",
    }

OUT.write_text(json.dumps(parsed, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"Prepared {len(parsed['features'])} map features ({OUT.stat().st_size / 1024:.1f} KiB)")
