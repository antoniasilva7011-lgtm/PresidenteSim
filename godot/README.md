# Presidente Simulator — Godot migration

This folder is the new long-term game foundation. The current Kivy APK remains untouched while Godot replaces the prototype piece by piece.

## Implemented now

- Godot 4 project configured for landscape/mobile.
- Real world map renderer from Natural Earth GeoJSON.
- One-finger pan, two-finger pinch zoom, mouse wheel zoom and country selection.
- Global `WorldState` singleton with country entities and simulation time.
- Country data is automatically created for every GeoJSON feature.
- Functional HUD/navigation for Government, Economy, Military, Diplomacy, Media, Map and Cabinet.
- First 3D Presidential Cabinet prototype with clickable crisis phone, law folders, TV and globe.
- Economy/politics/military/diplomacy actions already change the simulation state.

## Prepare the real world map

From the repository root:

```bash
python godot/tools/prepare_data.py
```

This downloads the Natural Earth Admin-0 country polygons and writes:

```text
godot/data/world.geojson
```

Natural Earth is public-domain map data. The 110m map is intentionally used first for mobile performance. Later builds can switch to 50m/10m LOD when zoomed in.

## Run

Open the `godot/` directory in Godot 4 and run `main.tscn`.

## Architecture

```text
Godot UI / 2D map / 3D cabinet
            |
        WorldState
   _________|_________
  |    |     |    |   |
Eco  Gov   Dip  Mil Media
```

The next milestones are:

1. replace placeholder country values with a complete structured dataset;
2. add map layers for relations, alliances, economy, conflict and military reach;
3. add diplomacy/trade/sanctions systems;
4. expand the cabinet into a finished interactive environment;
5. connect media/events to the same simulation state;
6. add Android export workflow and APK artifacts.

The goal is not a lightweight demo. The project is intentionally structured for a dense mobile grand-strategy game inspired by the interaction depth of geopolitical simulators, while keeping original UI/assets/code.
