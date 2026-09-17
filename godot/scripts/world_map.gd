extends Control

signal country_clicked(country_id: String)

const GEOJSON_PATH := "res://data/world.geojson"
var features: Array = []
var labels: Array = []
var zoom := 1.0
var pan := Vector2.ZERO
var _touches: Dictionary = {}
var _touch_start: Dictionary = {}
var _moved: Dictionary = {}
var _last_mouse := Vector2.ZERO
var _mouse_dragging := false
var _pinch_start_distance := 0.0
var _pinch_start_zoom := 1.0
var selected_id := "BRA"

func _ready() -> void:
    mouse_filter = Control.MOUSE_FILTER_STOP
    _load_geojson()
    WorldState.country_selected.connect(_on_country_selected)
    resized.connect(queue_redraw)
    queue_redraw()

func _load_geojson() -> void:
    if not FileAccess.file_exists(GEOJSON_PATH):
        push_warning("world.geojson ausente. Execute godot/tools/prepare_data.py antes de exportar.")
        return
    var raw := FileAccess.get_file_as_string(GEOJSON_PATH)
    var parsed = JSON.parse_string(raw)
    if typeof(parsed) != TYPE_DICTIONARY:
        push_error("GeoJSON inválido")
        return
    features = parsed.get("features", [])
    labels.clear()
    for f in features:
        var props: Dictionary = f.get("properties", {})
        var name := str(props.get("ADMIN", props.get("name", "País")))
        var iso := str(props.get("ADM0_A3", props.get("ISO_A3", "")))
        if iso == "-99" or iso.is_empty():
            iso = name.to_upper().replace(" ", "_")
        f["_presim_id"] = iso
        WorldState.merge_geo_country(iso, name)
        var geom: Dictionary = f.get("geometry", {})
        var center_geo := _feature_geo_center(geom.get("coordinates", []), str(geom.get("type", "")))
        labels.append({"id": iso, "name": name, "geo": center_geo, "area_hint": _feature_area_hint(geom.get("coordinates", []), str(geom.get("type", "")))})

func reset_view() -> void:
    zoom = 1.0
    pan = Vector2.ZERO
    queue_redraw()

func zoom_by(factor: float, focus := Vector2.ZERO) -> void:
    var old := zoom
    zoom = clamp(zoom * factor, 1.0, 8.0)
    if focus != Vector2.ZERO:
        pan = focus - (focus - pan) * (zoom / max(old, 0.001))
    queue_redraw()

func _gui_input(event: InputEvent) -> void:
    if event is InputEventScreenTouch:
        _handle_touch(event)
        accept_event()
    elif event is InputEventScreenDrag:
        _handle_drag(event)
        accept_event()
    elif event is InputEventMouseButton:
        if event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
            zoom_by(1.18, event.position)
        elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
            zoom_by(1.0 / 1.18, event.position)
        elif event.button_index == MOUSE_BUTTON_LEFT:
            _mouse_dragging = event.pressed
            _last_mouse = event.position
            if not event.pressed:
                _select_at(event.position)
        accept_event()
    elif event is InputEventMouseMotion and _mouse_dragging:
        pan += event.position - _last_mouse
        _last_mouse = event.position
        queue_redraw()
        accept_event()

func _handle_touch(event: InputEventScreenTouch) -> void:
    if event.pressed:
        _touches[event.index] = event.position
        _touch_start[event.index] = event.position
        _moved[event.index] = false
        if _touches.size() == 2:
            var pts := _touches.values()
            _pinch_start_distance = pts[0].distance_to(pts[1])
            _pinch_start_zoom = zoom
            for key in _moved.keys():
                _moved[key] = true
    else:
        var should_select := not bool(_moved.get(event.index, false)) and _touches.size() == 1
        _touches.erase(event.index)
        _touch_start.erase(event.index)
        _moved.erase(event.index)
        if should_select:
            _select_at(event.position)
        if _touches.size() < 2:
            _pinch_start_distance = 0.0

func _handle_drag(event: InputEventScreenDrag) -> void:
    _touches[event.index] = event.position
    var start: Vector2 = _touch_start.get(event.index, event.position)
    if event.position.distance_to(start) > 8.0:
        _moved[event.index] = true
    if _touches.size() == 1:
        pan += event.relative
        queue_redraw()
    elif _touches.size() >= 2:
        var pts := _touches.values()
        var distance := pts[0].distance_to(pts[1])
        if _pinch_start_distance <= 0.0:
            _pinch_start_distance = distance
            _pinch_start_zoom = zoom
        var center: Vector2 = (pts[0] + pts[1]) * 0.5
        var old := zoom
        zoom = clamp(_pinch_start_zoom * distance / max(1.0, _pinch_start_distance), 1.0, 8.0)
        pan = center - (center - pan) * (zoom / max(0.001, old))
        queue_redraw()

func _project(coord: Array) -> Vector2:
    var lon := float(coord[0])
    var lat := float(coord[1])
    var base := Vector2((lon + 180.0) / 360.0 * size.x, (90.0 - lat) / 180.0 * size.y)
    return base * zoom + pan

func _draw() -> void:
    draw_rect(Rect2(Vector2.ZERO, size), Color("07131d"))
    if features.is_empty():
        _draw_missing_data()
        return
    for f in features:
        var id := str(f.get("_presim_id", ""))
        var geom: Dictionary = f.get("geometry", {})
        var gtype := str(geom.get("type", ""))
        var coords = geom.get("coordinates", [])
        var fill := _country_color(id)
        if gtype == "Polygon":
            _draw_polygon_group(coords, fill)
        elif gtype == "MultiPolygon":
            for poly in coords:
                _draw_polygon_group(poly, fill)
    _draw_labels()

func _draw_polygon_group(rings: Array, fill: Color) -> void:
    if rings.is_empty():
        return
    var outer: PackedVector2Array = []
    for c in rings[0]:
        outer.append(_project(c))
    if outer.size() >= 3:
        draw_colored_polygon(outer, fill)
        draw_polyline(outer, Color(0.15, 0.72, 0.95, 0.34), 1.0, true)

func _draw_labels() -> void:
    var font := get_theme_default_font()
    for item in labels:
        var geo: Vector2 = item["geo"]
        if geo == Vector2.INF:
            continue
        var area_hint := float(item["area_hint"])
        var min_zoom := 1.0
        if area_hint < 4.0:
            min_zoom = 4.0
        elif area_hint < 12.0:
            min_zoom = 2.5
        elif area_hint < 30.0:
            min_zoom = 1.7
        if zoom < min_zoom:
            continue
        var p := _project([geo.x, geo.y])
        if p.x < -80 or p.y < -30 or p.x > size.x + 80 or p.y > size.y + 30:
            continue
        var id := str(item["id"])
        var name := str(item["name"]).to_upper()
        var font_size := int(clamp(12.0 + zoom * 1.8, 12.0, 22.0))
        var color := Color(0.95, 0.98, 1.0, 0.88)
        if id == selected_id:
            color = Color(0.30, 0.90, 1.0, 1.0)
            font_size += 2
        var width := font.get_string_size(name, HORIZONTAL_ALIGNMENT_CENTER, -1, font_size).x
        draw_string(font, p - Vector2(width * 0.5, -font_size * 0.35), name, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)

func _country_color(id: String) -> Color:
    if id == selected_id:
        return Color(0.08, 0.58, 0.78, 0.95)
    var c: Dictionary = WorldState.countries.get(id, {})
    if bool(c.get("war", false)):
        return Color(0.55, 0.10, 0.12, 0.96)
    if bool(c.get("sanctioned", false)):
        return Color(0.45, 0.25, 0.08, 0.96)
    var stability := float(c.get("stability", 55.0))
    var t := clamp(stability / 100.0, 0.0, 1.0)
    return Color(0.05 + 0.08 * t, 0.16 + 0.22 * t, 0.20 + 0.16 * t, 0.96)

func _select_at(pos: Vector2) -> void:
    var best_id := ""
    var best_distance := 99999.0
    for item in labels:
        var geo: Vector2 = item["geo"]
        if geo == Vector2.INF:
            continue
        var center := _project([geo.x, geo.y])
        var d := center.distance_to(pos)
        if d < best_distance:
            best_distance = d
            best_id = str(item["id"])
    var threshold := 95.0 + 30.0 * min(zoom, 3.0)
    if not best_id.is_empty() and best_distance < threshold:
        WorldState.select_country(best_id)
        country_clicked.emit(best_id)

func _feature_geo_center(coords, gtype: String) -> Vector2:
    var points: Array = []
    if gtype == "Polygon" and coords.size() > 0:
        points = coords[0]
    elif gtype == "MultiPolygon" and coords.size() > 0:
        var largest: Array = []
        for poly in coords:
            if poly.size() > 0 and poly[0].size() > largest.size():
                largest = poly[0]
        points = largest
    if points.is_empty():
        return Vector2.INF
    var sum_lon := 0.0
    var sum_lat := 0.0
    for c in points:
        sum_lon += float(c[0])
        sum_lat += float(c[1])
    return Vector2(sum_lon / points.size(), sum_lat / points.size())

func _feature_area_hint(coords, gtype: String) -> float:
    var points: Array = []
    if gtype == "Polygon" and coords.size() > 0:
        points = coords[0]
    elif gtype == "MultiPolygon" and coords.size() > 0 and coords[0].size() > 0:
        points = coords[0][0]
    if points.is_empty():
        return 0.0
    var min_lon := 999.0
    var max_lon := -999.0
    var min_lat := 999.0
    var max_lat := -999.0
    for c in points:
        min_lon = min(min_lon, float(c[0]))
        max_lon = max(max_lon, float(c[0]))
        min_lat = min(min_lat, float(c[1]))
        max_lat = max(max_lat, float(c[1]))
    return abs(max_lon - min_lon) * abs(max_lat - min_lat)

func _on_country_selected(id: String) -> void:
    selected_id = id
    queue_redraw()

func _draw_missing_data() -> void:
    draw_string(get_theme_default_font(), Vector2(50, 90), "MAPA GEOJSON NÃO PREPARADO", HORIZONTAL_ALIGNMENT_LEFT, -1, 28, Color.WHITE)
    draw_string(get_theme_default_font(), Vector2(50, 130), "Execute: python godot/tools/prepare_data.py", HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color(0.6,0.75,0.85))
